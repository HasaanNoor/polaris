# ADR-017: Literature Context and Retrieval

## Status

Accepted.

## Context

Polaris produces empirical findings from explicit datasets, specifications, evidence extraction, domain assessment, coordination, synthesis, and reporting. Those findings often need context from existing research, but external literature must not replace the empirical artifact chain or be invented from model memory.

## Decision

Phase 14 adds a local, deterministic literature retrieval layer under `src/polaris/literature`. It ingests explicitly supplied TXT, Markdown, and structured JSON sources into frozen `LiteratureDocument`, `LiteratureChunk`, `CitationMetadata`, and `LiteratureCorpus` models. Corpus ingestion computes source checksums, normalizes text without mutating raw files, chunks deterministically, and preserves citation metadata on every retrieved chunk.

Retrieval runs after empirical evidence and coordination. Evidence-to-literature queries are constructed from Phase 5 claim variables, claim type, direction, statistical procedure, and optional research-question variable references. The default index is an in-process BM25-style lexical retriever with deterministic ordering by score, document ID, chunk sequence, and chunk ID. Retrieval results become `LiteratureEvidence` records and a `LiteratureContextArtifact`, not empirical evidence.

Phase 8 synthesis and Phase 9 reporting may receive an optional `LiteratureContextArtifact`. Synthesis prompt payloads separate empirical findings from literature context. Reports render a separate Literature Context section with cited local-corpus documents, unmatched claims, and retrieval limitations. Phase 13 can add `RETRIEVE_LITERATURE` only when `ResearchProjectRequest.literature` is supplied.

## Consequences

Empirical findings remain primary and unchanged. Literature retrieval is reproducible after corpus preparation and works offline. Citation metadata is mandatory where available and never fabricated. The system can contextualize claims against a curated corpus, but lexical relevance is not treated as scientific agreement or causal validation.

The baseline does not provide autonomous browsing, online academic search, vector databases, Elasticsearch, OCR, model-generated citations, or provider-backed summarization. Embeddings are deferred behind an optional protocol because they require a concrete provider and reproducibility policy.

## Alternatives considered

- Autonomous internet or academic API search: rejected because Phase 14 requires explicit corpus grounding and no autonomous paper selection.
- LLM-generated citations or literature summaries: rejected because citations must come from supplied metadata and claims must remain source-grounded.
- Vector databases or Elasticsearch: deferred because the current corpus scale is served by deterministic local lexical retrieval with no new infrastructure.
- Running literature retrieval before empirical analysis: rejected because literature must contextualize findings Polaris already produced, not steer statistical outputs.
