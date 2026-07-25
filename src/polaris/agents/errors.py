"""Focused exceptions for deterministic domain agents."""


class DomainAgentError(Exception):
    """Base exception for Phase 6 domain-agent failures."""


class UnsupportedAgentDomainError(DomainAgentError):
    """Raised when a caller requests a domain outside the core taxonomy."""


class InvalidEvidenceArtifactError(DomainAgentError):
    """Raised when an evidence artifact cannot be assessed."""


class DomainMappingError(DomainAgentError):
    """Raised when deterministic domain mapping rules are invalid."""


class AgentAssessmentError(DomainAgentError):
    """Raised when an agent assessment cannot be constructed."""
