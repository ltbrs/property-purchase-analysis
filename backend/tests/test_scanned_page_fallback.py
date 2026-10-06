import asyncio
import zlib
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError
from PIL import Image, ImageDraw
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base, get_db_session
from app.documents.classification.models import DocumentClassificationCandidate
from app.documents.llm_content import extraction_as_numbered_text, page_source_text
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRead,
    DocumentRecord,
)
from app.documents.parsers import get_pdf_parser
from app.documents.parsers.base import ParsedPage, ParsedPdf, ParsedTable, PdfParserError
from app.documents.parsers.page_inspection import inspect_pages, render_page_image
from app.documents.parsers.vision import PageTranscription
from app.documents.repository import DocumentRepository
from app.jobs.persistent_processing import (
    PersistentDocumentWorker,
    claim_document,
    enqueue_document,
    enqueue_page_retry,
)
from app.llm import get_structured_output_client
from app.llm.rate_budget import DeferredLLMCall, LLMRateBudget, retry_at_for
from app.llm.structured_output import StructuredOutputResult
from app.main import create_app
from app.reports.models import ReportRecord
from app.risks.models.findings import RiskFindingRecord
from app.risks.rules.unread_pages import unread_page_findings
from app.storage.object_storage import get_object_storage
from tests.billing_fixtures import grant_analysis_access
from tests.pdf_fixtures import make_text_pdf


