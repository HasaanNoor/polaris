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
