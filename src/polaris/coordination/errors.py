"""Focused exceptions for deterministic multi-agent coordination."""


class CoordinationError(Exception):
    """Base exception for Phase 7 coordination failures."""


class CoordinationCompatibilityError(CoordinationError):
    """Raised when assessments cannot be coordinated together."""


class DuplicateAgentDomainError(CoordinationCompatibilityError):
    """Raised when more than one assessment is supplied for a domain."""


class AssessmentSourceMismatchError(CoordinationCompatibilityError):
    """Raised when assessments originate from different evidence or analysis sources."""


class CoordinationValidationError(CoordinationError):
    """Raised when a coordination request is structurally invalid."""
