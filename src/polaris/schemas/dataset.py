"""Dataset manifest schema."""

from pydantic import Field

from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    DatasetStatus,
    DataType,
    GeographicScope,
    NonEmptyStr,
    PolarisBaseModel,
    SchemaVersion,
    TemporalScope,
    ValidationWarning,
    VariableId,
    VariableRole,
)


class RevisionMetadata(PolarisBaseModel):
    release_date: NonEmptyStr | None = None
    revision_policy: NonEmptyStr | None = None
    update_frequency: NonEmptyStr | None = None
    source_version: NonEmptyStr | None = None


class DatasetVariable(PolarisBaseModel):
    variable_id: VariableId
    label: NonEmptyStr
    description: NonEmptyStr | None = None
    unit: NonEmptyStr | None = None
    data_type: DataType
    role: VariableRole
    source_field_name: NonEmptyStr | None = None
    missing_value_representation: list[NonEmptyStr] = Field(default_factory=list)
    comparability_notes: list[NonEmptyStr] = Field(default_factory=list)


class DatasetManifest(PolarisBaseModel):
    """Metadata contract for candidate, reviewed, or approved datasets."""

    dataset_id: DatasetId
    title: NonEmptyStr
    provider: NonEmptyStr
    source_url: NonEmptyStr
    access_url: NonEmptyStr | None = None
    description: NonEmptyStr | None = None
    license: NonEmptyStr | None = None
    status: DatasetStatus
    geographic_coverage: GeographicScope
    temporal_coverage: TemporalScope
    revision_metadata: RevisionMetadata = Field(default_factory=RevisionMetadata)
    variables: list[DatasetVariable] = Field(min_length=1)
    units: list[NonEmptyStr] = Field(default_factory=list)
    frequency: NonEmptyStr | None = None
    methodology_reference: NonEmptyStr | None = None
    comparability_warnings: list[ValidationWarning] = Field(default_factory=list)
    licensing_warnings: list[ValidationWarning] = Field(default_factory=list)
    access_restrictions: list[NonEmptyStr] = Field(default_factory=list)
    source_version: NonEmptyStr | None = None
    retrieval_timestamp: AwareDatetime | None = None
    checksum: NonEmptyStr | None = None
    schema_version: SchemaVersion = "1.0.0"
