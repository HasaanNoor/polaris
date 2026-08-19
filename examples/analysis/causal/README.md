# Phase 22 Causal Examples

The Phase 22 demonstration is synthetic. The repository does not contain reviewed real-world treatment metadata with defensible intervention dates and comparison groups, so Polaris does not invent policy timing.

The synthetic tests under `tests/analysis/causal` demonstrate:

- clean parallel-trends DiD with known positive ATT
- zero treatment effect
- violated pre-trends
- anticipation/post-treatment-control cautions
- unbalanced and missing pre-period rejection
- invalid treatment switching and unsupported staggered adoption rejection
- deterministic event-time and reference-period handling
