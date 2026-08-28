# Phase 24 Robustness Example

The current Phase 23 causal-study registry contains templates and draft or blocked studies, so
Polaris does not execute a real causal case study from those definitions.

Deterministic synthetic examples live in `tests/analysis/robustness/test_phase24_robustness.py`.
They cover stable effects, control-group sensitivity, time-window sensitivity, leave-one-out
checks, placebo diagnostics, event-study windows, failed variants, evidence extraction, reasoning,
reporting, project orchestration, and MCP.

```text
Reviewed CausalStudyDefinition
DesignReadinessAssessment
CausalSpecification
Phase 22 DiD/event-study result
RobustnessSpecification
RobustnessAnalysisResult
Phase 5 evidence
Phase 18 reasoning
Phase 9 report
```

Robustness checks characterize sensitivity. They do not prove causality.
