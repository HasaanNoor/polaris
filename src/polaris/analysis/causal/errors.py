"""Focused errors for explicit causal research designs."""

from polaris.analysis.errors import AnalysisCompatibilityError


class CausalSpecificationError(AnalysisCompatibilityError):
    """Raised when an explicit causal specification is malformed."""


class CausalDesignValidationError(CausalSpecificationError):
    """Raised when a causal design fails structural validation."""


class InvalidTreatmentAssignmentError(CausalDesignValidationError):
    """Raised when treated or control assignment is invalid."""


class InvalidTreatmentTimingError(CausalDesignValidationError):
    """Raised when treatment timing is missing, ambiguous, or inconsistent."""


class MissingControlGroupError(CausalDesignValidationError):
    """Raised when a design has no valid comparison group."""


class InsufficientPreTreatmentDataError(CausalDesignValidationError):
    """Raised when required pre-treatment observations are unavailable."""


class InsufficientPostTreatmentDataError(CausalDesignValidationError):
    """Raised when required post-treatment observations are unavailable."""


class UnsupportedStaggeredTreatmentError(CausalDesignValidationError):
    """Raised when unsupported staggered adoption is detected."""


class InvalidEventWindowError(CausalDesignValidationError):
    """Raised when event-study windows are invalid."""


class InvalidReferencePeriodError(CausalDesignValidationError):
    """Raised when an event-study reference period is invalid."""
