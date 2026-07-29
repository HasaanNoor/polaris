# ADR-013: Real Dataset Acquisition and Provider Integration

## Status

Accepted.

## Context

Polaris needs real public datasets from official providers, but downstream analysis must not depend on a live internet connection. Live provider access changes over time because files move, APIs change, portals are redesigned, and source datasets are revised.

## Decision

Polaris stores provider downloads as immutable raw snapshots under `data/raw/<provider>/`. Each snapshot receives a sidecar metadata file with source URL, original filename, download timestamp, byte size, format, and SHA-256 checksum. A compatible Polaris `DatasetManifest` is generated under `data/manifests/` at acquisition time.

Provider-specific logic is isolated in `src/polaris/providers/`. The rest of Polaris works with ordinary local file paths and `DatasetManifest` objects. Phase 3 ingestion does not call provider APIs and does not need provider credentials or network access.

The initial provider registry supports:

- World Bank World Development Indicators
- WHO Global Health Observatory
- UNESCO Institute for Statistics

## Rationale

Immutable snapshots make the acquired source file a research artifact. The exact bytes used in an analysis can be validated years later with the stored checksum even if the provider later revises the dataset.

Offline reproducibility is required because research results should be recoverable from local artifacts, not from whatever a provider happens to publish at rerun time.

Raw datasets are never modified after download. Any cleaning, normalization, or derived variables must happen in later explicit pipeline stages with their own provenance.

Provider logic is isolated because official sources differ in download shape and stability. New providers can be added by implementing the provider interface, declaring metadata and datasets, and relying on the shared downloader, cache, validation, and manifest generation utilities where possible.

## Consequences

Acquisition is an explicit step before ingestion. If a file with the same checksum already exists, Polaris returns the existing snapshot rather than storing a duplicate.

Phase 10 does not add literature retrieval, internet search, LLM reasoning, autonomous agent behavior, streaming APIs, or scheduled synchronization. Those remain deferred.
