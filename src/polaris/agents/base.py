"""Base deterministic behavior shared by Phase 6 domain agents."""

from datetime import UTC, datetime
from typing import Protocol

from pydantic import ValidationError

from polaris import __version__
from polaris.agents.errors import AgentAssessmentError, InvalidEvidenceArtifactError
from polaris.agents.models import (
    AGENT_RULESET_VERSION,
    AGENT_SCHEMA_VERSION,
    AgentAssessment,
    AgentAssessmentProvenance,
    AgentCoverageSummary,
    AgentDomain,
    CoverageStatus,
    DomainConcern,
    DomainConcernCode,
    DomainRelevanceRecord,
    RelevanceReasonCode,
    RelevanceStatus,
    UnsupportedInferenceCode,
)
from polaris.agents.relevance import relevance_for_claim, relevance_for_evidence
from polaris.evidence.models import ClaimType, EvidenceArtifact, LimitationCode
from polaris.evidence.provenance import deterministic_id


class DomainAgent(Protocol):
    domain: AgentDomain

    def assess(
        self,
        evidence_artifact: EvidenceArtifact,
        *,
        assessment_timestamp: datetime | None = None,
    ) -> AgentAssessment:
        """Return a deterministic assessment for one domain."""


class BaseDomainAgent:
    """Deterministic, non-generative domain agent implementation."""

    domain: AgentDomain

    def additional_unsupported_inferences(self) -> tuple[UnsupportedInferenceCode, ...]:
        return ()

    def assess(
        self,
        evidence_artifact: EvidenceArtifact,
        *,
        assessment_timestamp: datetime | None = None,
    ) -> AgentAssessment:
        artifact = _validate_artifact(evidence_artifact)
        evidence_by_id = {record.evidence_id: record for record in artifact.evidence_records}
        evidence_relevance = tuple(
            sorted(
                (
                    relevance_for_evidence(self.domain, record)
                    for record in artifact.evidence_records
                ),
                key=lambda record: record.source_id,
            )
        )
        claim_relevance = tuple(
            sorted(
                (
                    relevance_for_claim(self.domain, claim, evidence_by_id)
                    for claim in artifact.claim_candidates
                ),
                key=lambda record: record.source_id,
            )
        )
        relevance_records = tuple(sorted((*evidence_relevance, *claim_relevance), key=_sort_key))
        relevant_evidence_ids = tuple(
            record.source_id
            for record in evidence_relevance
            if record.relevance_status is not RelevanceStatus.NOT_RELEVANT
        )
        relevant_claim_ids = tuple(
            record.source_id
            for record in claim_relevance
            if record.relevance_status is not RelevanceStatus.NOT_RELEVANT
        )
        inherited_limitations = _inherited_limitations(
            artifact,
            relevant_evidence_ids=relevant_evidence_ids,
            relevant_claim_ids=relevant_claim_ids,
        )
        domain_concerns = _domain_concerns(
            artifact,
            relevance_records,
            inherited_limitations=inherited_limitations,
        )
        unsupported = tuple(
            sorted(
                set(
                    (
                        *_unsupported_inferences(artifact, inherited_limitations),
                        *self.additional_unsupported_inferences(),
                    )
                ),
                key=lambda item: item.value,
            )
        )
        coverage = _coverage_summary(
            artifact,
            relevant_evidence_ids=relevant_evidence_ids,
            relevant_claim_ids=relevant_claim_ids,
            relevance_records=relevance_records,
            inherited_limitations=inherited_limitations,
        )
        timestamp = assessment_timestamp or datetime.now(UTC)
        provenance = AgentAssessmentProvenance(
            source_evidence_artifact_id=artifact.artifact_id,
            source_analysis_result_id=artifact.source_analysis_result_id,
            dataset_id=artifact.dataset_id,
            source_checksum_sha256=artifact.source_checksum_sha256,
            agent_domain=self.domain,
            assessment_timestamp=timestamp,
            software_version=f"polaris-{__version__}",
            phase5_schema_version=artifact.schema_version,
        )
        assessment_id = _assessment_id(
            source_evidence_artifact_id=artifact.artifact_id,
            domain=self.domain,
            relevant_evidence_ids=relevant_evidence_ids,
            relevant_claim_ids=relevant_claim_ids,
            domain_concerns=domain_concerns,
        )
        try:
            return AgentAssessment(
                assessment_id=assessment_id,
                agent_domain=self.domain,
                source_evidence_artifact_id=artifact.artifact_id,
                relevant_evidence_ids=relevant_evidence_ids,
                relevant_claim_ids=relevant_claim_ids,
                domain_relevance_records=relevance_records,
                domain_concerns=domain_concerns,
                inherited_limitations=inherited_limitations,
                unsupported_inferences=unsupported,
                coverage_summary=coverage,
                provenance=provenance,
            )
        except ValidationError as exc:
            raise AgentAssessmentError("failed to construct agent assessment") from exc


