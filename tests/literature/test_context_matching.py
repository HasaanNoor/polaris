from polaris.literature import build_claim_literature_queries, build_literature_context


def test_query_construction_uses_claim_variables(regression_evidence):
    queries = build_claim_literature_queries(evidence_artifact=regression_evidence)
    assert queries
    assert any("x" in query.query and "y" in query.query for query in queries)
    assert all(query.query for query in queries)


def test_literature_context_preserves_claims_and_citations(regression_evidence, literature_corpus):
    context = build_literature_context(
        evidence_artifact=regression_evidence,
        corpus=literature_corpus,
        top_k=2,
    )
    assert context.literature_context_id.startswith("literature_context_")
    assert context.empirical_claim_ids == tuple(
        claim.claim_id for claim in regression_evidence.claim_candidates
    )
    assert context.retrieval_summary.corpus_document_count == 3
    for record in context.literature_evidence:
        for citation in record.citations:
            assert citation.document_id or citation.title
            assert citation.citation_text or citation.title or citation.source_path
        assert record.support_classification.value == "unclassified"


def test_literature_context_id_excludes_timestamp(regression_evidence, literature_corpus):
    first = build_literature_context(
        evidence_artifact=regression_evidence,
        corpus=literature_corpus,
    )
    second = build_literature_context(
        evidence_artifact=regression_evidence,
        corpus=literature_corpus,
    )
    assert first.literature_context_id == second.literature_context_id
