# ADR-012: Structured Research Report Generation

## Status

Accepted.

## Context

Phases 3 through 8 produce validated Polaris artifacts: ingested dataset state, deterministic statistical results, structured evidence and bounded claim candidates, deterministic domain assessments, coordinated cross-domain structure, and guardrailed synthesis. Polaris now needs a human-reviewable report layer that packages these artifacts without changing their meaning.

Report generation is separate from synthesis because Phase 8 explains a coordinated assessment in grounded language, while Phase 9 organizes that explanation and its upstream evidence into a stable report with sections, provenance, and export formats. Combining these concerns would make it harder to verify whether prose generation, source references, or presentation code introduced unsupported claims.

## Decision

Phase 9 adds a deterministic `polaris.reporting` package that consumes explicit Phase 3-8 artifacts and optional Phase 1 metadata. It validates that all inputs share one analytical lineage before building a frozen `ResearchReport`.

The report remains typed internally. Sections cover the research question, dataset and source metadata, methodology, statistical results, evidence and claims, domain assessments, cross-domain structure, Phase 8 synthesis, limitations, evidence and domain gaps, unsupported inferences, provenance, and an internal reference index.

No new reasoning occurs in Phase 9. The report does not rerun statistics, extract evidence, create claims, rerun agents, call a provider, retrieve outside facts, or build an external bibliography. Numerical results are copied from Phase 4 structures. Claims and evidence links are copied from Phase 5. Domain and cross-domain records are copied from Phases 6-8.

Markdown and standalone HTML are supported first because they are reviewable, deterministic, dependency-light, easy to snapshot in tests, and sufficient for early report inspection. JSON serialization is supported through the structured model.

PDF, DOCX, LaTeX, publication templates, and journal-specific formatting are deferred. They can consume `ResearchReport` later without redesigning report construction.

External bibliography generation is deferred because Phase 9 has no external retrieval boundary. The reference index is an internal analytical reference system for Polaris IDs, not a citation manager.

Provenance and internal references are mandatory. Limitations and unsupported-inference boundaries cannot be omitted because the report is a presentation layer over bounded evidence, not an opportunity to strengthen interpretation.

## Consequences

Report generation is reproducible and network-free. Identical source artifacts and deterministic title metadata produce stable report IDs. Rendering can evolve independently from report construction.

The report may be conservative or sparse when upstream artifacts are sparse. Missing research-question metadata, absent domains, empty gap lists, or deterministic fallback synthesis are represented explicitly rather than filled in.

Later retrieval-grounded literature integration can be added as a separate upstream artifact or section source. Phase 9 prepares for that by keeping report sections typed and references explicit.

## Alternatives considered

Using Phase 8 synthesis text as the whole report was rejected because it would collapse structured evidence, limitations, provenance, and references into prose.

Generating reports through an LLM was rejected for Phase 9 because it would blur the boundary between synthesis and presentation and increase fabricated-reference risk.

Adding PDF, DOCX, or LaTeX immediately was rejected because the current need is deterministic structured packaging, and those formats add dependencies or layout workflows before the internal contract is stable.

Creating an external bibliography was rejected because external retrieval and literature review remain deferred.
