# Dataset Metadata Standard

## Required Fields

Every dataset manifest must include:

- source name;
- source organization;
- source URL;
- access method;
- license or terms;
- citation;
- version or release date when available;
- retrieval timestamp;
- geographic coverage;
- temporal coverage;
- unit of analysis;
- indicator definitions;
- measurement method;
- update frequency;
- revision policy;
- missing-data codes;
- quality flags;
- known comparability limits;
- provenance record identifier.

## Indicator Metadata

Each indicator must include:

- name;
- stable identifier;
- definition;
- numerator and denominator where applicable;
- units;
- aggregation method;
- disaggregation fields;
- source table or endpoint;
- revisions;
- transformation history.

## Quality Warnings

Warnings must be structured, not buried in prose. Categories include missingness, coverage, definition change, survey design, administrative reporting, revision, comparability, licensing, and sensitive-context risk.

## Provenance

Metadata must link every observed value to a source, retrieval event, and dataset version. Derived values must link to observed inputs and transformation records.

## Phase 2 Registry Manifest Rules

Phase 2 stores candidate dataset records as local UTF-8 JSON files validated through the existing `DatasetManifest` Pydantic schema. Registry behavior must not duplicate schema validation or introduce observation ingestion.

Manifest loading is deterministic: only files ending in `.json` are loaded, unrelated files are ignored, and JSON files are processed in filename order. Empty manifest directories are valid and produce an empty registry.

Metadata search is structured and explainable. Filters across different fields use AND semantics. Multiple values within one field use ANY semantics unless `match_mode="all"` is explicitly used for keyword-style text filters. Identifiers are exact after case normalization. Text matches are case-insensitive substring checks. Search results preserve warnings and access restrictions from the manifest; a result is a metadata match, not an endorsement of dataset quality or suitability.
