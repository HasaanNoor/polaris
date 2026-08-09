"""Phase 14 corpus-grounded literature retrieval."""

from polaris.literature.ingestion import corpus_manifest, ingest_literature_corpus
from polaris.literature.matching import (
    build_claim_literature_queries,
    build_claim_literature_query,
)
from polaris.literature.models import (
    ChunkingConfig,
    CitationMetadata,
    ClaimLiteratureQuery,
    CorpusManifest,
    LiteratureChunk,
    LiteratureContextArtifact,
    LiteratureDocument,
    LiteratureEvidence,
    LiteratureProjectConfig,
    LiteratureSourceType,
    LiteratureSupportClassification,
    RetrievalMode,
    RetrievalQualitySummary,
    RetrievalRequest,
    RetrievalResult,
)
from polaris.literature.retrieval import retrieve_literature
from polaris.literature.service import build_literature_context

__all__ = [
    "ChunkingConfig",
    "CitationMetadata",
    "ClaimLiteratureQuery",
    "CorpusManifest",
    "LiteratureChunk",
    "LiteratureContextArtifact",
    "LiteratureDocument",
    "LiteratureEvidence",
    "LiteratureProjectConfig",
    "LiteratureSourceType",
    "LiteratureSupportClassification",
    "RetrievalMode",
    "RetrievalQualitySummary",
    "RetrievalRequest",
    "RetrievalResult",
    "build_claim_literature_queries",
    "build_claim_literature_query",
    "build_literature_context",
    "corpus_manifest",
    "ingest_literature_corpus",
    "retrieve_literature",
]
