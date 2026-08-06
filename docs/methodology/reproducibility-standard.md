# Reproducibility Standard

## Purpose

Polaris investigations must be reproducible from recorded inputs, code, configuration, and artifact metadata.

## Required Metadata

Every investigation must record:

- research question and classification;
- dataset sources, versions, access dates, and retrieval parameters;
- source licenses and access constraints;
- transformation steps and code references;
- statistical specifications;
- random seeds when random processes are used;
- software and dependency versions when code exists;
- execution environment metadata;
- validation results;
- harmonization request, variable mappings, country/year normalization rules, join type, duplicate behavior, missingness reasons, and value-level provenance when a derived harmonized dataset is used;
- report generation metadata.

## Artifact Reproduction

The machine-readable artifact is the canonical record. The human-readable report must be regenerable from the artifact and templates.

## Data Publication and Privacy

When data cannot be redistributed because of licensing, confidentiality, privacy, or security constraints, Polaris must record how the data was accessed and what is required for authorized reproduction. De-identification and sensitive-data review are required before any public release.

## Versioning

Artifact versions must be immutable. Later corrections must create a new version that references the earlier one and explains the change.

## References

- World Bank DIME, [Reproducible Research](https://dimewiki.worldbank.org/Reproducible_Research).
- World Bank DIME, [Reproducibility](https://dimewiki.worldbank.org/Reproducibility).
- United Nations Statistics Division, [United Nations National Quality Assurance Frameworks Manual for Official Statistics](https://unstats.un.org/unsd/methodology/dataquality/un-nqaf/).
