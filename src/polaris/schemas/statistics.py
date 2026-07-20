"""Statistical specification schema."""

from pydantic import Field, model_validator

from polaris.schemas.common import (
    CausalIdentificationLevel,
    NonEmptyStr,
    PolarisBaseModel,
    SchemaVersion,
    SpecificationId,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    VariableReference,
    InvestigationId,
)


class TransformationSpec(PolarisBaseModel):
    variable: VariableReference
    description: NonEmptyStr


class MissingDataStrategy(PolarisBaseModel):
    strategy: NonEmptyStr
    rationale: NonEmptyStr
    affected_variables: list[VariableReference] = Field(default_factory=list)


class WeightingSpec(PolarisBaseModel):
    weight_variable: VariableReference | None = None
    description: NonEmptyStr


class StandardErrorSpec(PolarisBaseModel):
    strategy: NonEmptyStr
    cluster_variables: list[VariableReference] = Field(default_factory=list)


class StatisticalSpecification(PolarisBaseModel):
    """Requested analytical procedure, without calculated results."""

    specification_id: SpecificationId
    investigation_id: InvestigationId
    analysis_type: StatisticalAnalysisType
    model_family: StatisticalModelFamily = StatisticalModelFamily.NONE
    outcome_variable: VariableReference
    exposure_variables: list[VariableReference] = Field(default_factory=list)
    covariates: list[VariableReference] = Field(default_factory=list)
    grouping_variables: list[VariableReference] = Field(default_factory=list)
    fixed_effects: list[VariableReference] = Field(default_factory=list)
    time_variable: VariableReference | None = None
    unit_of_analysis: NonEmptyStr
    sample_restrictions: list[NonEmptyStr] = Field(default_factory=list)
    missing_data_strategy: MissingDataStrategy
    transformations: list[TransformationSpec] = Field(default_factory=list)
    weighting: WeightingSpec | None = None
    standard_error_strategy: StandardErrorSpec | None = None
    multiple_comparison_strategy: NonEmptyStr | None = None
    confidence_level: float = Field(gt=0, lt=1)
    robustness_checks_requested: list[NonEmptyStr] = Field(default_factory=list)
    causal_identification_claim_level: CausalIdentificationLevel
    assumptions: list[NonEmptyStr] = Field(default_factory=list)
    schema_version: SchemaVersion = "1.0.0"

    @model_validator(mode="after")
    def require_exposure_for_relationship_models(self) -> "StatisticalSpecification":
        relationship_types = {
            StatisticalAnalysisType.CORRELATION,
            StatisticalAnalysisType.REGRESSION,
            StatisticalAnalysisType.PREDICTION,
            StatisticalAnalysisType.QUASI_EXPERIMENTAL,
            StatisticalAnalysisType.EXPERIMENTAL,
        }
        if self.analysis_type in relationship_types and not self.exposure_variables:
            raise ValueError("relationship analyses require exposure or predictor variables")
        return self
