from collections.abc import Sequence

from app.documents.models import DocumentExtractionRecord
from app.documents.parsers.page_inspection import PENDING_STATUSES, UNREAD_STATUSES
from app.property.normalization.dpe import SourceReference
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity


def unread_page_findings(extractions: Sequence[DocumentExtractionRecord]) -> list[RiskFinding]:
    """Required facts: page read status. Severity: medium, missing information."""
    findings: list[RiskFinding] = []
    for extraction in extractions:
        pages = [
            page.page_number
            for page in extraction.pages
            if page.read_status in UNREAD_STATUSES | PENDING_STATUSES
        ]
        if not pages:
            continue
        numbers = ", ".join(map(str, pages[:30])) + ("…" if len(pages) > 30 else "")
        findings.append(
            RiskFinding(
                code="UNREAD_DOCUMENT_PAGES",
                finding_key=f"UNREAD_DOCUMENT_PAGES:{extraction.document_id}",
                category=RiskCategory.MISSING_INFORMATION,
                severity=RiskSeverity.MEDIUM,
                title="Certaines pages n’ont pas pu être lues intégralement",
                description=(
                    f"Pages concernées : {numbers}. Leur contenu reste inconnu ou partiel. "
                    "L’analyse utilise uniquement les passages lisibles. Fournissez une copie "
                    "plus lisible pour compléter la vérification de ce document."
                ),
                status=FindingStatus.MISSING_INFORMATION,
                sources=[
                    SourceReference(document_id=extraction.document_id, page_number=number)
                    for number in pages
                ],
            )
        )
    return findings