def _validate_artifact(evidence_artifact: EvidenceArtifact) -> EvidenceArtifact:
    if not isinstance(evidence_artifact, EvidenceArtifact):
        raise InvalidEvidenceArtifactError("domain agents require a Phase 5 EvidenceArtifact")
    evidence_ids = {record.evidence_id for record in evidence_artifact.evidence_records}
    for claim in evidence_artifact.claim_candidates:
        missing = set(claim.supporting_evidence_ids) - evidence_ids
        if missing:
            raise InvalidEvidenceArtifactError(
                f"claim {claim.claim_id} references missing evidence IDs: {sorted(missing)}"
            )
    return evidence_artifact


def _domain_concerns(
    artifact: EvidenceArtifact,
    relevance_records: tuple[DomainRelevanceRecord, ...],
    *,
    inherited_limitations: tuple[LimitationCode, ...],
) -> tuple[DomainConcern, ...]:
    concerns: list[DomainConcern] = []
    relevant_records = [
        record
        for record in relevance_records
        if record.relevance_status is not RelevanceStatus.NOT_RELEVANT
    ]
    if any(
        RelevanceReasonCode.DIRECT_DOMAIN_VARIABLE in record.relevance_reason_codes
        for record in relevant_records
    ):
        concerns.append(_concern(DomainConcernCode.DIRECT_DOMAIN_VARIABLE, relevant_records))
    if any(
        RelevanceReasonCode.CROSS_DOMAIN_RELATIONSHIP in record.relevance_reason_codes
        for record in relevant_records
    ):
        concerns.append(_concern(DomainConcernCode.CROSS_DOMAIN_RELATIONSHIP, relevant_records))
    if any(
        RelevanceReasonCode.DOMAIN_CONTROL_PRESENT in record.relevance_reason_codes
        for record in relevant_records
    ):
        concerns.append(_concern(DomainConcernCode.DOMAIN_CONTROL_PRESENT, relevant_records))
    if _has_relationship_claim(artifact) and not relevant_records:
        concerns.append(DomainConcern(concern_code=DomainConcernCode.DOMAIN_CONTEXT_NOT_MEASURED))
    if any(
        claim.claim_id in _ids(relevant_records) and _is_association_claim(claim)
        for claim in artifact.claim_candidates
    ):
        concerns.append(_concern(DomainConcernCode.OBSERVATIONAL_ONLY, relevant_records))
        concerns.append(_concern(DomainConcernCode.UNSUPPORTED_CAUSAL_INFERENCE, relevant_records))
        concerns.append(_concern(DomainConcernCode.UNSUPPORTED_POLICY_INFERENCE, relevant_records))
    if LimitationCode.LIMITED_MODEL_SCOPE in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.LIMITED_MODEL_SCOPE,
                limitation_codes=(LimitationCode.LIMITED_MODEL_SCOPE,),
            )
        )
    if LimitationCode.MISSING_DATA_EXCLUSION in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.MISSING_DATA_RELEVANT,
                limitation_codes=(LimitationCode.MISSING_DATA_EXCLUSION,),
            )
        )
    if LimitationCode.MULTICOLLINEARITY in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.MULTICOLLINEARITY_RELEVANT,
                limitation_codes=(LimitationCode.MULTICOLLINEARITY,),
            )
        )
    if LimitationCode.HETEROSKEDASTICITY_WARNING in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.HETEROSKEDASTICITY_RELEVANT,
                limitation_codes=(LimitationCode.HETEROSKEDASTICITY_WARNING,),
            )
        )
    if LimitationCode.SMALL_SAMPLE in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.SMALL_SAMPLE_RELEVANT,
                limitation_codes=(LimitationCode.SMALL_SAMPLE,),
            )
        )
    if LimitationCode.UNSUPPORTED_GENERALIZATION in inherited_limitations:
        concerns.append(
            DomainConcern(
                concern_code=DomainConcernCode.UNSUPPORTED_GENERALIZATION,
                limitation_codes=(LimitationCode.UNSUPPORTED_GENERALIZATION,),
            )
        )
    return tuple(
        sorted(
            {concern.concern_code: concern for concern in concerns}.values(),
            key=lambda item: item.concern_code.value,
        )
    )


def _concern(
    code: DomainConcernCode,
    relevant_records: list[DomainRelevanceRecord],
) -> DomainConcern:
    return DomainConcern(
        concern_code=code,
        source_ids=tuple(record.source_id for record in relevant_records),
        variable_ids=tuple(
            variable_id
            for record in relevant_records
            for variable_id in record.matched_variable_ids
        ),
    )


