"""Provenance record schema."""

from pydantic import Field

from polaris.schemas.common import (
    ActorType,
    ArtifactId,
    AwareDatetime,
    DatasetId,
    DataValueCategory,
    FrozenPolarisBaseModel,
    InvestigationId,
    NonEmptyStr,
    ProvenanceOperationType,
    ProvenanceRecordId,
    Reference,
    SchemaVersion,
    ValidationWarning,
)


class SourceDatasetReference(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    source_version: NonEmptyStr | None = None
    retrieval_timestamp: AwareDatetime | None = None


class ProvenanceRecord(FrozenPolarisBaseModel):
    """Immutable lineage record for data, outputs, and interpretations."""

    provenance_record_id: ProvenanceRecordId
    investigation_id: InvestigationId
    artifact_id: ArtifactId | None = None
    timestamp: AwareDatetime
    actor_type: ActorType
    actor_id: NonEmptyStr
    operation_type: ProvenanceOperationType
    data_value_category: DataValueCategory
    input_references: list[Reference] = Field(default_factory=list)
    output_references: list[Reference] = Field(default_factory=list)
    source_dataset_references: list[SourceDatasetReference] = Field(default_factory=list)
    transformation_description: NonEmptyStr | None = None
    software_version: NonEmptyStr | None = None
    configuration_hash: NonEmptyStr | None = None
    code_reference: NonEmptyStr | None = None
    parameters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    warnings: list[ValidationWarning] = Field(default_factory=list)
    parent_provenance_record_ids: list[ProvenanceRecordId] = Field(default_factory=list)
    schema_version: SchemaVersion = "1.0.0"
