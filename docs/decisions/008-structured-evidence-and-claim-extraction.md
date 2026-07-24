# ADR 008: Structured Evidence and Claim Extraction

## Status

Accepted for Phase 5.

## Context

Phase 4 produces deterministic statistical results, diagnostics, findings, sample summaries, result identifiers, and provenance. Later Polaris phases will include domain agents and synthesis workflows, but those components should not consume raw numerical-library output or infer meaning directly from implementation-specific statistical structures.

Polaris needs a semantic bridge that preserves calculated facts while preventing unsupported interpretation. The bridge must remain deterministic, local, typed, and auditable. It must not use LLMs, agents, external APIs, databases, retrieval systems, automatic causal inference, policy recommendation generation, or domain-specific narrative interpretation.

## Decision

Polaris will add `src/polaris/evidence` as the Phase 5 deterministic evidence package. Its public entry point is `extract_evidence(analysis_result=result)`. The service accepts a Phase 4 `AnalysisResult`, extracts structured `EvidenceRecord` variants, derives bounded `ClaimCandidate` objects, links each claim to supporting evidence IDs, propagates typed limitation codes, and returns an immutable `EvidenceArtifact`.

The initial evidence taxonomy is deliberately small:

- descriptive summary;
- correlation;
- regression coefficient;
- model fit;
- model diagnostic;
- sample quality;
- analysis warning.

The initial claim taxonomy is also conservative:

- descriptive observation;
- association;
- conditional association;
- statistical uncertainty;
- model limitation.

Claims do not contain generated narrative conclusions. They carry structured fields such as variables, direction, procedure, support IDs, limitation codes, threshold comparison fields where Phase 4 explicitly supplied them, and `causal = false`.

Evidence IDs and claim IDs are deterministic SHA-256 hashes over canonicalized identity fields and the Phase 5 schema version. Timestamps are provenance metadata and are excluded from identity hashes. Output records are sorted by deterministic IDs. Claim support IDs, variables, and limitation codes are sorted to prevent incidental ordering from changing outputs.

Phase 5 prohibits causal claims. Correlations, OLS coefficients, statistical threshold comparisons, and temporal ordering are not converted into causal propositions. Association and conditional-association claims carry observational and unsupported-generalization limitations by default. OLS conditional-association claims also carry limited-model-scope limitations. Diagnostic, warning, and sample-construction limitations propagate into related claims.

Strength labels such as weak, moderate, strong, good fit, poor fit, important, or meaningful are deferred. Phase 5 stores numerical evidence and typed limitations only. Substantive interpretation, domain context, practical significance, evidence-quality ratings, and causal identification belong to later methodology-specific phases.

## Consequences

Later agents can consume a stable, machine-readable evidence layer rather than raw statistical-library output. They can trace claim candidates to evidence records, Phase 4 results, Phase 3 source checksums, sample construction, diagnostics, and limitations.

Phase 5 improves safety by making unsupported interpretation structurally difficult: claims require supporting evidence IDs, default to non-causal, reject causal truth values, avoid free-form conclusion fields, and use a limited taxonomy.

The evidence layer remains extensible through explicit new evidence types, claim types, limitation codes, tests, examples, and ADR updates. Unsupported future Phase 4 result types must be handled deliberately rather than silently ignored.

The layer does not decide whether evidence is substantively important, practically meaningful, policy relevant, externally valid beyond the analysis sample, or causally identified. Those responsibilities remain deferred.

## Alternatives considered

Let future agents read Phase 4 results directly: rejected because raw result contracts expose numerical facts but do not encode bounded claim support, limitation propagation, or claim-to-evidence links.

Generate narrative conclusions immediately: rejected because Phase 5 must be deterministic and must not introduce unsupported prose, domain interpretation, causal language, or LLM behavior.

Store full evidence payloads inside each claim: rejected because duplicating evidence would obscure lineage and make updates harder to audit. Claims reference evidence IDs instead.

Use arbitrary strength labels for correlations or model fit: rejected because no Phase 5 methodology defines thresholds for substantive strength.

Include timestamps in evidence and claim IDs: rejected because execution time is provenance metadata, not part of deterministic identity.
