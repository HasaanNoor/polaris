"""Provider registry and public acquisition API."""

from collections import OrderedDict
from collections.abc import Iterable

from polaris.providers.base import (
    DownloadRequest,
    DownloadResult,
    Provider,
    ProviderDataset,
    ProviderMetadata,
    ProviderRegistry,
)
from polaris.providers.errors import ProviderNotFoundError
from polaris.providers.unesco import build_provider as build_unesco_provider
from polaris.providers.who import build_provider as build_who_provider
from polaris.providers.world_bank import build_provider as build_world_bank_provider


class DataProviderRegistry:
    """Ordered in-memory registry for provider adapters."""

    def __init__(self, providers: Iterable[Provider] = ()) -> None:
        self._providers: OrderedDict[str, Provider] = OrderedDict()
        for provider in providers:
            self.register(provider)

    def register(self, provider: Provider) -> None:
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> Provider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise ProviderNotFoundError(provider_id) from exc

    def metadata(self) -> ProviderRegistry:
        return ProviderRegistry(
            providers=tuple(provider.metadata() for provider in self._providers.values())
        )

    def list_datasets(self, provider_id: str | None = None) -> tuple[ProviderDataset, ...]:
        if provider_id is not None:
            return self.get(provider_id).available_datasets()
        datasets: list[ProviderDataset] = []
        for provider in self._providers.values():
            datasets.extend(provider.available_datasets())
        return tuple(datasets)

    def list_providers(self) -> tuple[ProviderMetadata, ...]:
        return tuple(provider.metadata() for provider in self._providers.values())


def default_provider_registry() -> DataProviderRegistry:
    """Return the built-in official public provider registry."""

    return DataProviderRegistry(
        (
            build_world_bank_provider(),
            build_who_provider(),
            build_unesco_provider(),
        )
    )


def download_dataset(
    *,
    provider: str,
    dataset: str,
    registry: DataProviderRegistry | None = None,
    **request_options: object,
) -> DownloadResult:
    """Acquire one provider dataset and create a Phase 3-compatible manifest."""

    provider_registry = registry or default_provider_registry()
    adapter = provider_registry.get(provider)
    request = DownloadRequest(provider=provider, dataset=dataset, **request_options)
    return adapter.download_dataset(request)
