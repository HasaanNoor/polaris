"""Typed contracts for Phase 14 literature context and retrieval."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator

from polaris.schemas.common import AwareDatetime, FrozenPolarisBaseModel, NonEmptyStr, SchemaVersion

LITERATURE_SCHEMA_VERSION = "1.0.0"
LITERATURE_INDEX_VERSION = "lexical_bm25_phase14_v1"


class LiteratureSourceType(StrEnum):
    TXT = "txt"
    MARKDOWN = "markdown"
    JSON = "json"


class RetrievalMode(StrEnum):
    BM25 = "bm25"


class LiteratureSupportClassification(StrEnum):
    SUPPORTING = "supporting"
    CONTRASTING = "contrasting"
    CONTEXTUAL = "contextual"
    INSUFFICIENT = "insufficient"
    UNCLASSIFIED = "unclassified"


class CitationMetadata(FrozenPolarisBaseModel):
    title: NonEmptyStr | None = None
    authors: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    year: int | None = Field(default=None, ge=0)
    publication: NonEmptyStr | None = None
    doi: NonEmptyStr | None = None
    url: NonEmptyStr | None = None
    citation_text: NonEmptyStr | None = None
    document_id: NonEmptyStr | None = None
    source_path: str | None = None

    @field_validator("authors")
    @classmethod
    def normalize_authors(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(author.strip() for author in value if author.strip()))

    @model_validator(mode="after")
    def require_citable_identity(self) -> "CitationMetadata":
        if not (
            self.citation_text
            or self.title
            or self.doi
            or self.url
            or self.document_id
            or self.source_path
        ):
            raise ValueError("citation metadata must include at least one source identifier")
        return self


class LiteratureDocument(FrozenPolarisBaseModel):
    document_id: NonEmptyStr
    title: NonEmptyStr | None = None
    authors: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    year: int | None = Field(default=None, ge=0)
    publication: NonEmptyStr | None = None
    doi: NonEmptyStr | None = None
    url: NonEmptyStr | None = None
    citation_text: NonEmptyStr | None = None
    abstract: str | None = None
    full_text: NonEmptyStr | None = None
    text_source_reference: str | None = None
    source_type: LiteratureSourceType
    license: NonEmptyStr | None = None
    checksum_sha256: NonEmptyStr
    import_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    local_source_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: SchemaVersion = LITERATURE_SCHEMA_VERSION

    @field_validator("authors")
    @classmethod
    def dedupe_authors(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(author.strip() for author in value if author.strip()))

    @model_validator(mode="after")
    def require_text(self) -> "LiteratureDocument":
        if not self.full_text and not self.abstract:
            raise ValueError("literature document requires abstract or full_text")
        return self

    @property
    def citation_metadata(self) -> CitationMetadata:
        return CitationMetadata(
            title=self.title,
            authors=self.authors,
            year=self.year,
            publication=self.publication,
            doi=self.doi,
            url=self.url,
            citation_text=self.citation_text,
            document_id=self.document_id,
            source_path=self.local_source_path,
        )


class ChunkingConfig(FrozenPolarisBaseModel):
    max_characters: int = Field(default=900, ge=100)
    overlap_characters: int = Field(default=120, ge=0)
    preserve_headings: bool = True

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingConfig":
        if self.overlap_characters >= self.max_characters:
            raise ValueError("overlap_characters must be smaller than max_characters")
        return self


class LiteratureChunk(FrozenPolarisBaseModel):
    chunk_id: NonEmptyStr
    document_id: NonEmptyStr
    chunk_sequence: int = Field(ge=0)
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    section_heading: NonEmptyStr | None = None
    text: NonEmptyStr
    citation: CitationMetadata
    checksum_sha256: NonEmptyStr
    schema_version: SchemaVersion = LITERATURE_SCHEMA_VERSION


class CorpusIngestionFinding(FrozenPolarisBaseModel):
    code: NonEmptyStr
    message: NonEmptyStr
    document_id: NonEmptyStr | None = None
    source_path: str | None = None


class LiteratureCorpus(FrozenPolarisBaseModel):
    corpus_id: NonEmptyStr
    documents: tuple[LiteratureDocument, ...]
    chunks: tuple[LiteratureChunk, ...]
    chunking_config: ChunkingConfig
    ingestion_findings: tuple[CorpusIngestionFinding, ...] = Field(default_factory=tuple)
    corpus_checksum_sha256: NonEmptyStr
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: SchemaVersion = LITERATURE_SCHEMA_VERSION

    @field_validator("documents")
    @classmethod
    def sort_documents(
        cls, value: tuple[LiteratureDocument, ...]
    ) -> tuple[LiteratureDocument, ...]:
        ids = [document.document_id for document in value]
        if len(ids) != len(set(ids)):
            raise ValueError("document IDs must be unique")
        return tuple(sorted(value, key=lambda document: document.document_id))

    @field_validator("chunks")
    @classmethod
    def sort_chunks(cls, value: tuple[LiteratureChunk, ...]) -> tuple[LiteratureChunk, ...]:
        ids = [chunk.chunk_id for chunk in value]
        if len(ids) != len(set(ids)):
            raise ValueError("chunk IDs must be unique")
        return tuple(sorted(value, key=lambda chunk: (chunk.document_id, chunk.chunk_sequence)))


class CorpusManifest(FrozenPolarisBaseModel):
    corpus_id: NonEmptyStr
    document_ids: tuple[NonEmptyStr, ...]
    checksums: dict[str, str]
    source_paths: dict[str, str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingestion_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    chunking_config: ChunkingConfig
    index_config: dict[str, Any] = Field(default_factory=dict)
    schema_version: SchemaVersion = LITERATURE_SCHEMA_VERSION


class RetrievalRequest(FrozenPolarisBaseModel):
    query: NonEmptyStr
    corpus_id: NonEmptyStr
    top_k: int = Field(default=5, ge=1)
    year_range: tuple[int, int] | None = None
    domain_filters: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    publication_filters: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    document_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    retrieval_mode: RetrievalMode = RetrievalMode.BM25
    minimum_score: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_year_range(self) -> "RetrievalRequest":
        if self.year_range is not None and self.year_range[0] > self.year_range[1]:
            raise ValueError("year_range start must be <= end")
        return self

    @field_validator("domain_filters", "publication_filters", "document_ids")
    @classmethod
    def sort_filters(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(value)))


class RankedLiteratureChunk(FrozenPolarisBaseModel):
    chunk: LiteratureChunk
    document: LiteratureDocument
    score: float
    rank: int = Field(ge=1)
    matched_terms: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class RetrievalFinding(FrozenPolarisBaseModel):
    code: NonEmptyStr
    message: NonEmptyStr


class RetrievalResult(FrozenPolarisBaseModel):
    query: NonEmptyStr
    ranked_chunks: tuple[RankedLiteratureChunk, ...]
    retrieval_mode: RetrievalMode
    index_version: NonEmptyStr = LITERATURE_INDEX_VERSION
    corpus_id: NonEmptyStr
    corpus_checksum_sha256: NonEmptyStr
    findings: tuple[RetrievalFinding, ...] = Field(default_factory=tuple)
    retrieval_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))


class ClaimLiteratureQuery(FrozenPolarisBaseModel):
    empirical_claim_id: NonEmptyStr
    query: NonEmptyStr
    variable_terms: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    method_terms: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    domain_terms: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class LiteratureEvidence(FrozenPolarisBaseModel):
    literature_evidence_id: NonEmptyStr
    empirical_claim_id: NonEmptyStr
    retrieval_query: NonEmptyStr
    ranked_chunks: tuple[RankedLiteratureChunk, ...]
    citations: tuple[CitationMetadata, ...]
    relevance_scores: tuple[float, ...]
    support_classification: LiteratureSupportClassification = (
        LiteratureSupportClassification.UNCLASSIFIED
    )
    limitations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    provenance: dict[str, Any] = Field(default_factory=dict)


class RetrievalQualitySummary(FrozenPolarisBaseModel):
    corpus_document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    query_count: int = Field(ge=0)
    retrieved_chunk_count: int = Field(ge=0)
    unique_cited_documents: int = Field(ge=0)
    unmatched_claims: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    duplicate_citations: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    year_coverage: tuple[int, int] | None = None
    retrieval_mode: RetrievalMode
    score_distribution: dict[str, float | None] = Field(default_factory=dict)
    unsupported_queries: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class LiteratureContextArtifact(FrozenPolarisBaseModel):
    literature_context_id: NonEmptyStr
    corpus_id: NonEmptyStr
    project_id: NonEmptyStr | None = None
    research_question: str | None = None
    empirical_claim_ids: tuple[NonEmptyStr, ...]
    literature_evidence: tuple[LiteratureEvidence, ...]
    unmatched_claims: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    retrieval_summary: RetrievalQualitySummary
    provenance: dict[str, Any] = Field(default_factory=dict)
    schema_version: SchemaVersion = LITERATURE_SCHEMA_VERSION


class LiteratureProjectConfig(FrozenPolarisBaseModel):
    corpus_path: Path
    manifest_path: Path | None = None
    top_k: int = Field(default=5, ge=1)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval_mode: RetrievalMode = RetrievalMode.BM25
