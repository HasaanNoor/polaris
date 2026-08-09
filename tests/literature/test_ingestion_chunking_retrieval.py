import pytest

from polaris.literature import retrieve_literature
from polaris.literature.chunking import chunk_document
from polaris.literature.ingestion import ingest_literature_corpus
from polaris.literature.models import ChunkingConfig, RetrievalRequest


def test_ingests_txt_markdown_json_and_preserves_metadata(literature_corpus):
    assert len(literature_corpus.documents) == 3
    assert len(literature_corpus.chunks) >= 3
    structured = next(
        doc for doc in literature_corpus.documents if doc.document_id == "structured_income_health"
    )
    assert structured.doi == "10.0000/test"
    assert structured.url == "https://example.test/literature"
    assert structured.checksum_sha256


def test_duplicate_document_detection(literature_dir):
    (literature_dir / "duplicate.json").write_text(
        '{"document_id":"structured_income_health","full_text":"duplicate"}',
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="duplicate"):
        ingest_literature_corpus(literature_dir, manifest_path=literature_dir / "manifest.json")


def test_chunking_is_deterministic_and_preserves_heading(literature_corpus):
    document = next(
        doc for doc in literature_corpus.documents if doc.document_id == "income_health_note"
    )
    chunks = chunk_document(
        document,
        config=ChunkingConfig(max_characters=140, overlap_characters=20),
    )
    repeated = chunk_document(
        document,
        config=ChunkingConfig(max_characters=140, overlap_characters=20),
    )
    assert [chunk.chunk_id for chunk in chunks] == [chunk.chunk_id for chunk in repeated]
    assert chunks[0].section_heading == "Income and Health"
    assert chunks[0].start_offset == 0


def test_retrieval_ranks_relevant_chunks_and_is_stable(literature_corpus):
    request = RetrievalRequest(
        query="GDP per capita life expectancy",
        corpus_id=literature_corpus.corpus_id,
        top_k=2,
    )
    first = retrieve_literature(corpus=literature_corpus, request=request)
    second = retrieve_literature(corpus=literature_corpus, request=request)
    assert [row.chunk.chunk_id for row in first.ranked_chunks] == [
        row.chunk.chunk_id for row in second.ranked_chunks
    ]
    assert len(first.ranked_chunks) == 2
    assert first.ranked_chunks[0].score >= first.ranked_chunks[1].score


def test_retrieval_filters_and_no_matches(literature_corpus):
    filtered = retrieve_literature(
        corpus=literature_corpus,
        request=RetrievalRequest(
            query="GDP life expectancy",
            corpus_id=literature_corpus.corpus_id,
            document_ids=("education_health_note",),
        ),
    )
    assert not filtered.ranked_chunks
    assert filtered.findings[0].code == "no_matches"
