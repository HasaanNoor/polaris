"""Typed search inputs and explainable dataset-search outputs."""

from enum import StrEnum

from pydantic import Field

from polaris.schemas.common import DatasetStatus, FrozenPolarisBaseModel, NonEmptyStr
from polaris.schemas.dataset import DatasetManifest


class TextMatchMode(StrEnum):
    """How all keyword-like text filters are evaluated."""

    ANY = "any"
    ALL = "all"


class DatasetCollectionType(StrEnum):
    """Stable dataset-origin categories tracked by the registry."""

    ILLUSTRATIVE = "illustrative"
    REAL_PROVIDER = "real_provider"
    SAMPLE = "sample"


class TemporalMatchType(StrEnum):
    """Relationship between dataset coverage and requested temporal coverage."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    NOT_REQUESTED = "not_requested"


class GeographicMatchType(StrEnum):
    """Relationship between dataset coverage metadata and requested geography."""

    EXACT = "exact"
    DESCRIPTION = "description"
    NONE = "none"
    NOT_REQUESTED = "not_requested"


class TemporalRequirement(FrozenPolarisBaseModel):
    """Requested year range for metadata-only coverage matching."""

    start: int | None = None
    end: int | None = None

    def model_post_init(self, __context: object) -> None:
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("temporal requirement end must not precede start")


class DatasetSearchQuery(FrozenPolarisBaseModel):
    """Structured deterministic filters for dataset manifest search."""

    keywords: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    dataset_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    providers: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    statuses: tuple[DatasetStatus, ...] = Field(default_factory=tuple)
    variable_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    variable_keywords: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    geographic: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    temporal: TemporalRequirement | None = None
    frequencies: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    licenses: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    require_unrestricted_access: bool = False
    require_methodology_reference: bool = False
    include_datasets_with_warnings: bool = True
    match_mode: TextMatchMode = TextMatchMode.ANY


class TemporalCoverageMatch(FrozenPolarisBaseModel):
    """Temporal coverage comparison returned with search results."""

    match_type: TemporalMatchType
    dataset_start: int | None = None
    dataset_end: int | None = None
    requested_start: int | None = None
    requested_end: int | None = None


class GeographicCoverageMatch(FrozenPolarisBaseModel):
    """Geographic metadata comparison returned with search results."""

    match_type: GeographicMatchType
    requested: tuple[str, ...] = Field(default_factory=tuple)
    matched: tuple[str, ...] = Field(default_factory=tuple)


class DatasetSearchResult(FrozenPolarisBaseModel):
    """Explainable metadata-search result for one registered dataset."""

    dataset_id: str
    title: str
    manifest: DatasetManifest
    collection_type: DatasetCollectionType
    matched_variable_ids: tuple[str, ...] = Field(default_factory=tuple)
    match_reasons: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    temporal_overlap: TemporalCoverageMatch | None = None
    geographic_match: GeographicCoverageMatch | None = None
