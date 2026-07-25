"""Typed contracts for deterministic Phase 6 domain-agent assessments."""

import math
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from polaris.evidence.models import LimitationCode
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    NonEmptyStr,
    SchemaVersion,
    VariableId,
)

AGENT_SCHEMA_VERSION = "1.0.0"
AGENT_RULESET_VERSION = "deterministic_phase6_v1"


class AgentDomain(StrEnum):
    GOVERNANCE = "governance"
    ECONOMICS = "economics"
    EDUCATION = "education"
    PUBLIC_HEALTH = "public_health"


class ConceptCategory(StrEnum):
    GOVERNANCE = "governance"
    INSTITUTIONS = "institutions"
    RULE_OF_LAW = "rule_of_law"
    CORRUPTION = "corruption"
    GOVERNMENT_EFFECTIVENESS = "government_effectiveness"
    POLITICAL_STABILITY = "political_stability"
    PUBLIC_SERVICES = "public_services"
    CIVIC_PARTICIPATION = "civic_participation"
    STATE_CAPACITY = "state_capacity"
    GDP = "gdp"
    INCOME = "income"
    EMPLOYMENT = "employment"
    LABOR_FORCE = "labor_force"
    PRODUCTIVITY = "productivity"
    POVERTY = "poverty"
    INEQUALITY = "inequality"
    TRADE = "trade"
    INFLATION = "inflation"
    ECONOMIC_GROWTH = "economic_growth"
    LITERACY = "literacy"
    SCHOOL_ENROLLMENT = "school_enrollment"
    EDUCATIONAL_ATTAINMENT = "educational_attainment"
    YEARS_OF_SCHOOLING = "years_of_schooling"
    COMPLETION = "completion"
    EDUCATION_ACCESS = "education_access"
    LEARNING_OUTCOMES = "learning_outcomes"
    LIFE_EXPECTANCY = "life_expectancy"
    MORTALITY = "mortality"
    MATERNAL_HEALTH = "maternal_health"
    INFANT_MORTALITY = "infant_mortality"
    DISEASE = "disease"
    HEALTHCARE_ACCESS = "healthcare_access"
    NUTRITION = "nutrition"
    FERTILITY = "fertility"
    HEALTH_EXPENDITURE = "health_expenditure"


class RelevanceStatus(StrEnum):
    RELEVANT = "relevant"
    POSSIBLY_RELEVANT = "possibly_relevant"
    NOT_RELEVANT = "not_relevant"


class RelevanceSourceType(StrEnum):
    EVIDENCE_RECORD = "evidence_record"
    CLAIM_CANDIDATE = "claim_candidate"


class RelevanceReasonCode(StrEnum):
    DIRECT_DOMAIN_VARIABLE = "DIRECT_DOMAIN_VARIABLE"
    CROSS_DOMAIN_RELATIONSHIP = "CROSS_DOMAIN_RELATIONSHIP"
    DOMAIN_CONTROL_PRESENT = "DOMAIN_CONTROL_PRESENT"
    KEYWORD_VARIABLE_MATCH = "KEYWORD_VARIABLE_MATCH"
    DIAGNOSTIC_FOR_RELEVANT_VARIABLE = "DIAGNOSTIC_FOR_RELEVANT_VARIABLE"
    SAMPLE_QUALITY_FOR_RELEVANT_VARIABLE = "SAMPLE_QUALITY_FOR_RELEVANT_VARIABLE"
    NO_DOMAIN_MATCH = "NO_DOMAIN_MATCH"


class DomainConcernCode(StrEnum):
    DIRECT_DOMAIN_VARIABLE = "DIRECT_DOMAIN_VARIABLE"
    CROSS_DOMAIN_RELATIONSHIP = "CROSS_DOMAIN_RELATIONSHIP"
    DOMAIN_CONTROL_PRESENT = "DOMAIN_CONTROL_PRESENT"
    DOMAIN_CONTROL_ABSENT = "DOMAIN_CONTROL_ABSENT"
    DOMAIN_CONTEXT_NOT_MEASURED = "DOMAIN_CONTEXT_NOT_MEASURED"
    OBSERVATIONAL_ONLY = "OBSERVATIONAL_ONLY"
    LIMITED_MODEL_SCOPE = "LIMITED_MODEL_SCOPE"
    MISSING_DATA_RELEVANT = "MISSING_DATA_RELEVANT"
    MULTICOLLINEARITY_RELEVANT = "MULTICOLLINEARITY_RELEVANT"
    HETEROSKEDASTICITY_RELEVANT = "HETEROSKEDASTICITY_RELEVANT"
    SMALL_SAMPLE_RELEVANT = "SMALL_SAMPLE_RELEVANT"
    UNSUPPORTED_CAUSAL_INFERENCE = "UNSUPPORTED_CAUSAL_INFERENCE"
    UNSUPPORTED_POLICY_INFERENCE = "UNSUPPORTED_POLICY_INFERENCE"
    UNSUPPORTED_GENERALIZATION = "UNSUPPORTED_GENERALIZATION"


