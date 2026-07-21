# ADR 006: Local Tabular Ingestion

## Status

Accepted for Phase 3.

## Context

Phase 2 can register and search candidate dataset manifests, but it does not read observations. Polaris now needs a deterministic local step that can answer whether a specific tabular file can be interpreted according to a registered `DatasetManifest`.

Phase 3 must preserve the architectural boundary between metadata search, ingestion, profiling, and later statistical analysis. It must not download data, infer scientific suitability, fit models, produce research conclusions, introduce agents, expose an API, add a database, or create a frontend.

## Decision

Polaris will implement local CSV ingestion first. An `IngestionRequest` identifies a registered dataset by `dataset_id`, a local `source_path`, optional expected checksum, and a frozen `IngestionConfiguration`. The registry resolves the manifest; the request does not embed a duplicate manifest.

The loader uses Python's standard `csv` module. Pandas is deliberately not adopted in Phase 3 because the current needs are header parsing, row preservation, exact width checks, deterministic type coercion, checksum recording, and focused validation. Those requirements are small enough to implement and test without adding a dataframe dependency or dataframe-specific semantics.

Column mapping is manifest-driven and exact. A variable maps to `DatasetVariable.source_field_name` when present. If absent, it maps to the canonical `variable_id`. Fuzzy matching, synonym inference, and similarly named column guesses are rejected because they would hide source-contract mismatches.

Strict mode treats unexpected source columns as errors. Permissive mode records them as warnings and ignores them for normalized records; unexpected values are not mapped into canonical variable values.

Normalization uses manifest `data_type`, manifest missing-value tokens, and ingestion null tokens. Strings and categorical labels are trimmed only for surrounding whitespace. Integers require exact integer text. Floats reject locale-dependent comma parsing and non-finite values. Booleans accept only `true` and `false` case-insensitively. Date and datetime values use ISO parsing only when the manifest declares those types. Ingestion does not impute values, standardize units, round floats into integers, or reinterpret arbitrary strings as booleans.

Ingestion results are immutable Pydantic records containing the manifest, request, source metadata, SHA-256 checksum, normalized records, structural validation report, data-quality profile, ingestion timestamp, and ingestion-specific provenance metadata. Phase 1 `ProvenanceRecord` is not forced because Phase 3 does not yet have an investigation identifier; the result keeps provenance-compatible source identity without inventing a false investigation context.

The structural report distinguishes parsing success, validation success, and analysis readiness. A file can parse successfully while failing validation. Analysis readiness means parsing succeeded, no retained fatal or error findings remain, and at least one source row was accepted.

The data-quality profile is deterministic and structural only: non-null counts, null counts, invalid-value counts, unique-value counts, numeric or ISO date minimum and maximum where applicable, observed type names, and duplicate record count only when manifest variables declare identifier roles.

## Consequences

Polaris can now validate small local tabular files against registered manifests without network access, global state, a database, or statistical libraries. Ingestion failures are represented with domain-specific exceptions for unusable file, checksum, or structural conditions, while row-level conversion issues are retained as typed findings.

Checksums, file size, source path, ingestion configuration, timestamp, dataset identifier, and software version are recorded so later phases can build stronger provenance and reproducibility workflows.

CSV is the only supported file format in Phase 3. TSV can be read by setting `delimiter="\t"`, but Excel, Parquet, JSON Lines, databases, cloud storage, and HTTP retrieval are deferred until a stable need exists.

The ingestion layer does not claim that a dataset is unbiased, representative, statistically valid, causally interpretable, or scientifically appropriate. Those questions belong to later data-quality, statistical, and causal-assessment phases.

## Alternatives considered

Remote dataset downloading: deferred because Phase 3 validates local files only. Retrieval requires provider-specific access rules, logging, retries, and source-version semantics that should be designed separately.

Pandas: deferred because the standard library is sufficient for deterministic CSV parsing and avoids introducing dataframe behavior before analytical phases need it.

Fuzzy field inference: rejected because inferred mappings can silently convert incompatible source files into apparently valid datasets.

Database-backed ingestion: deferred because current example datasets are small local files and do not require concurrency, indexing, migrations, or operational persistence.

Distributed processing: deferred because Phase 3 validates small local tabular files and has no demonstrated scale requirement.

Combining ingestion, profiling, and statistical analysis: rejected because structural validity, data quality, and statistical inference have different evidentiary meanings and must remain separately auditable.

Format adapter framework: deferred. Additional file formats can later be added behind the stable `IngestionRequest`, loader output, validation report, normalized record, and result contracts without changing manifest semantics.
