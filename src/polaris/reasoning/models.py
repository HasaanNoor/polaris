"""Typed contracts for Phase 18 evidence-grounded reasoning."""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.agents.models import AgentDomain
from polaris.coordination.models import COORDINATION_SCHEMA_VERSION, CoordinatedAssessment
from polaris.evidence.models import EVIDENCE_SCHEMA_VERSION, EvidenceArtifact
from polaris.literature.models import LITERATURE_SCHEMA_VERSION, LiteratureContextArtifact
from polaris.reasoning.taxonomy import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    SupportLevel,
)
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    WarningSeverity,
)

REASONING_SCHEMA_VERSION = "1.0.0"
REASONING_RULESET_VERSION = "evidence_grounded_phase18_v1"
REASONING_PROMPT_VERSION = "phase18_grounded_reasoning_json_v1"


class ReasoningFindingCode(str):
    pass


class ReasoningValidationFinding(FrozenPolarisBaseModel):
    finding_code: NonEmptyStr
    severity: WarningSeverity
    message: NonEmptyStr
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("source_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class ReasoningStrictness(FrozenPolarisBaseModel):
    reject_ungrounded_statements: bool = True
    reject_unsupported_causal_language: bool = True
    reject_policy_recommendations: bool = True
    reject_medical_recommendations: bool = True
    allow_provider_fallback: bool = True


class ReasoningProviderConfig(FrozenPolarisBaseModel):
    provider_name: NonEmptyStr = "unspecified"
    timeout_seconds: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)


