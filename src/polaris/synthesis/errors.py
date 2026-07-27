"""Focused errors for Phase 8 synthesis."""


class SynthesisError(Exception):
    """Base exception for Phase 8 synthesis failures."""


class SynthesisProviderError(SynthesisError):
    """Raised when an LLM synthesis provider cannot produce a response."""


class SynthesisValidationError(SynthesisError):
    """Raised when a synthesis artifact or provider response is invalid."""


class GroundingValidationError(SynthesisValidationError):
    """Raised when generated synthesis violates grounding rules."""


class UnsupportedSynthesisModeError(SynthesisError):
    """Raised when an unsupported synthesis mode is requested."""
