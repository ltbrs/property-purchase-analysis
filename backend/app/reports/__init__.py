"""Source-backed report assembly boundary."""

from app.reports.assembly import build_buyer_report
from app.reports.models import BuyerReport, ReportRecord

__all__ = ["BuyerReport", "ReportRecord", "build_buyer_report"]
