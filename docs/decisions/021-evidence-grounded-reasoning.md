# ADR-021: Evidence-Grounded Reasoning

## Status

Accepted.

## Context

Phases 4-7 establish deterministic statistical evidence, claim candidates, domain-agent assessments, and coordinated cross-domain structure. Phase 14 may add local corpus-grounded literature context. Polaris needed a reasoning layer that can interpret these artifacts without mutating them, fabricating evidence, or converting observational associations into causal conclusions.

## Decision

Polaris adds Phase 18 under `src/polaris/reasoning`. `ReasoningRequest` consumes a research question, `EvidenceArtifact`, `CoordinatedAssessment`, optional `LiteratureContextArtifact`, explicit mode, requested categories, provider settings, and strictness settings. `ReasoningArtifact` records grounded `ReasoningStatement` objects, contradictions, candidate confounders, follow-up hypotheses, follow-up research questions, limitations, validation findings, grounding summary, provenance, prompt version, and deterministic identity.

Reasoning is separated from deterministic evidence generation. It consumes structured Phase 5/6/7/14 artifacts rather than raw datasets because the evidence core is already responsible for data validation, statistics, and claim extraction. Reasoning statements must distinguish empirical interpretation, cross-domain synthesis, plausible mechanisms, alternative explanations, potential confounders, contradictions, limitations, uncertainty, follow-up hypotheses, follow-up questions, literature alignment, and literature contrast.

Empirical facts and interpretations are distinct. Mechanism hypotheses are allowed only when labeled unproven with `causal_status=not_established` and a limitation that the mechanism was not directly tested. Causal conclusions are prohibited unless a future upstream causal-identification artifact explicitly supports them.

Grounding IDs are mandatory for every substantive statement. Provider-backed reasoning uses a small structured provider protocol and versioned prompt, and provider output is parsed and validated before acceptance. Unsupported grounding, fabricated citations, unsupported causal language, policy recommendations, medical recommendations, malformed structures, duplicated IDs, and empty substantive responses are rejected or fall back according to strictness.

Literature remains contextual rather than empirical evidence. It may support alignment, contrast, or mechanism context, but it does not validate Polaris statistical findings. Alternative explanations and contradictions are first-class records so the system does not force agreement.

Reasoning remains optional in Phase 13 orchestration. When enabled, the stage order is coordination, optional literature, reasoning, synthesis, report. When disabled, existing Phase 13 behavior is unchanged.

## Consequences

Polaris gains a reproducible offline reasoning baseline and an optional provider-backed path that reuses the existing provider pattern without a second LLM framework. Phase 8 can summarize validated reasoning instead of redoing unrestricted reasoning. Phase 9 can render an optional Evidence-Grounded Interpretation section.

No hidden chain-of-thought is persisted. The artifact stores final structured statements, provenance, validation findings, and grounding summaries only. No autonomous policy recommendations, medical recommendations, web browsing, dataset selection, statistical methods, causal estimators, vector databases, or workflow systems are introduced.

## Alternatives Considered

Embedding reasoning directly in Phase 8 was rejected because synthesis summarizes evidence for reports and should not become the primary reasoning contract.

Allowing raw-dataset reasoning was rejected because it would bypass deterministic analysis, evidence extraction, and provenance.

Accepting free-form provider prose was rejected because grounding and causal guardrails require structured validation.

Treating literature as evidence validation was rejected because retrieved text is contextual and may not match the project sample, variables, or specification.