def _unsupported_inferences(
    artifact: EvidenceArtifact,
    inherited_limitations: tuple[LimitationCode, ...],
) -> tuple[UnsupportedInferenceCode, ...]:
    values = {
        UnsupportedInferenceCode.CAUSALITY,
        UnsupportedInferenceCode.INTERVENTION_RECOMMENDATION,
        UnsupportedInferenceCode.POLICY_EFFECTIVENESS,
    }
    if any(
        claim.claim_type in {ClaimType.ASSOCIATION, ClaimType.CONDITIONAL_ASSOCIATION}
        for claim in artifact.claim_candidates
    ):
        values.add(UnsupportedInferenceCode.MECHANISM)
    if LimitationCode.UNSUPPORTED_GENERALIZATION in inherited_limitations:
        values.add(UnsupportedInferenceCode.POPULATION_WIDE_GENERALIZATION)
    if LimitationCode.LIMITED_MODEL_SCOPE in inherited_limitations:
        values.add(UnsupportedInferenceCode.MECHANISM)
    values.add(UnsupportedInferenceCode.TEMPORAL_PREDICTION)
    return tuple(sorted(values, key=lambda item: item.value))


def _inherited_limitations(
    artifact: EvidenceArtifact,
    *,
    relevant_evidence_ids: tuple[str, ...],
    relevant_claim_ids: tuple[str, ...],
) -> tuple[LimitationCode, ...]:
    evidence_ids = set(relevant_evidence_ids)
    claim_ids = set(relevant_claim_ids)
    values: list[LimitationCode] = []
    values.extend(
        limitation
        for record in artifact.evidence_records
        if record.evidence_id in evidence_ids
        for limitation in record.limitation_codes
    )
    values.extend(
        limitation
        for claim in artifact.claim_candidates
        if claim.claim_id in claim_ids
        for limitation in claim.limitation_codes
    )
    return tuple(sorted(set(values), key=lambda item: item.value))


def _coverage_summary(
    artifact: EvidenceArtifact,
    *,
    relevant_evidence_ids: tuple[str, ...],
    relevant_claim_ids: tuple[str, ...],
    relevance_records: tuple[DomainRelevanceRecord, ...],
    inherited_limitations: tuple[LimitationCode, ...],
) -> AgentCoverageSummary:
    direct_variables = {
        variable_id
        for record in relevance_records
        if RelevanceReasonCode.DIRECT_DOMAIN_VARIABLE in record.relevance_reason_codes
        for variable_id in record.matched_variable_ids
    }
    cross_domain_claims = {
        record.source_id
        for record in relevance_records
        if RelevanceReasonCode.CROSS_DOMAIN_RELATIONSHIP in record.relevance_reason_codes
    }
    return AgentCoverageSummary(
        coverage_status=CoverageStatus.RELEVANT_EVIDENCE
        if relevant_evidence_ids or relevant_claim_ids
        else CoverageStatus.NO_RELEVANT_EVIDENCE,
        total_evidence_records=len(artifact.evidence_records),
        relevant_evidence_count=len(relevant_evidence_ids),
        total_claims=len(artifact.claim_candidates),
        relevant_claim_count=len(relevant_claim_ids),
        direct_domain_variable_count=len(direct_variables),
        cross_domain_claim_count=len(cross_domain_claims),
        limitations_count=len(inherited_limitations),
    )


def _assessment_id(
    *,
    source_evidence_artifact_id: str,
    domain: AgentDomain,
    relevant_evidence_ids: tuple[str, ...],
    relevant_claim_ids: tuple[str, ...],
    domain_concerns: tuple[DomainConcern, ...],
) -> str:
    return deterministic_id(
        "agent_assessment_",
        {
            "source_evidence_artifact_id": source_evidence_artifact_id,
            "agent_domain": domain,
            "relevant_evidence_ids": tuple(sorted(relevant_evidence_ids)),
            "relevant_claim_ids": tuple(sorted(relevant_claim_ids)),
            "domain_concerns": tuple(concern.concern_code for concern in domain_concerns),
            "ruleset_version": AGENT_RULESET_VERSION,
            "schema_version": AGENT_SCHEMA_VERSION,
        },
    )


def _has_relationship_claim(artifact: EvidenceArtifact) -> bool:
    return any(_is_association_claim(claim) for claim in artifact.claim_candidates)


def _is_association_claim(claim) -> bool:
    return claim.claim_type in {ClaimType.ASSOCIATION, ClaimType.CONDITIONAL_ASSOCIATION}


def _ids(records: list[DomainRelevanceRecord]) -> set[str]:
    return {record.source_id for record in records}


def _sort_key(record: DomainRelevanceRecord) -> tuple[str, str]:
    return (record.source_type.value, record.source_id)
