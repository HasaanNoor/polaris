"""Domain exceptions for Phase 9 structured report generation."""


class ReportGenerationError(Exception):
    """Base error for report generation failures."""


class ReportCompatibilityError(ReportGenerationError):
    """Raised when supplied upstream artifacts do not share one lineage."""


class ReportValidationError(ReportGenerationError):
    """Raised when a generated report fails deterministic validation."""


class ReportRenderingError(ReportGenerationError):
    """Raised when a report cannot be rendered."""


class UnsupportedReportFormatError(ReportRenderingError):
    """Raised for unsupported report output formats."""


class ReportReferenceError(ReportValidationError):
    """Raised when a report references missing or fabricated source IDs."""
