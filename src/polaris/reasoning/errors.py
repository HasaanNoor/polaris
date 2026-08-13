"""Errors raised by Phase 18 evidence-grounded reasoning."""


class ReasoningError(Exception):
    """Base class for reasoning errors."""


class ReasoningValidationError(ReasoningError):
    """Raised when a reasoning artifact or provider response is invalid."""


class GroundingValidationError(ReasoningValidationError):
    """Raised when reasoning references unsupported grounding IDs."""


class ReasoningProviderError(ReasoningError):
    """Raised when provider-backed reasoning fails."""


class UnsupportedReasoningModeError(ReasoningError):
    """Raised when a requested reasoning mode is not implemented."""
