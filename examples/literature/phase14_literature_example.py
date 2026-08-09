"""Illustrative local literature retrieval example for Phase 14."""

from pathlib import Path

from polaris.literature import ingest_literature_corpus, retrieve_literature
from polaris.literature.models import RetrievalRequest


def main() -> None:
    corpus_dir = Path(__file__).parent / "corpus"
    corpus = ingest_literature_corpus(corpus_dir, manifest_path=corpus_dir / "manifest.json")
    result = retrieve_literature(
        corpus=corpus,
        request=RetrievalRequest(
            query="GDP per capita life expectancy association",
            corpus_id=corpus.corpus_id,
            top_k=3,
        ),
    )
    for row in result.ranked_chunks:
        print(row.rank, row.score, row.document.title, row.chunk.chunk_id)


if __name__ == "__main__":
    main()
