# ADR-022: Reasoning Evaluation and Benchmarking

## Status

Accepted.

## Context

Phase 18 added deterministic and optional provider-backed evidence-grounded reasoning.
Polaris needs a reproducible way to evaluate whether reasoning artifacts remain grounded,
faithful to evidence, uncertain where appropriate, causally restrained, internally
consistent, contradiction-aware, structurally valid, and reproducible.

The evaluator must compare deterministic reasoning, provider-backed reasoning, and
deliberately flawed fixtures without turning the benchmark into a universal model ranking.

## Decision

Polaris adds a separate Phase 19 package, `polaris.evaluation`. Evaluation consumes Phase
5 evidence, Phase 7 coordination, optional Phase 14 literature context, and Phase 18
reasoning artifacts. It does not modify reasoning artifacts or upstream evidence.

The baseline evaluator is deterministic and rule-based. It reuses Phase 18 grounding
indexes and causal-language guardrails where possible. LLM-as-judge is not the baseline
because it would add nondeterminism, network dependence, model drift, and opaque grading.

Evaluation reports dimensions separately: grounding, evidence fidelity, causal restraint,
epistemic calibration, contradiction handling, limitation propagation, literature
separation, structural validity, and reproducibility. Polaris avoids a single opaque
quality score because one aggregate would hide distinct failure categories.

Adversarial fixtures are required. They test fabricated grounding, fabricated citations,
causal overclaims, contradiction omission, limitation loss, literature misuse, and
mechanism mislabeling. Deterministic and provider-backed reasoning are compared on the
same dimensions, which supports factual comparison such as one mode producing more
mechanisms or more grounding failures.

Benchmark reports are separate from research reports. Research output remains research
output; evaluation output is diagnostic. Regression benchmarks protect future reasoning
changes from causal, grounding, contradiction, limitation, and reproducibility regressions
without requiring exact prose equality except where deterministic identity is intentional.

## Consequences

- Default evaluation is reproducible and network-free.
- Provider-backed evaluation remains optional and can be tested with fake providers.
- Failure categories remain visible instead of being hidden behind a score.
- Future Phase 18 changes can be assessed against transparent structural expectations.
- Rule-based evaluation cannot fully measure scientific creativity, explanatory
  usefulness, mechanism truth, comprehensive confounder discovery, novel research-question
  quality, or domain-expert judgment.

## Alternatives Considered

- LLM-as-judge baseline: rejected for nondeterminism, network dependence, and opacity.
- Single aggregate score: rejected because it encourages leaderboard interpretation.
- Exact prose regression fixtures: rejected except for deterministic identity checks.
- Vector or external evaluation platforms: rejected as unnecessary for structured Phase 18
  artifacts and outside the offline baseline.
- Automatic Phase 13 evaluation stage by default: deferred to keep project execution and
  benchmark diagnostics separate.
