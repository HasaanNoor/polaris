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
- project ID, execution plan, explicit stage results, completed upstream artifact IDs, failed stage if any, and project-level provenance when a Phase 13 project orchestrator is used;
- literature corpus ID, source document checksums, source paths, citation metadata, chunking configuration, retrieval mode, retrieval queries, and literature context artifact ID when Phase 14 literature context is used;
- WHO acquisition catalog path, selected WHO indicator IDs, source snapshot checksums, reviewed mapping ruleset version, dimension filters, aggregate/projection exclusion counts, deferred-indicator registry, and WHOHealthPanel ID when Phase 15 WHO data is used;
- WGI source snapshot paths, official WGI indicator IDs, source checksums, reviewed mapping ruleset version, country/temporal rules, aggregate/territory exclusion counts, uncertainty metadata availability, and WGIGovernancePanel ID when Phase 16 WGI data is used;
- UNESCO source file paths, UNESCO indicator IDs, source checksums, reviewed mapping ruleset version, country/temporal rules, dimension filters, aggregate/territory/subgroup exclusion counts, deferred-indicator registry, and UNESCOEducationPanel ID when Phase 17 UNESCO data is used;
- reasoning mode, requested reasoning categories, grounding source IDs, strictness configuration, provider metadata when used, prompt version, validation findings, grounding summary, and ReasoningArtifact ID when Phase 18 reasoning is used;
- benchmark case ID, expected reasoning behavior, benchmark tags, evaluator version, dimension results, findings, metrics, reasoning modes, suite ID, and BenchmarkSuiteResult ID-equivalent payload when Phase 19 evaluation is used;
- MCP resource URI, tool name, validated request payload, artifact references, configured resource roots, server configuration, transport, and safe error payload when Phase 20 MCP is used;
- panel procedure, entity variable, time variable, fixed-effect configuration, cluster variable, lag specifications, panel sample summary, within/between variation, transformed diagnostics, and lag exclusions when Phase 21 panel analysis is used;
- report generation metadata.

## Artifact Reproduction

The machine-readable artifact is the canonical record. The human-readable report must be regenerable from the artifact and templates.

For Phase 13 projects, deterministic project IDs must be derived from stable inputs such as the research question, dataset identifiers or checksums, harmonization configuration, statistical specification, selected agents, synthesis mode, report settings, geographic scope, temporal scope, and orchestration schema version. Execution timestamps are allowed in stage metadata and project provenance, but they must not affect project identity. Failures must stop downstream execution while preserving completed artifacts for inspection.

For Phase 14 literature context, corpus IDs and literature context IDs must be derived from stable document checksums, chunking configuration, empirical claim IDs, retrieval queries, and corpus identity. Retrieval timestamps may appear in provenance but must not affect deterministic artifact identity. Raw literature files must remain unmodified.

For Phase 15 WHO panels, panel IDs must be derived from stable indicator IDs, source checksums, mapping rules, dimension filters, geographic/temporal scope, schema version, and ruleset version. Creation timestamps may appear in metadata but must not affect identity. Raw WHO snapshots must remain unmodified.

For Phase 16 WGI panels, panel IDs must be derived from source checksums, selected WGI variables, country rules, temporal rules, schema version, and ruleset version. Creation timestamps may appear in metadata but must not affect identity. Raw WGI ZIP snapshots must remain unmodified.

For Phase 17 UNESCO panels, panel IDs must be derived from source checksums, selected UNESCO indicator IDs, mapping rules, dimension filters, geographic/temporal rules, schema version, and ruleset version. Creation timestamps may appear in metadata but must not affect identity. Raw UNESCO files must remain unmodified.

For Phase 18 reasoning artifacts, reasoning IDs must be derived from stable upstream artifact IDs, research question, mode, requested categories, strictness-relevant configuration, content digest, schema version, and ruleset version. Creation timestamps may appear in metadata but must not affect identity. Reasoning must not mutate evidence, reread raw datasets, persist hidden chain-of-thought, fabricate citations, or accept unsupported causal claims.

For Phase 19 benchmark evaluation, benchmark cases must contain the structured artifacts
needed to reproduce evaluation and must not require raw datasets. Evaluation IDs must be
derived from stable benchmark IDs, reasoning artifact IDs, dimension results, metrics,
evaluator version, and schema version. Creation timestamps may appear in metadata but must
not affect deterministic identity. Regression benchmarks should detect grounding coverage
drops, causal overclaims, missed contradictions, lost limitations, literature/evidence
mixing, fabricated citations, and unintended deterministic reasoning changes without
requiring exact prose equality except for intentional deterministic fixtures.

For Phase 20 MCP access, reproducibility depends on the same underlying Polaris artifacts
and public APIs used outside MCP. MCP responses must serialize deterministically, return
artifact references for large outputs, preserve provenance resources, and record validation
or execution errors without stack traces or secrets. MCP clients must supply explicit
methodological inputs; the server must not infer datasets, variables, mappings, models,
agents, causal claims, or recommendations. Raw provider files and arbitrary filesystem paths
remain outside the reproducibility package exposed by MCP.

For Phase 21 panel analysis, analysis IDs must be derived from the source checksum,
statistical specification, entity/time variables, fixed-effect configuration, clustering,
lag configuration, and schema version. Analysis timestamps may appear in provenance but
must not affect identity. Lags must be reproducible from sorted entity-time records and
must not cross entity boundaries. Missing periods, unbalanced coverage, low cluster counts,
and time-invariant predictors must remain visible in result metadata or validation errors.

## Data Publication and Privacy

When data cannot be redistributed because of licensing, confidentiality, privacy, or security constraints, Polaris must record how the data was accessed and what is required for authorized reproduction. De-identification and sensitive-data review are required before any public release.

## Versioning

Artifact versions must be immutable. Later corrections must create a new version that references the earlier one and explains the change.

## References

- World Bank DIME, [Reproducible Research](https://dimewiki.worldbank.org/Reproducible_Research).
- World Bank DIME, [Reproducibility](https://dimewiki.worldbank.org/Reproducibility).
- United Nations Statistics Division, [United Nations National Quality Assurance Frameworks Manual for Official Statistics](https://unstats.un.org/unsd/methodology/dataquality/un-nqaf/).

## Phase 22 Causal Identifiers

Causal analysis identifiers include source checksums, the full `CausalSpecification`, treatment assignment, treatment timing, event window, covariates, fixed-effects configuration, clustering configuration, schema version, and ruleset version. Timestamps are retained in provenance but excluded from deterministic IDs.

## Phase 23 Causal-Study Identifiers

Causal-study, intervention, and readiness identifiers are derived from stable metadata: intervention definition, assignment records, source IDs and source metadata, treatment timing rule, variable references, schema version, and ruleset version. Retrieval or execution timestamps may appear in provenance but must not define identity. Registry-built `CausalSpecification` objects preserve study ID, intervention ID, treatment source IDs, assignment source IDs, review status, schema version, and ruleset version so Phase 22 results remain traceable to treatment metadata.