def image_pdf(images: list[Image.Image]) -> bytes:
    """Real raster-only PDF pages, including blank, illustrated and scanned fixtures."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    page_ids = []
    for image in images:
        image = image.convert("RGB")
        compressed = zlib.compress(image.tobytes())
        image_id = len(objects) + 1
        objects.append(
            (
                f"<< /Type /XObject /Subtype /Image /Width {image.width} /Height {image.height} "
                "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode "
                f"/Length {len(compressed)} >>\nstream\n"
            ).encode()
            + compressed
            + b"\nendstream"
        )
        content = b"q 595 0 0 842 0 0 cm /Scan Do Q"
        content_id = len(objects) + 1
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream"
        )
        page_ids.append(len(objects) + 1)
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /XObject << /Scan {image_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
        )
    objects[1] = (
        f"<< /Type /Pages /Count {len(images)} /Kids ["
        + " ".join(f"{n} 0 R" for n in page_ids)
        + "] >>"
    ).encode()
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(output)


def scanned_image() -> Image.Image:
    image = Image.new("RGB", (595, 842), "white")
    draw = ImageDraw.Draw(image)
    for index, text in enumerate(
        [
            "PROCES VERBAL ASSEMBLEE GENERALE",
            "Travaux toiture 48000 EUR",
            "Resolution votee le 12/06/2025",
        ]
    ):
        draw.text((45, 60 + index * 30), text, fill="black")
    return image


def test_reconciles_omitted_pages_and_detects_scans_blanks_and_illustrations() -> None:
    blank = Image.new("RGB", (595, 842), "white")
    illustration = blank.copy()
    ImageDraw.Draw(illustration).rectangle((70, 120, 400, 500), fill="blue")
    pdf = image_pdf([scanned_image(), blank, illustration])
    parsed = inspect_pages(pdf, ParsedPdf(pages=[ParsedPage(page_number=1, text="1")]), 100)
    assert [page.page_number for page in parsed.pages] == [1, 2, 3]
    assert [page.read_status for page in parsed.pages] == ["pending", "blank", "pending"]
    with Image.open(BytesIO(render_page_image(pdf, 1))) as image:
        assert max(image.size) <= 2049


def test_textual_pdf_and_tables_do_not_need_vision() -> None:
    pdf = make_text_pdf(
        [["Un texte lisible et assez long pour identifier les informations du logement."]]
    )
    page = ParsedPage(
        page_number=1,
        text="",
        tables=[ParsedTable(cells=[["Le budget annuel de la copropriete est fixe a 12500 EUR"]])],
    )
    assert inspect_pages(pdf, ParsedPdf(pages=[page]), 100).pages[0].read_status == "read"


def test_candidates_above_limit_remain_explicitly_unread() -> None:
    pdf = image_pdf([scanned_image()] * 3)
    result = inspect_pages(pdf, ParsedPdf(pages=[ParsedPage(page_number=1)]), 1)
    assert [page.read_status for page in result.pages] == [
        "pending",
        "limit_exceeded",
        "limit_exceeded",
    ]
    with pytest.raises(PdfParserError):
        inspect_pages(pdf, ParsedPdf(pages=[ParsedPage(page_number=4)]), 100)


def test_scan_with_digital_footer_is_still_a_candidate() -> None:
    pdf = image_pdf([scanned_image()])
    parsed = ParsedPdf(
        pages=[
            ParsedPage(
                page_number=1,
                text=(
                    "Document fourni par le syndic Cabinet Exemple, "
                    "reproduction du proces verbal 2025"
                ),
            )
        ]
    )
    assert inspect_pages(pdf, parsed, 100).pages[0].read_status == "pending"


def test_real_xberg_output_on_raster_pdf_reaches_fallback() -> None:
    from app.documents.parsers.xberg_parser import XbergPdfParser

    pdf = image_pdf([scanned_image(), Image.new("RGB", (595, 842), "white")])
    parsed = asyncio.run(XbergPdfParser().parse(pdf, filename="scan.pdf"))
    inspected = inspect_pages(pdf, parsed, 100)
    assert [page.page_number for page in inspected.pages] == [1, 2]
    assert [page.read_status for page in inspected.pages] == ["pending", "blank"]


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class FakeParser:
    name = "xberg"
    version = "test"
    calls = 0

    async def parse(self, pdf_bytes: bytes, filename: str | None = None) -> ParsedPdf:
        self.calls += 1
        return ParsedPdf(pages=[ParsedPage(page_number=1)])


class Storage:
    def __init__(self, pdf: bytes) -> None:
        self.pdf = pdf
        self.calls = 0

    def download_pdf(self, bucket: str, key: str) -> bytes:
        self.calls += 1
        return self.pdf


class VisionClient:
    def __init__(self, outputs: list[PageTranscription | Exception], pages: int = 1) -> None:
        self.outputs = outputs
        self.calls = 0
        self.pages = pages
        self.active = 0
        self.max_active = 0

    async def parse_image(self, **kwargs: Any) -> Any:
        assert kwargs["image_url"].startswith("data:image/png;base64,")
        assert kwargs["response_model"] is PageTranscription
        self.calls += 1
        call_number = self.calls
        output = self.outputs.pop(0)
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.5)
        self.active -= 1
        if isinstance(output, Exception):
            raise output
        return StructuredOutputResult(
            output=output,
            response_id=f"resp_{call_number}",
            requested_model="gpt-6-luna",
            resolved_model="gpt-6-luna",
            input_tokens=100,
            output_tokens=20,
        )

    async def parse(self, **kwargs: Any) -> Any:
        assert f'<page number="{self.pages}">' in kwargs["user_content"]
        return StructuredOutputResult(
            output=DocumentClassificationCandidate.model_validate(
                {
                    "segments": [
                        {
                            "start_page": 1,
                            "end_page": self.pages,
                            "document_type": "unknown",
                            "confidence": 0.95,
                            "document_date": None,
                            "covered_period_start": None,
                            "covered_period_end": None,
                            "issuer": None,
                            "extraction_strategy": "none",
                        }
                    ]
                }
            ),
            response_id="classification",
            requested_model="gpt-6-luna",
            resolved_model="gpt-6-luna",
        )


def document_for(session: Session) -> DocumentRecord:
    repository = DocumentRepository(session)
    case = repository.create_analysis_case(uuid4(), "Test scanned PDF")
    return repository.create_document(
        DocumentRecord(
            analysis_case_id=case.id,
            original_filename="scan.pdf",
            content_type="application/pdf",
            size_bytes=100,
            sha256=uuid4().hex * 2,
            storage_bucket="private",
            storage_key=uuid4().hex,
            status="uploaded",
        ),
        case.user_id,
    )


def transcription(text: str = "Travaux de toiture 48000 EUR") -> PageTranscription:
    return PageTranscription(content_kind="text", text=text, has_unreadable_regions=False)


def test_illisible_marker_is_always_treated_as_partial() -> None:
    assert transcription("Montant [illisible]").has_unreadable_regions is True


def test_readable_scan_is_not_marked_partial() -> None:
    assert not transcription().has_unreadable_regions


@pytest.mark.parametrize("status", ["partial", "failed", "unreadable", "limit_exceeded"])
def test_page_retry_preserves_other_pages_and_refreshes_analysis(
    session: Session, status: str
) -> None:
    document = document_for(session)
    runner = worker(
        session,
        image_pdf([scanned_image()] * 2),
        VisionClient(
            [transcription("Budget [illisible]"), transcription("Texte confirmé")], pages=2
        ),
    )
    enqueue_document(session, document)
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    extraction = runner.repository.get_extraction(document.id)
    assert extraction is not None
    page, healthy_page = extraction.pages
    page.text = "Budget [illisible]"
    page.read_status = status
    page.attempts = runner.settings.vision_max_attempts
    page.vision_metadata = {**page.vision_metadata, "error_code": "temporary_error"}
    old_classification_id = runner.repository.list_document_classifications(document.id)[0].id
    report = ReportRecord(analysis_case_id=document.analysis_case_id, content={})
    finding = unread_page_findings([extraction])[0]
    session.add(report)
    session.add(
        RiskFindingRecord.from_finding(analysis_case_id=document.analysis_case_id, finding=finding)
    )
    session.commit()
    healthy_text = healthy_page.text
    healthy_metadata = healthy_page.vision_metadata.copy()

    enqueue_page_retry(session, document, 1)
    assert document.processing_stage == "vision"
    assert page.read_status == "pending" and page.attempts == 0
    assert page.text == "Budget [illisible]"
    assert runner.repository.list_document_classifications(document.id) == []
    assert session.scalar(select(ReportRecord)) is None
    assert session.scalar(select(RiskFindingRecord)) is None
    with pytest.raises(ValueError, match="déjà planifiées"):
        enqueue_page_retry(session, document, 1)
    session.rollback()

    resumed = worker(
        session, runner.storage.pdf, VisionClient([transcription("Budget 48000 EUR")], pages=2)
    )
    claimed = claim_document(session, resumed.settings)
    assert claimed is not None
    asyncio.run(resumed.run(claimed))
    session.refresh(healthy_page)
    assert resumed.parser.calls == 0
    assert resumed.client.calls == 1
    assert healthy_page.text == healthy_text
    assert healthy_page.vision_metadata == healthy_metadata
    assert healthy_page.attempts == 1
    session.refresh(page)
    assert page.text == "Budget 48000 EUR" and page.read_status == "read"
    assert page.failure_reason is None
    assert document.status == "completed"
    assert document.processing_progress["unread_pages"] == []
    new_classification = resumed.repository.list_document_classifications(document.id)[0]
    assert new_classification.id != old_classification_id


def test_page_retry_rejects_missing_and_successful_pages(session: Session) -> None:
    document = document_for(session)
    runner = worker(session, image_pdf([scanned_image()]), VisionClient([transcription()]))
    enqueue_document(session, document)
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    with pytest.raises(LookupError):
        enqueue_page_retry(session, document, 2)
    session.rollback()
    with pytest.raises(ValueError, match="Seules les pages"):
        enqueue_page_retry(session, document, 1)
    session.rollback()
    assert document.status == "completed"
    assert len(runner.repository.list_document_classifications(document.id)) == 1


def test_retry_without_text_does_not_confirm_a_previous_partial_transcription(
    session: Session,
) -> None:
    document = document_for(session)
    runner = worker(
        session, image_pdf([scanned_image()]), VisionClient([transcription("Budget [illisible]")])
    )
    enqueue_document(session, document)
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    enqueue_page_retry(session, document, 1)
    resumed = worker(
        session,
        runner.storage.pdf,
        VisionClient(
            [PageTranscription(content_kind="no_text", text="", has_unreadable_regions=False)]
        ),
    )
    claimed = claim_document(session, resumed.settings)
    assert claimed is not None
    asyncio.run(resumed.run(claimed))
    extraction = resumed.repository.get_extraction(document.id)
    assert extraction is not None
    assert extraction.pages[0].text == "Budget [illisible]"
    assert extraction.pages[0].read_status == "partial"
    assert document.processing_progress["unread_pages"] == [1]


def test_page_retry_api_requires_ownership_access_and_idle_document(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = document_for(session)
    repository = DocumentRepository(session)
    extraction = repository.save_extraction(
        document,
        ParsedPdf(
            pages=[ParsedPage(page_number=1, text="Montant [illisible]", read_status="partial")]
        ),
        "xberg",
        "test",
        1,
    )
    document.status = "completed"
    document.processing_stage = "completed"
    session.commit()
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: Storage(b"")
    application.dependency_overrides[get_pdf_parser] = lambda: FakeParser()
    application.dependency_overrides[get_structured_output_client] = lambda: VisionClient([])
    jobs = []

    async def capture_job(*args: Any) -> None:
        jobs.append(args[-1])

    monkeypatch.setattr("app.api.routes.documents.run_document_jobs", capture_job)
    url = (
        f"/api/v1/analysis-cases/{document.analysis_case_id}/documents/{document.id}"
        "/extraction/pages/1/retry"
    )
    owner_id = document.analysis_case.user_id
    assert owner_id is not None
    headers = {"X-User-Id": str(owner_id)}
    with TestClient(application) as client:
        assert client.post(url, headers={"X-User-Id": str(uuid4())}).status_code == 404
        assert client.post(url, headers=headers).status_code == 402
        grant_analysis_access(session, owner_id, document.analysis_case_id)
        case = document.analysis_case
        case.case_kind = "demo"
        case.user_id = None
        case.template_key = "retry-test"
        case.template_manifest_sha256 = "a" * 64
        case.access_mode = "grandfathered"
        case.published_at = datetime.now(UTC)
        session.commit()
        assert client.post(url, headers=headers).status_code == 409
        case.case_kind = "user"
        case.user_id = owner_id
        case.template_key = None
        case.template_manifest_sha256 = None
        case.access_mode = "standard"
        case.published_at = None
        document.processing_stage = "vision"
        session.commit()
        assert client.post(url, headers=headers).status_code == 409
        document.processing_stage = "completed"
        session.commit()
        response = client.post(url, headers=headers)
        assert response.status_code == 202
        assert response.json()["processing_stage"] == "vision"
        assert extraction.pages[0].read_status == "pending"
        assert client.post(url, headers=headers).status_code == 409
    assert jobs == [document.id]


def rate_limit(headers: dict[str, str] | None = None) -> RateLimitError:
    return RateLimitError(
        "rate limit",
        response=httpx.Response(
            429,
            headers=headers or {},
            request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
        ),
        body={"code": "rate_limit_exceeded"},
    )


def worker(
    session: Session, pdf: bytes, client: VisionClient, **settings: Any
) -> PersistentDocumentWorker:
    return PersistentDocumentWorker(
        session, Storage(pdf), FakeParser(), client, Settings(_env_file=None, **settings)
    )


def test_transcribes_one_page_and_keeps_page_number_sources_and_usage(session: Session) -> None:
    document = document_for(session)
    assert enqueue_document(session, document)
    assert not enqueue_document(session, document)
    runner = worker(session, image_pdf([scanned_image()]), VisionClient([transcription()]))
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    assert claim_document(session, runner.settings) is None
    asyncio.run(runner.run(claimed))
    extraction = runner.repository.get_extraction(document.id)
    assert extraction is not None
    assert extraction.pages[0].text == "Travaux de toiture 48000 EUR"
    assert extraction.pages[0].extraction_method == "vision"
    assert extraction.pages[0].attempts == 1
    assert extraction.pages[0].vision_metadata["input_tokens"] == 100
    assert '<page number="1">' in extraction_as_numbered_text(extraction)
    assert page_source_text(extraction)[1].startswith("Travaux de toiture")
    assert document.status == "completed"
    assert document.processing_progress["fallback_completed"] == 1
    assert document.lease_token is None


def test_429_checkpoints_retry_without_sleep_and_resume_does_not_reparse(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    runner = worker(
        session,
        image_pdf([scanned_image()]),
        VisionClient([rate_limit({"Retry-After": "120"}), transcription()]),
    )
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    started = datetime.now(UTC)
    asyncio.run(runner.run(claimed))
    page = session.scalar(select(DocumentExtractionPageRecord))
    assert page is not None
    assert page.read_status == "retry" and page.attempts == 1
    assert document.status == "extracting" and document.processing_stage == "vision"
    assert document.next_attempt_at is not None
    from app.llm.rate_budget import utc

    assert utc(document.next_attempt_at) >= started + timedelta(seconds=120)
    assert claim_document(session, runner.settings) is None
    document.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    page.next_attempt_at = document.next_attempt_at
    budget = runner.budget._locked_record()
    budget.state = {**budget.state, "cooldown": 0}
    session.commit()
    resumed = claim_document(session, runner.settings)
    assert resumed is not None
    asyncio.run(runner.run(resumed))
    assert runner.parser.calls == 1
    assert runner.client.calls == 2
    assert document.status == "completed"


def test_admission_wait_does_not_use_up_page_attempts(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    runner = worker(
        session,
        image_pdf([scanned_image()]),
        VisionClient([transcription()]),
        openai_requests_per_minute=1,
    )
    runner.budget.reserve(100)
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    page = session.scalar(select(DocumentExtractionPageRecord))
    assert page is not None and page.attempts == 0
    assert runner.client.calls == 0
    assert document.processing_progress["retry_reason"] == "rate_limit"


def test_exhausted_attempts_and_partial_pages_create_missing_information(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    runner = worker(
        session,
        image_pdf([scanned_image()] * 2),
        VisionClient(
            [
                rate_limit(),
                PageTranscription(
                    content_kind="text", text="Travaux [illisible]", has_unreadable_regions=True
                ),
            ],
            pages=2,
        ),
        vision_max_attempts=1,
    )
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    extraction = runner.repository.get_extraction(document.id)
    assert extraction is not None
    assert [p.read_status for p in extraction.pages] == ["failed", "partial"]
    response = DocumentExtractionRead.model_validate(extraction)
    assert response.pages[0].failure_reason is not None
    assert "erreur temporaire" in response.pages[0].failure_reason
    assert response.pages[1].failure_reason is None
    findings = unread_page_findings([extraction])
    assert findings[0].code == "UNREAD_DOCUMENT_PAGES"
    assert [source.page_number for source in findings[0].sources] == [1, 2]
    assert document.processing_progress["unread_pages"] == [1, 2]
    assert runner.client.max_active == 2


def test_expired_lease_is_reclaimed_but_live_lease_is_not(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    settings = Settings(_env_file=None)
    claimed = claim_document(session, settings)
    assert claimed is not None
    first_token = document.lease_token
    assert claim_document(session, settings) is None
    document.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()
    assert claim_document(session, settings) is not None
    assert document.lease_token != first_token


def test_resume_keeps_first_batch_and_only_transcribes_remaining_pages(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    pdf = image_pdf([scanned_image()] * 5)
    runner = worker(session, pdf, VisionClient([transcription()] * 4, pages=5))
    claimed = claim_document(session, runner.settings)
    assert claimed is not None

    async def first_batch() -> None:
        await runner.step(claimed, claimed.lease_token)
        await runner.step(claimed, claimed.lease_token)

    asyncio.run(first_batch())
    assert runner.client.calls == 4 and runner.client.max_active == 4
    assert document.processing_progress["fallback_completed"] == 4
    document.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()
    second_runner = worker(session, pdf, VisionClient([transcription()], pages=5))
    resumed = claim_document(session, second_runner.settings)
    assert resumed is not None
    asyncio.run(second_runner.run(resumed))
    assert second_runner.parser.calls == 0
    assert second_runner.client.calls == 1
    assert document.status == "completed"
    assert document.processing_progress["fallback_completed"] == 5


def test_old_empty_extraction_is_inspected_when_processing_resumes(session: Session) -> None:
    document = document_for(session)
    DocumentRepository(session).save_extraction(
        document, ParsedPdf(pages=[ParsedPage(page_number=1)]), "xberg", "old", 1
    )
    enqueue_document(session, document)
    runner = worker(session, image_pdf([scanned_image()]), VisionClient([transcription()]))
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    extraction = runner.repository.get_extraction(document.id)
    assert extraction is not None
    assert extraction.document_metadata["scan_inspection_version"] == 1
    assert extraction.pages[0].extraction_method == "vision"
    assert runner.parser.calls == 0


def test_illustration_without_text_is_not_flagged_as_unread(session: Session) -> None:
    document = document_for(session)
    enqueue_document(session, document)
    runner = worker(
        session,
        image_pdf([scanned_image()]),
        VisionClient(
            [PageTranscription(content_kind="no_text", text="", has_unreadable_regions=False)]
        ),
    )
    claimed = claim_document(session, runner.settings)
    assert claimed is not None
    asyncio.run(runner.run(claimed))
    extraction = runner.repository.get_extraction(document.id)
    assert extraction is not None
    assert extraction.pages[0].read_status == "no_text"
    assert unread_page_findings([extraction]) == []


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Retry-After": "invalid"},
        {"Retry-After": "90"},
        {"Retry-After": "Mon, 28 Sep 2026 14:02:00 GMT"},
    ],
)
def test_retry_after_and_fallback_backoff(headers: dict[str, str]) -> None:
    now = datetime(2026, 9, 28, 14, 0, tzinfo=UTC)
    scheduled = retry_at_for(rate_limit(headers), 2, now)
    minimum = (
        120
        if "GMT" in headers.get("Retry-After", "")
        else 90
        if headers.get("Retry-After") == "90"
        else 10
    )
    assert scheduled >= now + timedelta(seconds=minimum)


def test_rate_budget_is_shared_between_sessions_and_releases_concurrency(session: Session) -> None:
    settings = Settings(_env_file=None, openai_max_concurrency=1)
    first = LLMRateBudget(session, settings, "gpt-6-luna")
    reservation = first.reserve(100)
    with Session(session.get_bind()) as second_session:
        second = LLMRateBudget(second_session, settings, "gpt-6-luna")
        with pytest.raises(DeferredLLMCall):
            second.reserve(100)
        first.finish(reservation, 50)
        assert second.reserve(100)
