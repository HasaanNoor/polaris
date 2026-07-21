"""Research artifact schema."""

from pydantic import Field, model_validator

from polaris.schemas.agents import AgentContributionPayload
from polaris.schemas.common import (
    ArtifactId,
    AwareDatetime,
    CausalIdentificationLevel,
    Citation,
    DatasetId,
    DataValueCategory,
    EvidenceStrength,
    FrozenPolarisBaseModel,
    InvestigationId,
    InvestigationStatus,
    NonEmptyStr,
    PolarisBaseModel,
    ProvenanceRecordId,
    Reference,
    SchemaVersion,
    ValidationWarning,
    VariableReference,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.provenance import ProvenanceRecord
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification


class InvestigationPlan(PolarisBaseModel):
    steps: list[NonEmptyStr] = Field(min_length=1)
    stop_conditions: list[NonEmptyStr] = Field(default_factory=list)


class TransformationRecord(PolarisBaseModel):
    transformation_id: NonEmptyStr
    description: NonEmptyStr
    input_references: list[Reference] = Field(default_factory=list)
    output_references: list[Reference] = Field(default_factory=list)
    provenance_record_ids: list[ProvenanceRecordId] = Field(default_factory=list)


class MissingDataDecision(PolarisBaseModel):
    decision_id: NonEmptyStr
    affected_variables: list[VariableReference] = Field(min_length=1)
    strategy: NonEmptyStr
    rationale: NonEmptyStr
    provenance_record_ids: list[ProvenanceRecordId] = Field(default_factory=list)


class ObservedDataReference(PolarisBaseModel):
    reference_id: NonEmptyStr
    dataset_id: DatasetId
    variable: VariableReference
    data_value_category: DataValueCategory = DataValueCategory.OBSERVED_VALUE


class DerivedDataReference(PolarisBaseModel):
    reference_id: NonEmptyStr
    variable: VariableReference
    transformation_id: NonEmptyStr
    data_value_category: DataValueCategory = DataValueCategory.DERIVED_VARIABLE


class UncertaintyInterval(PolarisBaseModel):
    level: float = Field(gt=0, lt=1)
    lower: float
    upper: float

    @model_validator(mode="after")
    def require_ordered_interval(self) -> "UncertaintyInterval":
        if self.upper < self.lower:
            raise ValueError("uncertainty interval upper bound must not be below lower bound")
        return self


class DescriptiveValue(PolarisBaseModel):
    value_id: NonEmptyStr
    variable: VariableReference
    statistic: NonEmptyStr
    value: float | int | str
    unit: NonEmptyStr | None = None


class EffectEstimate(PolarisBaseModel):
    estimate_id: NonEmptyStr
    estimand: NonEmptyStr
    estimate: float
    standard_error: float | None = Field(default=None, ge=0)
    interval: UncertaintyInterval | None = None
    unit: NonEmptyStr | None = None
    causal_identification_level: CausalIdentificationLevel


class ModelDiagnostic(PolarisBaseModel):
    diagnostic_id: NonEmptyStr
    name: NonEmptyStr
    value: float | int | str | bool
    passed: bool | None = None
    warning: ValidationWarning | None = None


class CausalAssessment(PolarisBaseModel):
    level: CausalIdentificationLevel
    summary: NonEmptyStr
    assumptions: list[NonEmptyStr] = Field(default_factory=list)
    threats: list[NonEmptyStr] = Field(default_factory=list)


class NarrativeInterpretation(PolarisBaseModel):
    interpretation_id: NonEmptyStr
    text: NonEmptyStr
    evidence_reference_ids: list[NonEmptyStr] = Field(min_length=1)
    data_value_category: DataValueCategory = DataValueCategory.NARRATIVE_INTERPRETATION


class AnalyticalResults(PolarisBaseModel):
    descriptive_values: list[DescriptiveValue] = Field(default_factory=list)
    effect_estimates: list[EffectEstimate] = Field(default_factory=list)
    uncertainty: list[UncertaintyInterval] = Field(default_factory=list)
    diagnostics: list[ModelDiagnostic] = Field(default_factory=list)
    causal_assessment: CausalAssessment | None = None
    narrative_interpretations: list[NarrativeInterpretation] = Field(default_factory=list)


class RobustnessResult(PolarisBaseModel):
    check_id: NonEmptyStr
    description: NonEmptyStr
    result_summary: NonEmptyStr
    passed: bool | None = None


class ConflictingFinding(PolarisBaseModel):
    finding_id: NonEmptyStr
    description: NonEmptyStr
    affected_claims: list[NonEmptyStr] = Field(default_factory=list)


class EvidenceQualityAssessment(PolarisBaseModel):
    strength: EvidenceStrength
    rationale: NonEmptyStr
    limitations: list[NonEmptyStr] = Field(default_factory=list)


class ReproducibilityMetadata(PolarisBaseModel):
    code_reference: NonEmptyStr | None = None
    software_versions: list[NonEmptyStr] = Field(default_factory=list)
    dependency_versions: list[NonEmptyStr] = Field(default_factory=list)
    random_seed: int | None = None
    execution_environment: NonEmptyStr | None = None
    validation_results: list[NonEmptyStr] = Field(default_factory=list)


class ReportReference(PolarisBaseModel):
    uri: NonEmptyStr
    generated_at: AwareDatetime | None = None


class ResearchArtifact(FrozenPolarisBaseModel):
    """Versioned machine-readable output contract for a Polaris investigation."""

    artifact_id: ArtifactId
    artifact_version: NonEmptyStr
    schema_version: SchemaVersion = "1.0.0"
    investigation_id: InvestigationId
    research_question: ResearchQuestion
    investigation_status: InvestigationStatus
    investigation_plan: InvestigationPlan
    agent_contributions: list[AgentContributionPayload] = Field(default_factory=list)
    dataset_manifests: list[DatasetManifest] = Field(default_factory=list)
    dataset_references: list[DatasetId] = Field(default_factory=list)
    provenance_records: list[ProvenanceRecord] = Field(default_factory=list)
    provenance_record_references: list[ProvenanceRecordId] = Field(default_factory=list)
    transformations: list[TransformationRecord] = Field(default_factory=list)
    missing_data_decisions: list[MissingDataDecision] = Field(default_factory=list)
    statistical_specifications: list[StatisticalSpecification] = Field(default_factory=list)
    observed_data_references: list[ObservedDataReference] = Field(default_factory=list)
    derived_data_references: list[DerivedDataReference] = Field(default_factory=list)
    analytical_results: AnalyticalResults = Field(default_factory=AnalyticalResults)
    model_diagnostics: list[ModelDiagnostic] = Field(default_factory=list)
    effect_estimates: list[EffectEstimate] = Field(default_factory=list)
    uncertainty: list[UncertaintyInterval] = Field(default_factory=list)
    causal_identification_assessment: CausalAssessment | None = None
    robustness_and_sensitivity_results: list[RobustnessResult] = Field(default_factory=list)
    conflicting_findings: list[ConflictingFinding] = Field(default_factory=list)
    evidence_quality_assessment: EvidenceQualityAssessment
    limitations: list[NonEmptyStr] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)
    errors: list[NonEmptyStr] = Field(default_factory=list)
    reproducibility_metadata: ReproducibilityMetadata = Field(
        default_factory=ReproducibilityMetadata
    )
    human_readable_report_reference: ReportReference | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def require_update_not_before_creation(self) -> "ResearchArtifact":
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        if self.investigation_status == InvestigationStatus.INSUFFICIENT_EVIDENCE:
            if self.evidence_quality_assessment.strength != EvidenceStrength.INSUFFICIENT:
                raise ValueError(
                    "insufficient-evidence artifacts require insufficient evidence strength"
                )
        return self
