"""Shared schema primitives and controlled Polaris vocabularies."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("value must not be empty")
    return value


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


NonEmptyStr = Annotated[str, AfterValidator(_non_empty)]
SchemaVersion = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
AwareDatetime = Annotated[datetime, AfterValidator(_utc_datetime)]

ArtifactId = NonEmptyStr
InvestigationId = NonEmptyStr
QuestionId = NonEmptyStr
AgentId = NonEmptyStr
DatasetId = NonEmptyStr
VariableId = NonEmptyStr
ProvenanceRecordId = NonEmptyStr
MessageId = NonEmptyStr
SpecificationId = NonEmptyStr
GeographicCode = NonEmptyStr


class PolarisBaseModel(BaseModel):
    """Base model that keeps public schemas strict by default."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class FrozenPolarisBaseModel(BaseModel):
    """Base model for immutable historical records."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class QuestionCategory(StrEnum):
    DESCRIPTIVE = "descriptive"
    CORRELATIONAL = "correlational"
    PREDICTIVE = "predictive"
    COMPARATIVE = "comparative"
    QUASI_EXPERIMENTAL = "quasi_experimental"
    EXPERIMENTAL = "experimental"
    SYNTHESIS = "synthesis"


class EvidenceCategory(StrEnum):
    DESCRIPTIVE = "descriptive"
    CORRELATIONAL = "correlational"
    PREDICTIVE = "predictive"
    QUASI_EXPERIMENTAL = "quasi_experimental"
    EXPERIMENTAL = "experimental"
    SYNTHESIZED = "synthesized"


class EvidenceStrength(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"


class InvestigationStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ANALYZED = "analyzed"
    CRITIQUED = "critiqued"
    REPORTED = "reported"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_IDENTIFIABLE = "not_identifiable"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    FAILED_VALIDATION = "failed_validation"
    FAILED_EXECUTION = "failed_execution"


class WarningSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DatasetStatus(StrEnum):
    CANDIDATE = "candidate"
    REVIEWED_CANDIDATE = "reviewed_candidate"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class DataType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"


class VariableRole(StrEnum):
    OUTCOME = "outcome"
    EXPOSURE = "exposure"
    PREDICTOR = "predictor"
    COVARIATE = "covariate"
    GROUPING = "grouping"
    TIME = "time"
    WEIGHT = "weight"
    IDENTIFIER = "identifier"
    QUALITY_FLAG = "quality_flag"


class AgentMessageType(StrEnum):
    INVESTIGATION_REQUEST = "investigation_request"
    AGENT_CONTRIBUTION = "agent_contribution"
    VALIDATION_FAILURE = "validation_failure"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    COMPLETION_NOTIFICATION = "completion_notification"


class AgentMessageStatus(StrEnum):
    CREATED = "created"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    COMPLETED = "completed"


class ProvenanceOperationType(StrEnum):
    RETRIEVE_SOURCE_DATA = "retrieve_source_data"
    RECORD_OBSERVED_VALUE = "record_observed_value"
    TRANSFORM_VALUE = "transform_value"
    IMPUTE_VALUE = "impute_value"
    DERIVE_VARIABLE = "derive_variable"
    PRODUCE_STATISTICAL_OUTPUT = "produce_statistical_output"
    PRODUCE_NARRATIVE_INTERPRETATION = "produce_narrative_interpretation"
    VALIDATE_ARTIFACT = "validate_artifact"


class ActorType(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class DataValueCategory(StrEnum):
    RETRIEVED_SOURCE_DATA = "retrieved_source_data"
    OBSERVED_VALUE = "observed_value"
    TRANSFORMED_VALUE = "transformed_value"
    IMPUTED_VALUE = "imputed_value"
    DERIVED_VARIABLE = "derived_variable"
    STATISTICAL_OUTPUT = "statistical_output"
    NARRATIVE_INTERPRETATION = "narrative_interpretation"


class StatisticalAnalysisType(StrEnum):
    DESCRIPTIVE = "descriptive"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    PREDICTION = "prediction"
    QUASI_EXPERIMENTAL = "quasi_experimental"
    EXPERIMENTAL = "experimental"
    SYNTHESIS = "synthesis"


class StatisticalModelFamily(StrEnum):
    NONE = "none"
    LINEAR = "linear"
    LOGISTIC = "logistic"
    POISSON = "poisson"
    SURVIVAL = "survival"
    TREE_BASED = "tree_based"
    BAYESIAN = "bayesian"


class StatisticalProcedure(StrEnum):
    DESCRIPTIVE_STATISTICS = "descriptive_statistics"
    PEARSON_CORRELATION = "pearson_correlation"
    SPEARMAN_CORRELATION = "spearman_correlation"
    ORDINARY_LEAST_SQUARES = "ordinary_least_squares"
    PANEL_ENTITY_FE = "panel_entity_fe"
    PANEL_TWO_WAY_FE = "panel_two_way_fe"
    FIRST_DIFFERENCE = "first_difference"
    BINARY_LOGISTIC_REGRESSION = "binary_logistic_regression"


class CausalIdentificationLevel(StrEnum):
    NOT_CAUSAL = "not_causal"
    DESCRIPTIVE_ONLY = "descriptive_only"
    ASSOCIATIONAL = "associational"
    PREDICTIVE_ONLY = "predictive_only"
    QUASI_EXPERIMENTAL_CLAIM = "quasi_experimental_claim"
    EXPERIMENTAL_CLAIM = "experimental_claim"
    NOT_IDENTIFIABLE = "not_identifiable"


class Citation(PolarisBaseModel):
    title: NonEmptyStr
    url: str | None = None
    accessed_at: AwareDatetime | None = None


class Warning(PolarisBaseModel):
    severity: WarningSeverity
    code: NonEmptyStr
    message: NonEmptyStr


class ValidationWarning(Warning):
    field: NonEmptyStr | None = None


class TemporalScope(PolarisBaseModel):
    start: int | None = None
    end: int | None = None
    label: NonEmptyStr | None = None

    @property
    def is_bounded(self) -> bool:
        return self.start is not None and self.end is not None

    def model_post_init(self, __context: object) -> None:
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("temporal scope end must not precede start")


class GeographicScope(PolarisBaseModel):
    codes: list[GeographicCode] = Field(min_length=1)
    description: NonEmptyStr | None = None


class VariableReference(PolarisBaseModel):
    variable_id: VariableId
    label: NonEmptyStr | None = None


class EvidenceReference(PolarisBaseModel):
    reference_id: NonEmptyStr
    evidence_category: EvidenceCategory
    data_value_category: DataValueCategory | None = None


class ArtifactReference(PolarisBaseModel):
    artifact_id: ArtifactId
    artifact_version: NonEmptyStr | None = None


class Reference(PolarisBaseModel):
    reference_id: NonEmptyStr
    reference_type: NonEmptyStr
    description: NonEmptyStr | None = None
