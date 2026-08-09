"""Typed contracts for Phase 8 guardrailed interdisciplinary synthesis."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.agents.models import AgentDomain, UnsupportedInferenceCode
from polaris.coordination.models import (
    COORDINATION_SCHEMA_VERSION,
    DOMAIN_ORDER,
    CoordinatedAssessment,
    CoordinationCoverageStatus,
)
from polaris.evidence.models import EVIDENCE_SCHEMA_VERSION, EvidenceArtifact, LimitationCode
from polaris.literature.models import LiteratureContextArtifact
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    WarningSeverity,
)

SYNTHESIS_SCHEMA_VERSION = "1.0.0"
SYNTHESIS_RULESET_VERSION = "guardrailed_phase8_v1"
SYNTHESIS_PROMPT_VERSION = "phase8_grounded_json_v1"


class SynthesisMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class SynthesisFindingCode(StrEnum):
    LLM_PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
    LLM_RESPONSE_INVALID = "LLM_RESPONSE_INVALID"
    FABRICATED_REFERENCE = "FABRICATED_REFERENCE"
    CAUSAL_LANGUAGE_VIOLATION = "CAUSAL_LANGUAGE_VIOLATION"
    UNSUPPORTED_INFERENCE_DETECTED = "UNSUPPORTED_INFERENCE_DETECTED"
    LIMITATION_OMITTED = "LIMITATION_OMITTED"
    FALLBACK_USED = "FALLBACK_USED"
    MISSING_DOMAIN_ACKNOWLEDGED = "MISSING_DOMAIN_ACKNOWLEDGED"
    NO_SUBSTANTIVE_EVIDENCE = "NO_SUBSTANTIVE_EVIDENCE"
    POLICY_RECOMMENDATION_VIOLATION = "POLICY_RECOMMENDATION_VIOLATION"
    MEDICAL_RECOMMENDATION_VIOLATION = "MEDICAL_RECOMMENDATION_VIOLATION"


class UncertaintyCode(StrEnum):
    EVIDENCE_STRENGTH_NOT_ASSESSED = "evidence_strength_not_assessed"
    CAUSAL_INFERENCE_UNSUPPORTED = "causal_inference_unsupported"
    GENERALIZATION_LIMITED = "generalization_limited"
    DOMAIN_COVERAGE_INCOMPLETE = "domain_coverage_incomplete"
    MODEL_SCOPE_LIMITED = "model_scope_limited"


class SynthesisProviderConfig(FrozenPolarisBaseModel):
    provider_name: NonEmptyStr = "unspecified"
    timeout_seconds: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)


class SynthesisRequest(FrozenPolarisBaseModel):
    coordinated_assessment: CoordinatedAssessment
    mode: SynthesisMode = SynthesisMode.DETERMINISTIC
    evidence_artifact: EvidenceArtifact | None = None
    literature_context: LiteratureContextArtifact | None = None
    provider_config: SynthesisProviderConfig | None = None
    model_identifier: NonEmptyStr | None = None
    allow_deterministic_fallback: bool = True
    max_synthesis_length: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_matching_evidence_artifact(self) -> "SynthesisRequest":
        if self.evidence_artifact is None:
            return self
        coordinated = self.coordinated_assessment
        artifact = self.evidence_artifact
        mismatches = (
            artifact.artifact_id != coordinated.source_evidence_artifact_id,
            artifact.source_analysis_result_id != coordinated.source_analysis_result_id,
            artifact.dataset_id != coordinated.dataset_id,
            artifact.source_checksum_sha256 != coordinated.source_checksum_sha256,
        )
        if any(mismatches):
            raise ValueError("evidence artifact must match coordinated assessment lineage")
        return self


class SynthesisFinding(FrozenPolarisBaseModel):
    finding_code: SynthesisFindingCode
    severity: WarningSeverity
    message: NonEmptyStr
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


class DomainSynthesis(FrozenPolarisBaseModel):
    domain: AgentDomain
    summary: NonEmptyStr
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    limitations: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    coverage_status: CoordinationCoverageStatus

    @field_validator("referenced_claim_ids", "referenced_evidence_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitations")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class CrossDomainSynthesis(FrozenPolarisBaseModel):
    finding_id: NonEmptyStr
    summary: NonEmptyStr
    domains: tuple[AgentDomain, ...]
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_agreement_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_divergence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return _sort_domains(value)

    @field_validator(
        "referenced_claim_ids",
        "referenced_evidence_ids",
        "referenced_agreement_ids",
        "referenced_divergence_ids",
    )
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def require_support_reference(self) -> "CrossDomainSynthesis":
        if not (
            self.referenced_claim_ids
            or self.referenced_evidence_ids
            or self.referenced_agreement_ids
            or self.referenced_divergence_ids
        ):
            raise ValueError("cross-domain synthesis items require source references")
        return self


class SynthesisProvenance(FrozenPolarisBaseModel):
    source_coordinated_assessment_id: NonEmptyStr
    source_evidence_artifact_id: NonEmptyStr
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    source_assessment_ids: tuple[NonEmptyStr, ...]
    synthesis_mode_requested: SynthesisMode
    synthesis_mode_used: SynthesisMode
    provider: NonEmptyStr | None = None
    model_identifier: NonEmptyStr | None = None
    prompt_version: NonEmptyStr = SYNTHESIS_PROMPT_VERSION
    ruleset_version: NonEmptyStr = SYNTHESIS_RULESET_VERSION
    content_digest_sha256: NonEmptyStr
    synthesis_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr
    phase5_schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    phase7_schema_version: SchemaVersion = COORDINATION_SCHEMA_VERSION
    phase8_schema_version: SchemaVersion = SYNTHESIS_SCHEMA_VERSION

    @field_validator("source_assessment_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class SynthesisArtifact(FrozenPolarisBaseModel):
    synthesis_id: NonEmptyStr
    source_coordinated_assessment_id: NonEmptyStr
    synthesis_mode: SynthesisMode
    overall_summary: NonEmptyStr
    domain_summaries: tuple[DomainSynthesis, ...]
    cross_domain_findings: tuple[CrossDomainSynthesis, ...] = Field(default_factory=tuple)
    limitations_summary: NonEmptyStr
    evidence_gaps_summary: NonEmptyStr
    unsupported_inferences_preserved: tuple[UnsupportedInferenceCode, ...] = Field(
        default_factory=tuple
    )
    uncertainty: tuple[UncertaintyCode, ...] = Field(default_factory=tuple)
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_assessment_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    grounding_findings: tuple[SynthesisFinding, ...] = Field(default_factory=tuple)
    provenance: SynthesisProvenance
    schema_version: SchemaVersion = SYNTHESIS_SCHEMA_VERSION

    @field_validator(
        "referenced_claim_ids",
        "referenced_evidence_ids",
        "referenced_assessment_ids",
    )
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("unsupported_inferences_preserved")
    @classmethod
    def sort_unsupported(
        cls, value: tuple[UnsupportedInferenceCode, ...]
    ) -> tuple[UnsupportedInferenceCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("uncertainty")
    @classmethod
    def sort_uncertainty(cls, value: tuple[UncertaintyCode, ...]) -> tuple[UncertaintyCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def require_source_consistency(self) -> "SynthesisArtifact":
        if (
            self.source_coordinated_assessment_id
            != self.provenance.source_coordinated_assessment_id
        ):
            raise ValueError("synthesis source coordinated assessment ID must match provenance")
        if self.synthesis_mode != self.provenance.synthesis_mode_used:
            raise ValueError("synthesis mode must match provenance mode used")
        return self


class ProviderDomainSynthesis(FrozenPolarisBaseModel):
    domain: AgentDomain
    summary: NonEmptyStr
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    limitations: tuple[LimitationCode, ...] = Field(default_factory=tuple)


class ProviderCrossDomainSynthesis(FrozenPolarisBaseModel):
    summary: NonEmptyStr
    domains: tuple[AgentDomain, ...]
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_agreement_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_divergence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class StructuredSynthesisResponse(FrozenPolarisBaseModel):
    overall_summary: NonEmptyStr
    domain_summaries: tuple[ProviderDomainSynthesis, ...]
    cross_domain_findings: tuple[ProviderCrossDomainSynthesis, ...] = Field(default_factory=tuple)
    limitations_summary: NonEmptyStr
    evidence_gaps_summary: NonEmptyStr
    unsupported_inferences_preserved: tuple[UnsupportedInferenceCode, ...] = Field(
        default_factory=tuple
    )
    uncertainty: tuple[UncertaintyCode, ...] = Field(default_factory=tuple)
    referenced_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    referenced_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


GroundingPayload = dict[str, Any]


def _sort_domains(domains: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
    order = {domain: index for index, domain in enumerate(DOMAIN_ORDER)}
    return tuple(sorted(set(domains), key=lambda domain: order[domain]))
