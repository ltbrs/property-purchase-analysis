import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DemoCaseManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    property_type: str
    price_eur: Decimal = Field(gt=0)
    surface_m2: Decimal = Field(gt=0)
    lot_count: int = Field(gt=0)
    address_is_fictional: bool
    read_only: bool


class DemoScenarioManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    expected_signals: list[str]
    expected_missing_document_findings: list[str]


class DemoDocumentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logical_id: str = Field(min_length=1, max_length=100)
    filename: str = Field(min_length=5, max_length=255)
    title: str
    classification_hint: str
    issuer: str
    document_date: date
    covered_period_start: date | None
    covered_period_end: date | None
    purpose: str
    page_count: int = Field(gt=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class LocalLayoutReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[str]
    use: str


class DemoGenerationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str
    notice: str
    pdf_profile: str
    dpe_template_url: str


class DemoManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    fixture_kind: str
    case: DemoCaseManifest
    scenario: DemoScenarioManifest
    documents: list[DemoDocumentManifest]
    sources_used_to_scope_the_fixture: list[str]
    local_layout_references: LocalLayoutReferences
    generation: DemoGenerationManifest

    @model_validator(mode="after")
    def validate_identity_and_fixture_guards(self) -> "DemoManifest":
        if self.schema_version != 1:
            raise ValueError("Unsupported demo manifest schema version")
        if self.fixture_kind != "synthetic_demo_dossier":
            raise ValueError("The fixture must be declared as synthetic")
        if not self.case.address_is_fictional or not self.case.read_only:
            raise ValueError("The demo case must be fictional and read-only")
        logical_ids = [document.logical_id for document in self.documents]
        filenames = [document.filename for document in self.documents]
        if len(logical_ids) != len(set(logical_ids)):
            raise ValueError("Demo logical document identifiers must be unique")
        if len(filenames) != len(set(filenames)):
            raise ValueError("Demo document filenames must be unique")
        return self

    def selected_documents(
        self, logical_ids: tuple[str, ...]
    ) -> list[DemoDocumentManifest]:
        documents_by_id = {document.logical_id: document for document in self.documents}
        missing = [logical_id for logical_id in logical_ids if logical_id not in documents_by_id]
        if missing:
            raise ValueError(f"Configured demo documents are absent: {', '.join(missing)}")
        return [documents_by_id[logical_id] for logical_id in logical_ids]

    def fingerprint(self, logical_ids: tuple[str, ...]) -> str:
        payload = {
            "manifest": self.model_dump(mode="json"),
            "selected_document_logical_ids": list(logical_ids),
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(canonical).hexdigest()


def load_demo_manifest(path: Path) -> DemoManifest:
    return DemoManifest.model_validate_json(path.read_text(encoding="utf-8"))
