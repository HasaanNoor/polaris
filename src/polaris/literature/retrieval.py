"""Public retrieval functions for local literature corpora."""

from datetime import UTC, datetime

from polaris.literature.errors import LiteratureRetrievalError
from polaris.literature.index import LexicalLiteratureIndex
from polaris.literature.models import (
    LiteratureCorpus,
    RetrievalFinding,
    RetrievalMode,
    RetrievalRequest,
    RetrievalResult,
)


def retrieve_literature(
    *,
    corpus: LiteratureCorpus,
    request: RetrievalRequest,
    retrieval_timestamp: datetime | None = None,
) -> RetrievalResult:
    if request.corpus_id != corpus.corpus_id:
        raise LiteratureRetrievalError("retrieval request corpus_id does not match corpus")
    if request.retrieval_mode is not RetrievalMode.BM25:
        raise LiteratureRetrievalError(f"unsupported retrieval mode: {request.retrieval_mode}")
    ranked = LexicalLiteratureIndex(corpus).search(request)
    findings = ()
    if not ranked:
        findings = (RetrievalFinding(code="no_matches", message="No chunks matched the query."),)
    return RetrievalResult(
        query=request.query,
        ranked_chunks=ranked,
        retrieval_mode=request.retrieval_mode,
        corpus_id=corpus.corpus_id,
        corpus_checksum_sha256=corpus.corpus_checksum_sha256,
        findings=findings,
        retrieval_timestamp=retrieval_timestamp or datetime.now(UTC),
    )