class ReasoningRequest(FrozenPolarisBaseModel):
    research_question: NonEmptyStr
    evidence_artifact: EvidenceArtifact
    coordinated_assessment: CoordinatedAssessment
    literature_context: LiteratureContextArtifact | None = None
    mode: ReasoningMode = ReasoningMode.DETERMINISTIC
    requested_categories: tuple[ReasoningCategory, ...] = Field(
        default_factory=lambda: tuple(ReasoningCategory)
    )
    domain_focus: tuple[AgentDomain, ...] = Field(default_factory=tuple)
    max_statement_count: int | None = Field(default=None, gt=0)
    provider_config: ReasoningProviderConfig | None = None
    model_identifier: NonEmptyStr | None = None
    strictness: ReasoningStrictness = Field(default_factory=ReasoningStrictness)
    schema_version: SchemaVersion = REASONING_SCHEMA_VERSION

    @field_validator("requested_categories")
    @classmethod
    def sort_categories(cls, value: tuple[ReasoningCategory, ...]) -> tuple[ReasoningCategory, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("domain_focus")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def require_matching_lineage(self) -> "ReasoningRequest":
        artifact = self.evidence_artifact
        coordinated = self.coordinated_assessment
        mismatches = (
            artifact.artifact_id != coordinated.source_evidence_artifact_id,
            artifact.source_analysis_result_id != coordinated.source_analysis_result_id,
            artifact.dataset_id != coordinated.dataset_id,
            artifact.source_checksum_sha256 != coordinated.source_checksum_sha256,
        )
        if any(mismatches):
            raise ValueError("evidence artifact must match coordinated assessment lineage")
        if self.literature_context is not None:
            claim_ids = {claim.claim_id for claim in artifact.claim_candidates}
            if not set(self.literature_context.empirical_claim_ids) <= claim_ids:
                raise ValueError("literature context must reference known empirical claim IDs")
        return self


class ReasoningStatement(FrozenPolarisBaseModel):
    statement_id: NonEmptyStr
    category: ReasoningCategory
    text: NonEmptyStr
    evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    agent_assessment_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    literature_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    domains: tuple[AgentDomain, ...] = Field(default_factory=tuple)
    support_level: SupportLevel
    epistemic_status: EpistemicStatus
    causal_status: CausalStatus = CausalStatus.NON_CAUSAL
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    provenance: dict[str, Any] = Field(default_factory=dict)
    schema_version: SchemaVersion = REASONING_SCHEMA_VERSION

    @field_validator(
        "evidence_ids",
        "claim_ids",
        "agent_assessment_ids",
        "literature_evidence_ids",
        "limitations",
    )
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def require_grounding_and_category_status(self) -> "ReasoningStatement":
        if not (
            self.evidence_ids
            or self.claim_ids
            or self.agent_assessment_ids
            or self.literature_evidence_ids
        ):
            raise ValueError("reasoning statements require at least one grounding reference")
        if self.category is ReasoningCategory.PLAUSIBLE_MECHANISM:
            if self.epistemic_status not in {
                EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
                EpistemicStatus.SPECULATIVE,
            }:
                raise ValueError("mechanisms must be labeled plausible or speculative")
            if self.causal_status is not CausalStatus.NOT_ESTABLISHED:
                raise ValueError("mechanisms require causal_status=not_established")
            if not self.limitations:
                raise ValueError("mechanisms must state that the mechanism was not directly tested")
        if (
            self.category
            in {
                ReasoningCategory.EMPIRICAL_INTERPRETATION,
                ReasoningCategory.CROSS_DOMAIN_SYNTHESIS,
                ReasoningCategory.LITERATURE_ALIGNMENT,
                ReasoningCategory.LITERATURE_CONTRAST,
            }
            and self.epistemic_status is EpistemicStatus.SPECULATIVE
        ):
            raise ValueError("interpretive statements must not be labeled speculative")
        return self


class ContradictionRecord(FrozenPolarisBaseModel):
    contradiction_id: NonEmptyStr
    evidence_id_a: NonEmptyStr | None = None
    evidence_id_b: NonEmptyStr | None = None
    claim_id_a: NonEmptyStr | None = None
    claim_id_b: NonEmptyStr | None = None
    literature_evidence_id: NonEmptyStr | None = None
    agent_assessment_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    nature_of_conflict: NonEmptyStr
    possible_explanation: NonEmptyStr
    unresolved: bool = True

    @model_validator(mode="after")
    def require_two_sides(self) -> "ContradictionRecord":
        left = self.evidence_id_a or self.claim_id_a
        right = self.evidence_id_b or self.claim_id_b or self.literature_evidence_id
        if not left or not right:
            raise ValueError("contradictions require grounded conflicting references")
        return self


class CandidateConfounder(FrozenPolarisBaseModel):
    confounder_id: NonEmptyStr
    variable_or_concept: NonEmptyStr
    reason_it_may_matter: NonEmptyStr
    currently_measured: bool
    currently_controlled: bool
    related_domains: tuple[AgentDomain, ...] = Field(default_factory=tuple)
    supporting_source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("related_domains")
    @classmethod
    def sort_domains(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("supporting_source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class GroundingSummary(FrozenPolarisBaseModel):
    total_statements: int = Field(ge=0)
    fully_grounded_statements: int = Field(ge=0)
    statements_with_literature_support: int = Field(ge=0)
    statements_based_only_on_empirical_evidence: int = Field(ge=0)
    plausible_or_unproven_statements: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    potential_confounder_count: int = Field(ge=0)
    follow_up_hypothesis_count: int = Field(ge=0)
    follow_up_research_question_count: int = Field(ge=0)
    rejected_provider_statements: int = Field(ge=0)
    unsupported_grounding_attempts: int = Field(ge=0)
    causal_guard_violations: int = Field(ge=0)


class ReasoningProvenance(FrozenPolarisBaseModel):
    source_evidence_artifact_id: NonEmptyStr
    source_coordinated_assessment_id: NonEmptyStr
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    source_assessment_ids: tuple[NonEmptyStr, ...]
    literature_context_id: NonEmptyStr | None = None
    reasoning_mode_requested: ReasoningMode
    reasoning_mode_used: ReasoningMode
    provider: NonEmptyStr | None = None
    model_identifier: NonEmptyStr | None = None
    prompt_version: NonEmptyStr = REASONING_PROMPT_VERSION
    ruleset_version: NonEmptyStr = REASONING_RULESET_VERSION
    content_digest_sha256: NonEmptyStr
    reasoning_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    software_version: NonEmptyStr
    phase5_schema_version: SchemaVersion = EVIDENCE_SCHEMA_VERSION
    phase7_schema_version: SchemaVersion = COORDINATION_SCHEMA_VERSION
    phase14_schema_version: SchemaVersion | None = LITERATURE_SCHEMA_VERSION
    phase18_schema_version: SchemaVersion = REASONING_SCHEMA_VERSION


class ReasoningArtifact(FrozenPolarisBaseModel):
    reasoning_id: NonEmptyStr
    research_question: NonEmptyStr
    mode: ReasoningMode
    evidence_artifact_id: NonEmptyStr
    coordinated_assessment_id: NonEmptyStr
    literature_context_id: NonEmptyStr | None = None
    reasoning_statements: tuple[ReasoningStatement, ...] = Field(default_factory=tuple)
    contradictions: tuple[ContradictionRecord, ...] = Field(default_factory=tuple)
    candidate_confounders: tuple[CandidateConfounder, ...] = Field(default_factory=tuple)
    follow_up_hypotheses: tuple[ReasoningStatement, ...] = Field(default_factory=tuple)
    follow_up_research_questions: tuple[ReasoningStatement, ...] = Field(default_factory=tuple)
    limitations: tuple[ReasoningStatement, ...] = Field(default_factory=tuple)
    grounding_summary: GroundingSummary
    validation_findings: tuple[ReasoningValidationFinding, ...] = Field(default_factory=tuple)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    prompt_version: NonEmptyStr = REASONING_PROMPT_VERSION
    deterministic_fallback_used: bool = False
    provenance: ReasoningProvenance
    creation_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: SchemaVersion = REASONING_SCHEMA_VERSION

    @field_validator("reasoning_statements")
    @classmethod
    def sort_statements(
        cls, value: tuple[ReasoningStatement, ...]
    ) -> tuple[ReasoningStatement, ...]:
        ids = [item.statement_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("reasoning statement IDs must be unique")
        return tuple(sorted(value, key=lambda item: item.statement_id))

    @model_validator(mode="after")
    def require_provenance_consistency(self) -> "ReasoningArtifact":
        if self.evidence_artifact_id != self.provenance.source_evidence_artifact_id:
            raise ValueError("reasoning evidence artifact ID must match provenance")
        if self.coordinated_assessment_id != self.provenance.source_coordinated_assessment_id:
            raise ValueError("reasoning coordinated assessment ID must match provenance")
        if self.mode != self.provenance.reasoning_mode_used:
            raise ValueError("reasoning mode must match provenance")
        return self


class StructuredReasoningResponse(FrozenPolarisBaseModel):
    reasoning_statements: tuple[ReasoningStatement, ...]
    contradictions: tuple[ContradictionRecord, ...] = Field(default_factory=tuple)
    candidate_confounders: tuple[CandidateConfounder, ...] = Field(default_factory=tuple)
    provider_notes: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
