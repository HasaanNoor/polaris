"""Domain exceptions for deterministic evidence extraction."""


class EvidenceExtractionError(Exception):
    """Base error for Phase 5 evidence extraction."""

    def __init__(
        self,
        message: str,
        *,
        analysis_result_id: str | None = None,
        evidence_id: str | None = None,
        claim_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.analysis_result_id = analysis_result_id
        self.evidence_id = evidence_id
        self.claim_id = claim_id


class UnsupportedEvidenceSourceError(EvidenceExtractionError):
    """Raised when a Phase 4 result type is not supported by Phase 5."""


class InvalidEvidenceRecordError(EvidenceExtractionError):
    """Raised when an evidence record cannot be constructed."""


class InvalidClaimCandidateError(EvidenceExtractionError):
    """Raised when a claim candidate is invalid."""


class UnsupportedClaimTypeError(InvalidClaimCandidateError):
    """Raised when a requested claim type is outside the Phase 5 taxonomy."""


class EvidenceLinkError(InvalidClaimCandidateError):
    """Raised when a claim cannot be linked to supporting evidence."""
