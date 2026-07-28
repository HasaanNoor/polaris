"""Phase 9 structured report-generation public API."""

from polaris.reporting.errors import (
    ReportCompatibilityError,
    ReportGenerationError,
    ReportReferenceError,
    ReportRenderingError,
    ReportValidationError,
    UnsupportedReportFormatError,
)
from polaris.reporting.models import (
    REPORT_RULESET_VERSION,
    REPORT_SCHEMA_VERSION,
    GeneratedReport,
    ReportFormat,
    ReportMetadata,
    ReportRequest,
    ResearchReport,
)
from polaris.reporting.service import build_research_report, generate_report, report_to_json

__all__ = [
    "REPORT_RULESET_VERSION",
    "REPORT_SCHEMA_VERSION",
    "GeneratedReport",
    "ReportCompatibilityError",
    "ReportFormat",
    "ReportGenerationError",
    "ReportMetadata",
    "ReportReferenceError",
    "ReportRenderingError",
    "ReportRequest",
    "ReportValidationError",
    "ResearchReport",
    "UnsupportedReportFormatError",
    "build_research_report",
    "generate_report",
    "report_to_json",
]