class UnsupportedInferenceCode(StrEnum):
    CAUSALITY = "causality"
    MECHANISM = "mechanism"
    POLICY_EFFECTIVENESS = "policy_effectiveness"
    POPULATION_WIDE_GENERALIZATION = "population_wide_generalization"
    TEMPORAL_PREDICTION = "temporal_prediction"
    INTERVENTION_RECOMMENDATION = "intervention_recommendation"
    MEDICAL_CONCLUSION = "medical_conclusion"


class CoverageStatus(StrEnum):
    NO_RELEVANT_EVIDENCE = "no_relevant_evidence"
    RELEVANT_EVIDENCE = "relevant_evidence"


class DomainRelevanceRecord(FrozenPolarisBaseModel):
    source_id: NonEmptyStr
    source_type: RelevanceSourceType
    agent_domain: AgentDomain
    relevance_status: RelevanceStatus
    relevance_reason_codes: tuple[RelevanceReasonCode, ...] = Field(default_factory=tuple)
    matched_variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    matched_concept_categories: tuple[ConceptCategory, ...] = Field(default_factory=tuple)

    @field_validator("relevance_reason_codes")
    @classmethod
    def sort_reasons(
        cls, value: tuple[RelevanceReasonCode, ...]
    ) -> tuple[RelevanceReasonCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("matched_variable_ids")
    @classmethod
    def sort_variables(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("matched_concept_categories")
    @classmethod
    def sort_concepts(cls, value: tuple[ConceptCategory, ...]) -> tuple[ConceptCategory, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class DomainConcern(FrozenPolarisBaseModel):
    concern_code: DomainConcernCode
    source_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    variable_ids: tuple[VariableId, ...] = Field(default_factory=tuple)
    limitation_codes: tuple[LimitationCode, ...] = Field(default_factory=tuple)

    @field_validator("source_ids", "variable_ids")
    @classmethod
    def sort_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("limitation_codes")
    @classmethod
    def sort_limitations(cls, value: tuple[LimitationCode, ...]) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))


class AgentCoverageSummary(FrozenPolarisBaseModel):
    coverage_status: CoverageStatus
    total_evidence_records: int = Field(ge=0)
    relevant_evidence_count: int = Field(ge=0)
    total_claims: int = Field(ge=0)
    relevant_claim_count: int = Field(ge=0)
    direct_domain_variable_count: int = Field(ge=0)
    cross_domain_claim_count: int = Field(ge=0)
    limitations_count: int = Field(ge=0)


class AgentAssessmentProvenance(FrozenPolarisBaseModel):
    source_evidence_artifact_id: NonEmptyStr
    source_analysis_result_id: NonEmptyStr
    dataset_id: DatasetId
    source_checksum_sha256: str
    agent_domain: AgentDomain
    ruleset_version: NonEmptyStr = AGENT_RULESET_VERSION
    assessment_timestamp: AwareDatetime
    software_version: NonEmptyStr
    phase5_schema_version: SchemaVersion
    phase6_schema_version: SchemaVersion = AGENT_SCHEMA_VERSION


class AgentAssessment(FrozenPolarisBaseModel):
    assessment_id: NonEmptyStr
    agent_domain: AgentDomain
    source_evidence_artifact_id: NonEmptyStr
    relevant_evidence_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    relevant_claim_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    domain_relevance_records: tuple[DomainRelevanceRecord, ...] = Field(default_factory=tuple)
    domain_concerns: tuple[DomainConcern, ...] = Field(default_factory=tuple)
    inherited_limitations: tuple[LimitationCode, ...] = Field(default_factory=tuple)
    unsupported_inferences: tuple[UnsupportedInferenceCode, ...] = Field(default_factory=tuple)
    coverage_summary: AgentCoverageSummary
    provenance: AgentAssessmentProvenance
    schema_version: SchemaVersion = AGENT_SCHEMA_VERSION

    @field_validator("*", check_fields=False)
    @classmethod
    def require_json_safe_numbers(cls, value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("agent assessment numeric fields must be finite or None")
        return value

    @field_validator("relevant_evidence_ids", "relevant_claim_ids")
    @classmethod
    def sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))

    @field_validator("inherited_limitations")
    @classmethod
    def sort_inherited_limitations(
        cls, value: tuple[LimitationCode, ...]
    ) -> tuple[LimitationCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @field_validator("unsupported_inferences")
    @classmethod
    def sort_unsupported(
        cls, value: tuple[UnsupportedInferenceCode, ...]
    ) -> tuple[UnsupportedInferenceCode, ...]:
        return tuple(sorted(set(value), key=lambda item: item.value))

    @model_validator(mode="after")
    def require_selected_sources_have_relevance_records(self) -> "AgentAssessment":
        relevant_records = {
            record.source_id
            for record in self.domain_relevance_records
            if record.relevance_status is not RelevanceStatus.NOT_RELEVANT
        }
        selected = set(self.relevant_evidence_ids) | set(self.relevant_claim_ids)
        if not selected <= relevant_records:
            raise ValueError("selected evidence and claims must have relevance records")
        return self
