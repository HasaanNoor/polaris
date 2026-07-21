"""Deterministic in-memory registry for validated dataset manifests."""

from collections import OrderedDict
from collections.abc import Iterable, Iterator

from polaris.registry.errors import (
    DatasetNotFoundError,
    DatasetRegistryError,
    DuplicateDatasetError,
)
from polaris.registry.models import DatasetSearchQuery, DatasetSearchResult
from polaris.registry.search import manifest_matches_query, warning_messages
from polaris.schemas.dataset import DatasetManifest


class DatasetRegistry:
    """Ordered in-memory collection of validated DatasetManifest records."""

    def __init__(self, manifests: Iterable[DatasetManifest] = ()) -> None:
        self._manifests: OrderedDict[str, DatasetManifest] = OrderedDict()
        self.register_many(manifests)

    @property
    def count(self) -> int:
        return len(self._manifests)

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[DatasetManifest]:
        return iter(self.list_all())

    def contains(self, dataset_id: str) -> bool:
        return dataset_id in self._manifests

    def get(self, dataset_id: str) -> DatasetManifest:
        try:
            return self._manifests[dataset_id]
        except KeyError as exc:
            raise DatasetNotFoundError(dataset_id) from exc

    def register(self, manifest: DatasetManifest) -> None:
        if not isinstance(manifest, DatasetManifest):
            raise DatasetRegistryError("registered object must be a DatasetManifest instance")
        if manifest.dataset_id in self._manifests:
            raise DuplicateDatasetError(manifest.dataset_id)
        self._manifests[manifest.dataset_id] = manifest

    def register_many(self, manifests: Iterable[DatasetManifest]) -> None:
        for manifest in manifests:
            self.register(manifest)

    def list_all(self) -> tuple[DatasetManifest, ...]:
        return tuple(self._manifests.values())

    def search(self, query: DatasetSearchQuery | None = None) -> tuple[DatasetSearchResult, ...]:
        active_query = query or DatasetSearchQuery()
        results: list[DatasetSearchResult] = []
        for manifest in self._manifests.values():
            matched, variables, reasons, temporal_match, geographic_match = manifest_matches_query(
                manifest,
                active_query,
            )
            if matched:
                results.append(
                    DatasetSearchResult(
                        dataset_id=manifest.dataset_id,
                        title=manifest.title,
                        manifest=manifest,
                        matched_variable_ids=variables,
                        match_reasons=reasons,
                        warnings=warning_messages(manifest),
                        temporal_overlap=temporal_match,
                        geographic_match=geographic_match,
                    )
                )
        return tuple(results)
