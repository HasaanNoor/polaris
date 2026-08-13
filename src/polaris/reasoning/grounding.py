"""Grounding reference helpers for Phase 18 reasoning."""

from polaris.coordination.models import CoordinatedAssessment
from polaris.evidence.models import EvidenceArtifact
from polaris.literature.models import LiteratureContextArtifact
from polaris.reasoning.models import ReasoningStatement


class ReasoningGroundingIndex:
    def __init__(
        self,
        *,
        evidence_artifact: EvidenceArtifact,
        coordinated_assessment: CoordinatedAssessment,
        literature_context: LiteratureContextArtifact | None = None,
    ) -> None:
        self.evidence_ids = {record.evidence_id for record in evidence_artifact.evidence_records}
        self.claim_ids = {claim.claim_id for claim in evidence_artifact.claim_candidates}
        self.agent_assessment_ids = set(coordinated_assessment.source_assessment_ids)
        self.agreement_ids = {record.agreement_id for record in coordinated_assessment.agreements}
        self.divergence_ids = {
            record.divergence_id for record in coordinated_assessment.divergences
        }
        self.literature_evidence_ids = (
            {record.literature_evidence_id for record in literature_context.literature_evidence}
            if literature_context is not None
            else set()
        )

    def unsupported_ids(self, statement: ReasoningStatement) -> tuple[str, ...]:
        missing = []
        missing.extend(sorted(set(statement.evidence_ids) - self.evidence_ids))
        missing.extend(sorted(set(statement.claim_ids) - self.claim_ids))
        missing.extend(sorted(set(statement.agent_assessment_ids) - self.agent_assessment_ids))
        missing.extend(
            sorted(set(statement.literature_evidence_ids) - self.literature_evidence_ids)
        )
        return tuple(missing)


def statement_is_grounded(statement: ReasoningStatement, index: ReasoningGroundingIndex) -> bool:
    return not index.unsupported_ids(statement)
