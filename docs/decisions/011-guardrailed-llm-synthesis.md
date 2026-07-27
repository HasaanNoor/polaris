# ADR 011: Guardrailed LLM-Assisted Interdisciplinary Synthesis

## Status

Accepted for Phase 8.

## Context

Phases 4 through 7 now produce deterministic statistical results, bounded evidence and claim records, domain-agent assessments, and coordinated interdisciplinary structure. Polaris needs a first natural-language layer that can explain this coordinated state without becoming a research engine itself.

This is the first phase where probabilistic language generation is allowed. The boundary is intentionally late: the LLM consumes a `CoordinatedAssessment` after deterministic evidence extraction, domain assessment, and coordination have already established claims, limitations, gaps, and unsupported-inference boundaries.

## Decision

Polaris will add `src/polaris/synthesis` as the Phase 8 synthesis package. Its public API is:

```python
artifact = synthesize_assessment(
    request=SynthesisRequest(
        coordinated_assessment=coordinated,
        mode=SynthesisMode.DETERMINISTIC,
    )
)
```

The output is a frozen `SynthesisArtifact` containing an overall summary, domain summaries, cross-domain findings, preserved unsupported inferences, uncertainty codes, referenced claim/evidence/assessment IDs, grounding findings, provenance, and a schema version.

The LLM consumes a deterministic JSON-compatible grounding payload built from `CoordinatedAssessment` and, when supplied, matching Phase 5 `EvidenceArtifact` details. It must not inspect raw CSV rows, calculate statistics, select datasets, retrieve outside facts, change claims, remove limitations, infer causal mechanisms, recommend policy, or generate medical advice.

Structured provider output is required. Polaris validates every referenced claim ID, evidence ID, agreement ID, divergence ID, assessment ID, domain, limitation, and unsupported-inference boundary before accepting LLM output. Rule-based grounding validation rejects fabricated references, unsupported positive causal language, prohibited policy recommendations, prohibited medical recommendations, omitted required limitations, and missing/no-evidence domains described as evidence-producing.

A deterministic fallback synthesizer is always available. It uses templates over the coordinated assessment and prioritizes correctness over prose quality. Environments without credentials, provider failures, malformed responses, fabricated references, and grounding violations can fall back deterministically when the request permits it.

LLM synthesis IDs are not treated as inherently deterministic. Deterministic fallback IDs use the source coordinated assessment ID, synthesis mode, ruleset version, and schema version. LLM-mode IDs include provider, model identifier, generated-content digest, ruleset version, and schema version so probabilistic output remains traceable without pretending repeated runs are identical.

No OpenAI SDK dependency is adopted in Phase 8. The package defines a minimal `SynthesisProvider` protocol for mocked or future provider implementations. Real provider credentials must not be hard-coded or stored in provenance.

## Consequences

Phase 8 gives Polaris useful interdisciplinary prose while preserving traceability to deterministic upstream artifacts. The LLM explains coordinated evidence; it does not perform the research pipeline.

Structured validation remains around probabilistic generation. Prompt rules are necessary but not sufficient, so generated output is rejected unless deterministic checks pass.

The synthesis artifact records lineage from source checksum, dataset ID, Phase 4 analysis result, Phase 5 evidence artifact, Phase 6 assessment IDs, Phase 7 coordinated assessment, and Phase 8 synthesis execution. It stores provider and model identifiers when used, but never secrets.

Causal, mechanism, policy-effectiveness, intervention, broad-generalization, prediction, and medical-conclusion boundaries remain prohibited unless later phases add explicit contracts that can support them.

Phase 8 prepares for later retrieval-grounded research by defining the post-coordination synthesis boundary and validation surface. External contextual research, source retrieval, embeddings, and report generation remain deferred.

## Alternatives considered

Let the LLM read raw data or Phase 4 results directly: rejected because synthesis should explain bounded coordinated evidence, not rerun analysis or bypass limitation propagation.

Accept free-form LLM prose: rejected because traceability, fabricated-reference detection, limitation preservation, and missing-domain handling require structured output.

Use only prompt instructions for safety: rejected because prompts cannot reliably enforce grounding, causality, policy, medical, and reference constraints.

Make LLM execution mandatory: rejected because Polaris must work in local CI and no-credential environments.

Add a broad provider framework now: rejected because Phase 8 needs only a narrow mockable provider boundary; provider selection, retrieval, and orchestration are later concerns.
