"""Deterministic lexical retrieval index."""

import math
import re
from collections import Counter

from polaris.literature.models import (
    LiteratureCorpus,
    LiteratureDocument,
    RankedLiteratureChunk,
    RetrievalRequest,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class LexicalLiteratureIndex:
    """Small deterministic BM25-style index over local literature chunks."""

    def __init__(self, corpus: LiteratureCorpus) -> None:
        self.corpus = corpus
        self.documents_by_id: dict[str, LiteratureDocument] = {
            document.document_id: document for document in corpus.documents
        }
        self._chunk_terms = [Counter(tokenize(chunk.text)) for chunk in corpus.chunks]
        self._doc_freq = Counter(token for terms in self._chunk_terms for token in set(terms))
        self._lengths = [sum(terms.values()) for terms in self._chunk_terms]
        self._avgdl = sum(self._lengths) / len(self._lengths) if self._lengths else 0.0

    def search(self, request: RetrievalRequest) -> tuple[RankedLiteratureChunk, ...]:
        query_terms = tokenize(request.query)
        if not query_terms:
            return ()
        rows: list[RankedLiteratureChunk] = []
        for index, chunk in enumerate(self.corpus.chunks):
            document = self.documents_by_id[chunk.document_id]
            if not _passes_filters(document, request):
                continue
            score = self._score(index, query_terms)
            if request.minimum_score is not None and score < request.minimum_score:
                continue
            if score <= 0:
                continue
            matched = tuple(sorted(set(query_terms) & set(self._chunk_terms[index])))
            rows.append(
                RankedLiteratureChunk(
                    chunk=chunk,
                    document=document,
                    score=round(score, 10),
                    rank=1,
                    matched_terms=matched,
                )
            )
        rows.sort(
            key=lambda item: (
                -item.score,
                item.document.document_id,
                item.chunk.chunk_sequence,
                item.chunk.chunk_id,
            )
        )
        return tuple(
            item.model_copy(update={"rank": rank})
            for rank, item in enumerate(rows[: request.top_k], start=1)
        )

    def _score(self, chunk_index: int, query_terms: tuple[str, ...]) -> float:
        terms = self._chunk_terms[chunk_index]
        length = self._lengths[chunk_index] or 1
        total = len(self.corpus.chunks) or 1
        k1 = 1.5
        b = 0.75
        score = 0.0
        for term in query_terms:
            freq = terms.get(term, 0)
            if freq == 0:
                continue
            df = self._doc_freq.get(term, 0)
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            denom = freq + k1 * (1 - b + b * (length / (self._avgdl or 1)))
            score += idf * ((freq * (k1 + 1)) / denom)
        return score


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.lower()))


def _passes_filters(document: LiteratureDocument, request: RetrievalRequest) -> bool:
    if request.document_ids and document.document_id not in request.document_ids:
        return False
    if request.year_range is not None:
        if document.year is None:
            return False
        start, end = request.year_range
        if not start <= document.year <= end:
            return False
    if request.publication_filters:
        publication = (document.publication or "").lower()
        if publication not in {item.lower() for item in request.publication_filters}:
            return False
    if request.domain_filters:
        domain = str(document.metadata.get("domain", "")).lower()
        domains = {str(item).lower() for item in document.metadata.get("domains", ())}
        if not ({domain, *domains} & {item.lower() for item in request.domain_filters}):
            return False
    return True
