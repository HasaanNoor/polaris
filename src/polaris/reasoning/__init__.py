"""Phase 18 evidence-grounded reasoning public API."""

from polaris.reasoning.models import (
    CandidateConfounder,
    ContradictionRecord,
    GroundingSummary,
    ReasoningArtifact,
    ReasoningProviderConfig,
    ReasoningRequest,
    ReasoningStatement,
    ReasoningStrictness,
)
from polaris.reasoning.service import build_reasoning_artifact, run_evidence_grounded_reasoning
from polaris.reasoning.taxonomy import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    SupportLevel,
)

__all__ = [
    "CandidateConfounder",
    "CausalStatus",
    "ContradictionRecord",
    "EpistemicStatus",
    "GroundingSummary",
    "ReasoningArtifact",
    "ReasoningCategory",
    "ReasoningMode",
    "ReasoningProviderConfig",
    "ReasoningRequest",
    "ReasoningStatement",
    "ReasoningStrictness",
    "SupportLevel",
    "build_reasoning_artifact",
    "run_evidence_grounded_reasoning",
]
