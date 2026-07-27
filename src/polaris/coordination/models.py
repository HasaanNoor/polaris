"""Typed contracts for deterministic Phase 7 multi-agent coordination."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from polaris.agents.models import (
    AGENT_SCHEMA_VERSION,
    AgentAssessment,
    AgentDomain,
    DomainConcernCode,
    RelevanceReasonCode,
    RelevanceStatus,
    UnsupportedInferenceCode,
)
from polaris.evidence.models import EVIDENCE_SCHEMA_VERSION, LimitationCode
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    VariableId,
    WarningSeverity,
)

COORDINATION_SCHEMA_VERSION = "1.0.0"
COORDINATION_RULESET_VERSION = "deterministic_phase7_v1"

DOMAIN_ORDER: tuple[AgentDomain, ...] = (
    AgentDomain.GOVERNANCE,
    AgentDomain.ECONOMICS,
    AgentDomain.EDUCATION,
    AgentDomain.PUBLIC_HEALTH,
)


class CoordinationCoverageStatus(StrEnum):
    ASSESSMENT_MISSING = "assessment_missing"
    NO_RELEVANT_EVIDENCE = "no_relevant_evidence"
    RELEVANT_EVIDENCE = "relevant_evidence"


class AgreementType(StrEnum):
    SHARED_EVIDENCE = "shared_evidence"
    SHARED_CLAIM = "shared_claim"
    SHARED_LIMITATION = "shared_limitation"
    SHARED_UNSUPPORTED_INFERENCE = "shared_unsupported_inference"
    SHARED_DOMAIN_CONCERN = "shared_domain_concern"


class DivergenceType(StrEnum):
    DIFFERENT_RELEVANCE_CLASSIFICATION = "different_relevance_classification"
    DOMAIN_SPECIFIC_CONCERN = "domain_specific_concern"
    DOMAIN_SPECIFIC_UNSUPPORTED_INFERENCE = "domain_specific_unsupported_inference"
    DOMAIN_SPECIFIC_LIMITATION = "domain_specific_limitation"
    UNEVEN_EVIDENCE_COVERAGE = "uneven_evidence_coverage"


class EvidenceGapType(StrEnum):
    CROSS_DOMAIN_CLAIM_WITH_LIMITED_DOMAIN_COVERAGE = (
        "cross_domain_claim_with_limited_domain_coverage"
    )
    CLAIM_SUPPORTED_BY_SINGLE_DOMAIN_ONLY = "claim_supported_by_single_domain_only"
    EVIDENCE_REFERENCED_WITHOUT_CROSS_DOMAIN_CONTEXT = (
        "evidence_referenced_without_cross_domain_context"
    )
    LIMITED_VARIABLE_COVERAGE = "limited_variable_coverage"


class DomainGapType(StrEnum):
    DOMAIN_NOT_REPRESENTED = "domain_not_represented"
    DOMAIN_HAS_NO_RELEVANT_EVIDENCE = "domain_has_no_relevant_evidence"


class CoordinationFindingCode(StrEnum):
    INCOMPLETE_DOMAIN_SET = "incomplete_domain_set"
    NO_CROSS_DOMAIN_EVIDENCE = "no_cross_domain_evidence"
    SINGLE_DOMAIN_ONLY_EVIDENCE = "single_domain_only_evidence"
    ALL_AGENTS_EMPTY = "all_agents_empty"
    BROAD_SHARED_LIMITATION = "broad_shared_limitation"
    BROAD_UNSUPPORTED_CAUSALITY_WARNING = "broad_unsupported_causality_warning"


class CoordinationRequest(FrozenPolarisBaseModel):
    assessments: tuple[AgentAssessment, ...] = Field(min_length=1)


class DomainRelevanceReference(FrozenPolarisBaseModel):
    domain: AgentDomain
    relevance_status: RelevanceStatus
    relevance_reason_codes: tuple[RelevanceReasonCode, ...] = Field(default_factory=tuple)
    matched_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    matched_concept_categories: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("relevance_reason_codes")
    @classmethod
    def sort_reasons(
        cls, value: tuple[RelevanceReasonCode, ...]
    ) -> tuple[RelevanceReasonCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("matched_variable_ids", "matched_concept_categories")
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class DomainCoverageRecord(FrozenPolarisBaseModel):
    domain: AgentDomain
    assessment_supplied: bool
    assessment_id: NonEmptyStr | None = None
    relevant_evidence_count: int = Field(default=0, ge=0)
    relevant_claim_count: int = Field(default=0, ge=0)
    direct_domain_variable_count: int = Field(default=0, ge=0)
    cross_domain_claim_count: int = Field(default=0, ge=0)
    inherited_limitation_count: int = Field(default=0, ge=0)
    domain_concern_count: int = Field(default=0, ge=0)
    coverage_status: CoordinationCoverageStatus


class EvidenceDomainMapRecord(FrozenPolarisBaseModel):
    evidence_id: NonEmptyStr
    selecting_domains: tuple[AgentDomain, ...]
    relevance_by_domain: tuple[DomainRelevanceReference, ...] = Field(default_factory=tuple)
    selection_count: int = Field(ge=0)
    cross_domain: bool

    @field_validator("selecting_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)


class ClaimDomainMapRecord(FrozenPolarisBaseModel):
    claim_id: NonEmptyStr
    selecting_domains: tuple[AgentDomain, ...]
    relevance_by_domain: tuple[DomainRelevanceReference, ...] = Field(default_factory=tuple)
    shared_limitations: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    selection_count: int = Field(ge=0)
    cross_domain: bool

    @field_validator("selecting_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator("shared_limitations")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class CoordinationAgreement(FrozenPolarisBaseModel):
    agreement_id: NonEmptyStr
    agreement_type: AgreementType
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    unsupported_inference_codes: tuple[UnsupportedInferenceCode, ...] = Field(default_factory=tuple)
    domain_concern_codes: tuple[DomainConcernCode, ...] = Field(default_factory=tuple)
    participating_domains: tuple[AgentDomain, ...]

    @field_validator("source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("unsupported_inference_codes")
    @classmethod
    def sort_unsupported(
        cls, value: tuple[UnsupportedInferenceCode, ...]
    ) -> tuple[UnsupportedInferenceCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("domain_concern_codes")
    @classmethod
    def sort_concerns(cls, value: tuple[DomainConcernCode, ...]) -> tuple[DomainConcernCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("participating_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)


class CoordinationDivergence(FrozenPolarisBaseModel):
    divergence_id: NonEmptyStr
    divergence_type: DivergenceType
    domains_involved: tuple[AgentDomain, ...]
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    unsupported_inference_codes: tuple[UnsupportedInferenceCode, ...] = Field(default_factory=tuple)
    domain_concern_codes: tuple[DomainConcernCode, ...] = Field(default_factory=tuple)
    factual_basis: NonEmptyStr

    @field_validator("domains_involved")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator("source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("unsupported_inference_codes")
    @classmethod
    def sort_unsupported(
        cls, value: tuple[UnsupportedInferenceCode, ...]
    ) -> tuple[UnsupportedInferenceCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("domain_concern_codes")
    @classmethod
    def sort_concerns(cls, value: tuple[DomainConcernCode, ...]) -> tuple[DomainConcernCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class SharedLimitationRecord(FrozenPolarisBaseModel):
    limitation_code: LimitationCode
    domains: tuple[AgentDomain, ...]
    associated_source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    global_limitation: bool

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator("associated_source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class UnsupportedInferenceAggregation(FrozenPolarisBaseModel):
    inference_code: UnsupportedInferenceCode
    domains: tuple[AgentDomain, ...]
    all_participating_agents: bool
    relevant_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator("relevant_claim_ids")
    @classmethod
    def sort_claim_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class EvidenceGap(FrozenPolarisBaseModel):
    gap_id: NonEmptyStr
    gap_type: EvidenceGapType
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    domains: tuple[AgentDomain, ...] = Field(default_factory=tuple)

    @field_validator("source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)


class DomainGap(FrozenPolarisBaseModel):
    gap_id: NonEmptyStr
    gap_type: DomainGapType
    domain: AgentDomain
    assessment_supplied: bool
    coverage_status: CoordinationCoverageStatus


class CoordinationFinding(FrozenPolarisBaseModel):
    finding_code: CoordinationFindingCode
    severity: WarningSeverity
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    domains: tuple[AgentDomain, ...] = Field(default_factory=tuple)

    @field_validator("source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)


class CoordinationProvenance(FrozenPolarisBaseModel):
    source_evidence_artifact_id: NonEmptyStr
    source_assessment_ids: tuple[NonEmptyStr, ...]
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    participating_domains: tuple[AgentDomain, ...]
    missing_domains: tuple[AgentDomain, ...]
    coordination_ruleset_version: NonEmptyStr = COORDINATION_RULESET_VERSION
    coordination_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr
    phase5_schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    phase6_schema_version: SchemaVersion = AGENT_SCHEMA_VERSION
    phase7_schema_version: SchemaVersion = COORDINATION_SCHEMA_VERSION

    @field_validator("source_assessment_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("participating_domains", "missing_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)


class CoordinatedAssessment(FrozenPolarisBaseModel):
    coordinated_assessment_id: NonEmptyStr
    source_evidence_artifact_id: NonEmptyStr
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    participating_domains: tuple[AgentDomain, ...]
    missing_domains: tuple[AgentDomain, ...]
    source_assessment_ids: tuple[NonEmptyStr, ...]
    domain_coverage: tuple[DomainCoverageRecord, ...]
    evidence_domain_map: tuple[EvidenceDomainMapRecord, ...] = Field(default_factory=tuple)
    claim_domain_map: tuple[ClaimDomainMapRecord, ...] = Field(default_factory=tuple)
    agreements: tuple[CoordinationAgreement, ...] = Field(default_factory=tuple)
    divergences: tuple[CoordinationDivergence, ...] = Field(default_factory=tuple)
    shared_limitations: tuple[SharedLimitationRecord, ...] = Field(default_factory=tuple)
    shared_unsupported_inferences: tuple[UnsupportedInferenceAggregation, ...] = Field(
        default_factory=tuple
    )
    evidence_gaps: tuple[EvidenceGap, ...] = Field(default_factory=tuple)
    domain_gaps: tuple[DomainGap, ...] = Field(default_factory=tuple)
    coordination_findings: tuple[CoordinationFinding, ...] = Field(default_factory=tuple)
    provenance: CoordinationProvenance
    schema_version: SchemaVersion = COORDINATION_SCHEMA_VERSION

    @field_validator("participating_domains", "missing_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator("source_assessment_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def prohibit_narrative_synthesis_fields(self) -> "CoordinatedAssessment":
        if self.participating_domains != self.provenance.participating_domains:
            raise ValueError("participating domains must match provenance")
        return self


def _sort_domains(domains: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
    order = {domain: index for index, domain in enumerate(DOMAIN_ORDER)}
    return tuple(sorted(set(domains), key=lambda domain: order[domain]))
