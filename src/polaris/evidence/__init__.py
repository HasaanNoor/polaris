"""Deterministic structured evidence extraction for Polaris Phase 5."""

from polaris.evidence.models import (
    ClaimCandidate,
    ClaimType,
    Direction,
    EvidenceArtifact,
    EvidenceRecord,
    EvidenceType,
    LimitationCode,
)
from polaris.evidence.service import extract_evidence

__all__ = [
    "ClaimCandidate",
    "ClaimType",
    "Direction",
    "EvidenceArtifact",
    "EvidenceRecord",
    "EvidenceType",
    "LimitationCode",
    "extract_evidence",
]
