"""High-level Phase 14 literature context API."""

from collections import Counter
from datetime import UTC, datetime

from polaris.evidence.models import EvidenceArtifact
from polaris.literature.matching import build_claim_literature_queries
from polaris.literature.models import (
    LiteratureContextArtifact,
    LiteratureCorpus,
    LiteratureEvidence,
    RetrievalMode,
    RetrievalQualitySummary,
    RetrievalRequest,
)
from polaris.literature.provenance import deterministic_literature_id
from polaris.literature.retrieval import retrieve_literature
from polaris.schemas.research_question import ResearchQuestion


def build_literature_context(
    *,
    evidence_artifact: EvidenceArtifact,
    corpus: LiteratureCorpus,
    research_question: ResearchQuestion | None = None,
    project_id: str | None = None,
    top_k: int = 5,
    retrieval_mode: RetrievalMode = RetrievalMode.BM25,
    retrieval_timestamp: datetime | None = None,
) -> LiteratureContextArtifact:
    """Retrieve local literature for Phase 5 empirical claims without altering them."""

    timestamp = retrieval_timestamp or datetime.now(UTC)
    queries = build_claim_literature_queries(
        evidence_artifact=evidence_artifact,
        research_question=research_question,
    )
    evidence_records: list[LiteratureEvidence] = []
    unmatched: list[str] = []
    unsupported: list[str] = []
    for query in queries:
        if not query.query.strip():
            unsupported.append(query.empirical_claim_id)
            unmatched.append(query.empirical_claim_id)
            continue
        result = retrieve_literature(
            corpus=corpus,
            request=RetrievalRequest(
                query=query.query,
                corpus_id=corpus.corpus_id,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
            ),
            retrieval_timestamp=timestamp,
        )
        if not result.ranked_chunks:
            unmatched.append(query.empirical_claim_id)
        citations = tuple(row.chunk.citation for row in result.ranked_chunks)
        evidence_records.append(
            LiteratureEvidence(
                literature_evidence_id=deterministic_literature_id(
                    "lit_evidence_",
                    {
                        "claim_id": query.empirical_claim_id,
                        "query": query.query,
                        "chunk_ids": [row.chunk.chunk_id for row in result.ranked_chunks],
                        "corpus_id": corpus.corpus_id,
                    },
                ),
                empirical_claim_id=query.empirical_claim_id,
                retrieval_query=query.query,
                ranked_chunks=result.ranked_chunks,
                citations=citations,
                relevance_scores=tuple(row.score for row in result.ranked_chunks),
                limitations=(
                    "Retrieval relevance is lexical and does not establish scientific agreement.",
                    "Literature context is separate from Polaris empirical evidence.",
                ),
                provenance={
                    "corpus_id": corpus.corpus_id,
                    "corpus_checksum_sha256": corpus.corpus_checksum_sha256,
                    "retrieval_mode": retrieval_mode.value,
                    "retrieval_timestamp": timestamp.isoformat(),
                },
            )
        )
    claim_ids = tuple(claim.claim_id for claim in evidence_artifact.claim_candidates)
    summary = _quality_summary(
        corpus=corpus,
        evidence_records=tuple(evidence_records),
        query_count=len(queries),
        unmatched_claims=tuple(unmatched),
        retrieval_mode=retrieval_mode,
        unsupported_queries=tuple(unsupported),
    )
    return LiteratureContextArtifact(
        literature_context_id=deterministic_literature_id(
            "literature_context_",
            {
                "corpus_id": corpus.corpus_id,
                "project_id": project_id,
                "research_question": research_question.raw_text if research_question else None,
                "empirical_claim_ids": claim_ids,
                "literature_evidence_ids": [
                    item.literature_evidence_id for item in evidence_records
                ],
                "schema_version": "1.0.0",
            },
        ),
        corpus_id=corpus.corpus_id,
        project_id=project_id,
        research_question=research_question.raw_text if research_question else None,
        empirical_claim_ids=claim_ids,
        literature_evidence=tuple(evidence_records),
        unmatched_claims=tuple(unmatched),
        retrieval_summary=summary,
        provenance={
            "source_evidence_artifact_id": evidence_artifact.artifact_id,
            "source_analysis_result_id": evidence_artifact.source_analysis_result_id,
            "dataset_id": evidence_artifact.dataset_id,
            "retrieval_timestamp": timestamp.isoformat(),
        },
    )


def _quality_summary(
    *,
    corpus: LiteratureCorpus,
    evidence_records: tuple[LiteratureEvidence, ...],
    query_count: int,
    unmatched_claims: tuple[str, ...],
    retrieval_mode: RetrievalMode,
    unsupported_queries: tuple[str, ...],
) -> RetrievalQualitySummary:
    scores = [score for record in evidence_records for score in record.relevance_scores]
    cited_docs = [
        citation.document_id or citation.source_path or citation.title or ""
        for record in evidence_records
        for citation in record.citations
    ]
    counts = Counter(item for item in cited_docs if item)
    years = sorted(document.year for document in corpus.documents if document.year is not None)
    return RetrievalQualitySummary(
        corpus_document_count=len(corpus.documents),
        chunk_count=len(corpus.chunks),
        query_count=query_count,
        retrieved_chunk_count=sum(len(record.ranked_chunks) for record in evidence_records),
        unique_cited_documents=len(set(cited_docs)),
        unmatched_claims=unmatched_claims,
        duplicate_citations=tuple(sorted(item for item, count in counts.items() if count > 1)),
        year_coverage=(years[0], years[-1]) if years else None,
        retrieval_mode=retrieval_mode,
        score_distribution={
            "minimum": min(scores) if scores else None,
            "maximum": max(scores) if scores else None,
            "mean": sum(scores) / len(scores) if scores else None,
        },
        unsupported_queries=unsupported_queries,
    )
