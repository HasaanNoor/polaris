"""Deterministic dataset registry and metadata search."""

from polaris.registry.errors import (
    DatasetNotFoundError,
    DatasetRegistryError,
    DuplicateDatasetError,
    ManifestLoadError,
    ManifestValidationError,
)
from polaris.registry.loader import load_manifest, load_manifests, load_registry
from polaris.registry.models import (
    DatasetCollectionType,
    DatasetSearchQuery,
    DatasetSearchResult,
    GeographicCoverageMatch,
    GeographicMatchType,
    TemporalCoverageMatch,
    TemporalMatchType,
    TemporalRequirement,
    TextMatchMode,
)
from polaris.registry.registry import DatasetRegistry, infer_collection_type
from polaris.registry.search import geographic_coverage_match, temporal_coverage_match

__all__ = [
    "DatasetNotFoundError",
    "DatasetCollectionType",
    "DatasetRegistry",
    "DatasetRegistryError",
    "DatasetSearchQuery",
    "DatasetSearchResult",
    "DuplicateDatasetError",
    "GeographicCoverageMatch",
    "GeographicMatchType",
    "ManifestLoadError",
    "ManifestValidationError",
    "TemporalCoverageMatch",
    "TemporalMatchType",
    "TemporalRequirement",
    "TextMatchMode",
    "geographic_coverage_match",
    "infer_collection_type",
    "load_manifest",
    "load_manifests",
    "load_registry",
    "temporal_coverage_match",
]
