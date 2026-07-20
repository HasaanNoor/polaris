"""Research question schema."""

from pydantic import Field

from polaris.schemas.common import (
    AwareDatetime,
    EvidenceStrength,
    GeographicScope,
    NonEmptyStr,
    PolarisBaseModel,
    QuestionCategory,
    QuestionId,
    SchemaVersion,
    TemporalScope,
    ValidationWarning,
    VariableReference,
)


class ResearchQuestion(PolarisBaseModel):
    """Typed representation of an analyzable user research question."""

    question_id: QuestionId
    raw_text: NonEmptyStr
    normalized_text: NonEmptyStr | None = None
    category: QuestionCategory
    outcome_variables: list[VariableReference] = Field(min_length=1)
    exposure_variables: list[VariableReference] = Field(default_factory=list)
    covariates: list[VariableReference] = Field(default_factory=list)
    population: NonEmptyStr
    geographic_scope: GeographicScope
    temporal_scope: TemporalScope
    unit_of_analysis: NonEmptyStr
    requested_evidence_level: EvidenceStrength
    requested_analytical_methods: list[NonEmptyStr] = Field(default_factory=list)
    assumptions: list[NonEmptyStr] = Field(default_factory=list)
    exclusions: list[NonEmptyStr] = Field(default_factory=list)
    required_metadata: list[NonEmptyStr] = Field(default_factory=list)
    validation_warnings: list[ValidationWarning] = Field(default_factory=list)
    created_at: AwareDatetime
    schema_version: SchemaVersion = "1.0.0"
