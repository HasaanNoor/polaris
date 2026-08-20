"""Errors for Phase 23 causal-study registry support."""

from polaris.analysis.errors import AnalysisCompatibilityError


class CausalStudyError(AnalysisCompatibilityError):
    """Base error for reviewed causal-study metadata."""


class CausalStudyNotFoundError(CausalStudyError):
    """Raised when a requested causal study is not registered."""


class InterventionValidationError(CausalStudyError):
    """Raised when intervention metadata is structurally invalid."""


class TreatmentSourceError(CausalStudyError):
    """Raised when treatment source provenance is invalid."""


class TreatmentAssignmentError(CausalStudyError):
    """Raised when treatment assignments are missing or contradictory."""


class StudyCompatibilityError(CausalStudyError):
    """Raised when study metadata is incompatible with available datasets."""


class StudyNotReadyError(CausalStudyError):
    """Raised when conversion is requested for a study that is not design-ready."""


class StudyConversionError(CausalStudyError):
    """Raised when a causal study cannot be converted to Phase 22 configuration."""
