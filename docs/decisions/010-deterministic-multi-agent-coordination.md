# ADR 010: Deterministic Multi-Agent Coordination

## Status

Accepted for Phase 7.

## Context

Phase 6 produces deterministic `AgentAssessment` objects for governance, economics, education, and public health. Each assessment independently identifies domain relevance, concern codes, inherited limitations, unsupported inferences, coverage summaries, deterministic IDs, and provenance from the same Phase 5 `EvidenceArtifact`.

Polaris now needs a structural layer that explains how those domain assessments fit together. This layer must identify overlap, domain-specific differences, cross-domain evidence, cross-domain claims, missing domains, evidence gaps, shared limitations, and unsupported inferences without producing final natural-language synthesis.

The coordinator must remain deterministic. It must not use LLMs, retrieval, embeddings, external APIs, databases, causal inference, statistical recalculation, policy recommendations, autonomous debate, or report generation.

## Decision

Polaris will add `src/polaris/coordination` as the Phase 7 deterministic coordination package. The public API is:

```python
coordinated = coordinate_assessments(assessments=assessments)
```

Callers may also pass a frozen `CoordinationRequest`. The coordinator consumes Phase 6 `AgentAssessment` objects only. It does not require raw datasets, Phase 4 numerical results, Phase 5 evidence payload duplication, or an orchestration runtime.

The top-level output is a frozen `CoordinatedAssessment`. It records source evidence and analysis identifiers, dataset lineage, checksum lineage, participating and missing domains, source assessment IDs, domain coverage, evidence-domain mappings, claim-domain mappings, agreements, divergences, shared limitations, shared unsupported inferences, evidence gaps, domain gaps, coordination findings, provenance, and schema version.

Assessment compatibility is validated before coordination. Inputs are rejected when they contain duplicate domains, duplicate assessment IDs, unsupported domains, mismatched EvidenceArtifact IDs, mismatched dataset IDs, mismatched checksums, mismatched Phase 4 analysis IDs, or incompatible Phase 5/6 schema versions. Incompatible assessments are not silently merged because doing so would obscure provenance and combine unrelated analyses.

Missing domains are allowed. A missing domain means the assessment was not supplied. That is distinct from a supplied domain assessment that found no relevant evidence. Both states are represented explicitly in coverage and domain-gap records.

Agreement is defined conservatively. It means multiple domain assessments independently referenced the same structured item: evidence ID, claim ID, limitation code, unsupported-inference code, or domain concern code. It does not mean subjective consensus, truth, robustness, policy agreement, or final interpretation.

Divergence is also conservative. Phase 7 records domain-specific differences such as different relevance classification, domain-specific concern, domain-specific unsupported inference, domain-specific limitation, or uneven evidence coverage. These are not argumentative disagreements or contradictions unless a later typed contract can represent genuinely contradictory structured states.

Evidence gaps and domain gaps are first-class records. They identify conditions such as missing domain assessments, supplied domains with no relevant evidence, single-domain-only claims, cross-domain claims with limited domain coverage, evidence referenced without cross-domain context, and limited variable coverage. The coordinator does not speculate about missing datasets, controls, variables, mechanisms, or interventions.

Limitations and unsupported inferences propagate into the coordinated result. Later synthesis layers must know what they must not say, including unsupported causal, mechanism, policy, intervention, prediction, generalization, and medical conclusions.

Deterministic SHA-256 IDs are used for coordinated assessments, agreements, divergences, and gaps. IDs are based on canonical source IDs, domains, structured codes, the Phase 7 schema version, and the coordination ruleset version. Timestamps are recorded in provenance but excluded from deterministic IDs.

## Consequences

Phase 7 prepares Polaris for later interdisciplinary reasoning by creating a compact, auditable state object over domain assessments. It preserves phase boundaries: Phase 6 decides domain relevance, Phase 7 coordinates structured outputs, and later synthesis may render cautious natural language from the coordinated state.

The coordinator is not another domain expert. It does not add empirical evidence, alter Phase 5 claims, rank domains, assign confidence scores, infer causality, recommend policy, or generate report prose.

Partial coordination is possible when only one or some domain assessments are available. All-empty assessment sets return valid coordinated outputs with explicit findings and gaps rather than failing solely due to lack of relevance.

## Alternatives considered

Use `AgentMessage` for the coordinated result: rejected because `AgentMessage` is a communication envelope for orchestration, while `CoordinatedAssessment` is analytical state.

Embed full `AgentAssessment` objects in the coordinated output: rejected to avoid unnecessary duplication. Stable references and derived maps are sufficient.

Treat non-selection as disagreement: rejected because deterministic domain agents represent scoped relevance, not subjective interpretation.

Use LLM debate or natural-language synthesis: rejected for Phase 7 because coordination must be deterministic and structural. LLM-assisted synthesis remains deferred.

Merge incompatible assessments with warnings: rejected because source mismatches can combine unrelated analyses and break reproducibility.
