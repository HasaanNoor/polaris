"""Typed Phase 23 causal-study registry contracts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.analysis.causal.models import CausalEstimand, CausalMethod, EventStudyConfig
from polaris.registry.models import DatasetCollectionType
from polaris.schemas.common import (
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    VariableId,
    VariableReference,
)

CAUSAL_STUDY_SCHEMA_VERSION = "1.0.0"
CAUSAL_STUDY_RULESET_VERSION = "causal_studies_phase23_v1"
ISO3_PATTERN = re.compile(r"^[A-Z]{3}$")


class InterventionType(StrEnum):
    LAW = "law"
    REGULATION = "regulation"
    PUBLIC_PROGRAM = "public_program"
    FUNDING_CHANGE = "funding_change"
    TAX_POLICY = "tax_policy"
    HEALTH_POLICY = "health_policy"
    EDUCATION_POLICY = "education_policy"
    GOVERNANCE_REFORM = "governance_reform"
    TRADE_POLICY = "trade_policy"
    INFRASTRUCTURE_PROGRAM = "infrastructure_program"
    ENVIRONMENTAL_POLICY = "environmental_policy"
    INSTITUTIONAL_REFORM = "institutional_reform"
    EXTERNAL_SHOCK = "external_shock"
    OTHER = "other"


class JurisdictionLevel(StrEnum):
    COUNTRY = "country"
    SUBNATIONAL = "subnational"
    REGIONAL = "regional"
    INTERNATIONAL = "international"
    OTHER = "other"


class TreatmentDateRole(StrEnum):
    ANNOUNCEMENT = "announcement_date"
    ADOPTION = "adoption_date"
    EFFECTIVE = "effective_date"
    IMPLEMENTATION = "implementation_date"


class TreatmentPersistence(StrEnum):
    ABSORBING = "absorbing"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class TreatmentReversibility(StrEnum):
    REVERSIBLE = "reversible"
    NOT_REVERSED_IN_SCOPE = "not_reversed_in_scope"
    UNKNOWN = "unknown"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    SOURCE_REVIEWED = "source_reviewed"
    METADATA_VALIDATED = "metadata_validated"
    DATA_COMPATIBLE = "data_compatible"
    DESIGN_READY = "design_ready"
    BLOCKED = "blocked"


class TreatmentStatus(StrEnum):
    TREATED = "treated"
    NEVER_TREATED = "never_treated"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


class SourceType(StrEnum):
    OFFICIAL_DOCUMENT = "official_document"
    DATASET_METADATA = "dataset_metadata"
    ACADEMIC_ARTICLE = "academic_article"
    REPORT = "report"
    WEB_PAGE = "web_page"
    OTHER = "other"


class SourceQualityCategory(StrEnum):
    PRIMARY_OFFICIAL = "primary_official"
    OFFICIAL_SECONDARY = "official_secondary"
    ACADEMIC = "academic"
    INTERGOVERNMENTAL = "intergovernmental"
    REPUTABLE_SECONDARY = "reputable_secondary"
    OTHER = "other"


class ComparisonGroupPolicy(StrEnum):
    EXPLICIT_ONLY = "explicit_only"
    NEVER_TREATED_WITHIN_SCOPE = "never_treated_within_scope"


class ReadinessStatus(StrEnum):
    READY = "ready"
    READY_WITH_WARNINGS = "ready_with_warnings"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class FindingCode(StrEnum):
    MISSING_TREATMENT_SOURCE = "missing_treatment_source"
    UNRESOLVED_ENTITY = "unresolved_entity"
    MISSING_TREATMENT_DATE = "missing_treatment_date"
    AMBIGUOUS_TREATMENT_TIMING = "ambiguous_treatment_timing"
    INSUFFICIENT_PRE_PERIODS = "insufficient_pre_periods"
    INSUFFICIENT_POST_PERIODS = "insufficient_post_periods"
    NO_CONTROL_CANDIDATES = "no_control_candidates"
    OUTCOME_NOT_AVAILABLE = "outcome_not_available"
    COVARIATE_NOT_AVAILABLE = "covariate_not_available"
    STAGGERED_TREATMENT_UNSUPPORTED = "staggered_treatment_unsupported"
    POST_TREATMENT_COVARIATE_RISK = "post_treatment_covariate_risk"
    DATASET_COVERAGE_GAP = "dataset_coverage_gap"
    SOURCE_REVIEW_REQUIRED = "source_review_required"
    DUPLICATE_STUDY_ID = "duplicate_study_id"
    DUPLICATE_INTERVENTION_ID = "duplicate_intervention_id"
    DUPLICATE_ASSIGNMENT = "duplicate_assignment"
    CONTRADICTORY_ASSIGNMENT = "contradictory_assignment"
    MISSING_SOURCE_REFERENCE = "missing_source_reference"
    METHOD_NOT_SUPPORTED = "method_not_supported"
    VARIABLE_AVAILABLE = "variable_available"
    ENTITY_AVAILABLE = "entity_available"


class VariableRole(StrEnum):
    OUTCOME = "outcome"
    COVARIATE = "covariate"


class AnnualTimingRule(FrozenPolarisBaseModel):
    date_role: TreatmentDateRole
    analysis_treatment_year: int
    rule: NonEmptyStr
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    @field_validator("source_ids")
    @classmethod
    def sort_source_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class TreatmentSource(FrozenPolarisBaseModel):
    source_id: NonEmptyStr
    title: NonEmptyStr
    publisher: NonEmptyStr | None = None
    publication_date: date | None = None
    url: str | None = None
    document_identifier: NonEmptyStr | None = None
    source_type: SourceType
    quality_category: SourceQualityCategory
    access_date: date | None = None
    citation_text: NonEmptyStr | None = None
    source_checksum: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    notes: NonEmptyStr | None = None


class InterventionDefinition(FrozenPolarisBaseModel):
    intervention_id: NonEmptyStr
    name: NonEmptyStr
    description: NonEmptyStr
    intervention_type: InterventionType
    jurisdiction_level: JurisdictionLevel
    treatment_definition: NonEmptyStr
    announcement_date: date | None = None
    adoption_date: date | None = None
    effective_date: date | None = None
    implementation_date: date | None = None
    treated_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    potentially_unaffected_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    geographic_scope: NonEmptyStr | None = None
    temporal_scope: NonEmptyStr | None = None
    treatment_persistence: TreatmentPersistence = TreatmentPersistence.UNKNOWN
    treatment_reversibility: TreatmentReversibility = TreatmentReversibility.UNKNOWN
    notes: NonEmptyStr | None = None
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    review_status: ReviewStatus = ReviewStatus.DRAFT
    schema_version: SchemaVersion = CAUSAL_STUDY_SCHEMA_VERSION

    @field_validator("treated_entities", "potentially_unaffected_entities", "source_ids")
    @classmethod
    def sort_unique_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class TreatmentAssignment(FrozenPolarisBaseModel):
    entity_id: NonEmptyStr
    treatment_status: TreatmentStatus
    treatment_start: int | float | None = None
    treatment_end: int | float | None = None
    assignment_source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    assignment_notes: NonEmptyStr | None = None
    review_status: ReviewStatus = ReviewStatus.DRAFT

    @field_validator("entity_id")
    @classmethod
    def validate_iso3_entity(cls, value: str) -> str:
        if not ISO3_PATTERN.fullmatch(value):
            raise ValueError("country-level treatment assignments require canonical ISO-3 IDs")
        return value

    @field_validator("assignment_source_ids")
    @classmethod
    def sort_assignment_sources(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def validate_treated_timing(self) -> TreatmentAssignment:
        if self.treatment_status is TreatmentStatus.TREATED and self.treatment_start is None:
            raise ValueError("treated assignments require explicit treatment_start")
        if (
            self.treatment_start is not None
            and self.treatment_end is not None
            and self.treatment_end < self.treatment_start
        ):
            raise ValueError("treatment_end must not precede treatment_start")
        return self


class StudyVariableReference(FrozenPolarisBaseModel):
    variable_id: VariableId
    dataset_id: DatasetId
    role: VariableRole
    label: NonEmptyStr | None = None
    provider: NonEmptyStr | None = None
    unit: NonEmptyStr | None = None
    post_treatment_concern: bool = False
    notes: NonEmptyStr | None = None


class CausalStudyDefinition(FrozenPolarisBaseModel):
    study_id: NonEmptyStr
    title: NonEmptyStr
    research_question: NonEmptyStr
    intervention: InterventionDefinition
    treatment_assignments: tuple[TreatmentAssignment, ...] = Field(min_length=1)
    treatment_timing_rule: AnnualTimingRule
    sources: tuple[TreatmentSource, ...] = Field(default_factory=tuple)
    proposed_outcomes: tuple[StudyVariableReference, ...] = Field(min_length=1)
    proposed_covariates: tuple[StudyVariableReference, ...] = Field(default_factory=tuple)
    candidate_dataset_ids: tuple[DatasetId, ...] = Field(default_factory=tuple)
    entity_variable: VariableReference
    time_variable: VariableReference
    estimand: CausalEstimand = CausalEstimand.ATT
    supported_methods: tuple[CausalMethod, ...] = (
        CausalMethod.DIFFERENCE_IN_DIFFERENCES,
        CausalMethod.EVENT_STUDY,
    )
    pre_period_requirements: int = Field(default=1, ge=1)
    post_period_requirements: int = Field(default=1, ge=1)
    event_study_window: EventStudyConfig | None = None
    comparison_group_policy: ComparisonGroupPolicy = ComparisonGroupPolicy.EXPLICIT_ONLY
    explicit_comparison_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    identifying_assumptions: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    known_threats: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    review_status: ReviewStatus = ReviewStatus.DRAFT
    schema_version: SchemaVersion = CAUSAL_STUDY_SCHEMA_VERSION

    @field_validator(
        "candidate_dataset_ids",
        "explicit_comparison_entities",
        "identifying_assumptions",
        "known_threats",
        "source_ids",
    )
    @classmethod
    def sort_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @model_validator(mode="after")
    def validate_shape(self) -> CausalStudyDefinition:
        outcomes = [item for item in self.proposed_outcomes if item.role is VariableRole.OUTCOME]
        if len(outcomes) != len(self.proposed_outcomes):
            raise ValueError("proposed_outcomes must use outcome variable references")
        covariates = [
            item for item in self.proposed_covariates if item.role is VariableRole.COVARIATE
        ]
        if len(covariates) != len(self.proposed_covariates):
            raise ValueError("proposed_covariates must use covariate variable references")
        return self


class CausalStudyFinding(FrozenPolarisBaseModel):
    code: FindingCode
    severity: FindingSeverity
    message: NonEmptyStr
    entity_id: NonEmptyStr | None = None
    dataset_id: DatasetId | None = None
    variable_id: VariableId | None = None
    source_id: NonEmptyStr | None = None
    details: dict[str, str] = Field(default_factory=dict)


class DatasetCompatibility(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    provider: NonEmptyStr | None = None
    collection_type: DatasetCollectionType | None = None
    entity_variable_available: bool
    time_variable_available: bool
    covered_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    missing_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    temporal_start: int | None = None
    temporal_end: int | None = None
    outcome_variables_available: tuple[VariableId, ...] = Field(default_factory=tuple)
    outcome_variables_missing: tuple[VariableId, ...] = Field(default_factory=tuple)
    covariates_available: tuple[VariableId, ...] = Field(default_factory=tuple)
    covariates_missing: tuple[VariableId, ...] = Field(default_factory=tuple)
    findings: tuple[CausalStudyFinding, ...] = Field(default_factory=tuple)


class EntityCoverage(FrozenPolarisBaseModel):
    entity_id: NonEmptyStr
    treatment_start: int | float | None
    first_available_year: int | None = None
    last_available_year: int | None = None
    available_pre_periods: int = Field(ge=0)
    available_post_periods: int = Field(ge=0)
    missing_pre_periods: tuple[int, ...] = Field(default_factory=tuple)
    missing_post_periods: tuple[int, ...] = Field(default_factory=tuple)
    sufficient_pre: bool
    sufficient_post: bool


class PrePostCoverage(FrozenPolarisBaseModel):
    treated_entity_coverage: tuple[EntityCoverage, ...] = Field(default_factory=tuple)
    control_entity_coverage: tuple[EntityCoverage, ...] = Field(default_factory=tuple)
    treated_entities_with_sufficient_coverage: tuple[NonEmptyStr, ...] = Field(
        default_factory=tuple
    )
    treated_entities_with_insufficient_coverage: tuple[NonEmptyStr, ...] = Field(
        default_factory=tuple
    )
    control_entities_with_sufficient_coverage: tuple[NonEmptyStr, ...] = Field(
        default_factory=tuple
    )
    usable_event_study_window: tuple[int, int] | None = None
    findings: tuple[CausalStudyFinding, ...] = Field(default_factory=tuple)


class ComparisonGroupDiagnostics(FrozenPolarisBaseModel):
    policy: ComparisonGroupPolicy
    explicit_control_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    candidate_never_treated_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    excluded_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    potential_control_count: int = Field(ge=0)
    findings: tuple[CausalStudyFinding, ...] = Field(default_factory=tuple)


class DesignReadinessAssessment(FrozenPolarisBaseModel):
    assessment_id: NonEmptyStr
    study_id: NonEmptyStr
    readiness_status: ReadinessStatus
    treatment_metadata_status: ReviewStatus
    source_status: ReviewStatus
    treated_entity_count: int = Field(ge=0)
    potential_control_count: int = Field(ge=0)
    dataset_compatibility: tuple[DatasetCompatibility, ...] = Field(default_factory=tuple)
    outcome_coverage: tuple[DatasetCompatibility, ...] = Field(default_factory=tuple)
    covariate_coverage: tuple[DatasetCompatibility, ...] = Field(default_factory=tuple)
    pre_treatment_coverage: PrePostCoverage
    post_treatment_coverage: PrePostCoverage
    comparison_group_diagnostics: ComparisonGroupDiagnostics
    staggered_treatment_status: NonEmptyStr
    event_study_feasibility: NonEmptyStr
    blocking_findings: tuple[CausalStudyFinding, ...] = Field(default_factory=tuple)
    warnings: tuple[CausalStudyFinding, ...] = Field(default_factory=tuple)
    recommended_human_review_items: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    provenance: dict[str, Any] = Field(default_factory=dict)
    schema_version: SchemaVersion = CAUSAL_STUDY_SCHEMA_VERSION
    ruleset_version: NonEmptyStr = CAUSAL_STUDY_RULESET_VERSION


class CausalStudySearchQuery(FrozenPolarisBaseModel):
    intervention_types: tuple[InterventionType, ...] = Field(default_factory=tuple)
    geography: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    treated_entities: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    treatment_years: tuple[int, ...] = Field(default_factory=tuple)
    outcome_domains: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    providers: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    review_statuses: tuple[ReviewStatus, ...] = Field(default_factory=tuple)
    readiness_statuses: tuple[ReadinessStatus, ...] = Field(default_factory=tuple)


def deterministic_id(prefix: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return f"{prefix}_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def identity_payload(
    model: FrozenPolarisBaseModel, *, exclude: set[str] | None = None
) -> dict[str, Any]:
    return model.model_dump(mode="json", exclude=exclude or set())
