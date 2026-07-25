# ADR 009: Deterministic Domain Agents

## Status

Accepted for Phase 6.

## Context

Phase 5 produces immutable `EvidenceArtifact` outputs containing structured evidence records, bounded non-causal claim candidates, limitation codes, and provenance. Polaris now needs a first domain-agent layer that can inspect this structured evidence and identify which parts matter to specific research domains without producing final interdisciplinary interpretation.

This phase must remain deterministic. It must not use LLMs, external APIs, retrieval systems, databases, vector stores, causal inference, policy recommendations, agent debate, coordinator synthesis, or final report generation.

## Decision

Polaris will add `src/polaris/agents` as the Phase 6 deterministic domain-agent package. The first core domains are explicitly enumerated:

- governance;
- economics;
- education;
- public health.

Each domain agent consumes a Phase 5 `EvidenceArtifact` and returns a frozen `AgentAssessment`. Assessments reference relevant evidence and claims by ID rather than duplicating evidence payloads. They include domain relevance records, concern codes, inherited limitations, unsupported inference codes, coverage summaries, deterministic assessment IDs, and provenance.

Domain relevance is rule-based. Variable IDs are classified through an explicit concept taxonomy and canonical mappings, with conservative token-based fallback for stable keywords only. The rules do not use fuzzy matching, embeddings, LLM classification, or outside contextual knowledge.

Agents may select the same evidence or claim. Cross-domain evidence is expected: for example, a literacy-to-fertility association can be relevant to both education and public health, and an economics agent may select the same relationship when GDP appears as a model variable. Domain ownership is not exclusive.

Unsupported inference categories are explicit, typed, and deterministic. Association evidence does not support causality, mechanisms, policy effectiveness, intervention recommendations, temporal prediction, or broad generalization beyond the encoded limitations. The public-health agent also marks medical conclusions unsupported.

Limitations from Phase 5 evidence and claim candidates must propagate into domain assessments. A domain agent may add concern codes, but it must not delete source limitations or strengthen Phase 5 claims.

Phase 6 exposes `run_domain_agent(domain=..., evidence_artifact=...)` and `run_all_domain_agents(evidence_artifact=...)`. Running all agents uses deterministic domain order and does not perform coordinator synthesis.

## Consequences

Later Polaris phases can reason over stable domain-specific assessment objects rather than raw evidence artifacts or generated prose. The system gains domain relevance, cross-domain selection, and unsupported-inference tracking while preserving reproducibility and auditability.

The design keeps `AgentMessage` separate from `AgentAssessment`. `AgentMessage` remains a communication envelope for orchestration, while `AgentAssessment` is the structured domain output.

The current domain taxonomy and concept mappings are intentionally small. Expanding them requires explicit code, tests, examples, and documentation updates.

Phase 6 does not decide final interpretation, reconcile agents, introduce outside context, recommend policy, or render research reports. Those capabilities remain deferred until coordination, retrieval/context, causal identification, and synthesis phases define their contracts.

## Alternatives considered

Force assessments into `AgentMessage`: rejected because the existing message schema is an orchestration envelope with recipients and communication payloads, not a compact domain assessment artifact.

Let agents inspect raw data or Phase 4 results directly: rejected because Phase 5 already supplies the bounded evidence and claim layer with limitation propagation and stable IDs.

Use LLM classification or embeddings for domain relevance: rejected because Phase 6 must be deterministic, testable, local, and auditable.

Assign exclusive ownership of evidence to one domain: rejected because many social indicators are cross-domain and should be independently assessable by multiple agents.

Introduce a coordinator now: rejected because this phase only defines independent domain assessments. Interdisciplinary synthesis belongs to a later phase.
