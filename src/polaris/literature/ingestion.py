"""Local corpus ingestion for Phase 14 literature retrieval."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from polaris.literature.chunking import chunk_document, normalize_text
from polaris.literature.errors import LiteratureIngestionError
from polaris.literature.models import (
    ChunkingConfig,
    CorpusIngestionFinding,
    CorpusManifest,
    LiteratureCorpus,
    LiteratureDocument,
    LiteratureSourceType,
)
from polaris.literature.provenance import deterministic_literature_id, sha256_file, sha256_text


def ingest_literature_corpus(
    corpus_path: Path | str,
    *,
    manifest_path: Path | str | None = None,
    chunking_config: ChunkingConfig | None = None,
    ingestion_timestamp: datetime | None = None,
) -> LiteratureCorpus:
    """Ingest local TXT, Markdown, and JSON sources into a deterministic corpus."""

    root = Path(corpus_path)
    if not root.exists() or not root.is_dir():
        raise LiteratureIngestionError(f"literature corpus directory does not exist: {root}")
    timestamp = ingestion_timestamp or datetime.now(UTC)
    cfg = chunking_config or ChunkingConfig()
    manifest = _load_manifest(Path(manifest_path)) if manifest_path is not None else {}
    documents: list[LiteratureDocument] = []
    findings: list[CorpusIngestionFinding] = []
    excluded = {Path(manifest_path).resolve()} if manifest_path is not None else set()
    for source in sorted(_iter_supported_sources(root)):
        if source.resolve() in excluded:
            continue
        try:
            document = _ingest_source(source, root=root, manifest=manifest, timestamp=timestamp)
            documents.append(document)
            findings.append(
                CorpusIngestionFinding(
                    code="document_ingested",
                    message="Literature source ingested from local corpus.",
                    document_id=document.document_id,
                    source_path=str(source),
                )
            )
        except LiteratureIngestionError as exc:
            raise exc
    ids = [document.document_id for document in documents]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        raise LiteratureIngestionError(f"duplicate literature document IDs: {duplicates}")
    chunks = tuple(
        chunk for document in documents for chunk in chunk_document(document, config=cfg)
    )
    if not documents:
        raise LiteratureIngestionError("literature corpus contains no supported documents")
    checksum_payload = {
        "documents": [
            {
                "document_id": document.document_id,
                "checksum": document.checksum_sha256,
                "source_path": document.local_source_path,
            }
            for document in sorted(documents, key=lambda item: item.document_id)
        ],
        "chunking": cfg.model_dump(mode="json"),
    }
    corpus_checksum = sha256_text(
        json.dumps(checksum_payload, sort_keys=True, separators=(",", ":"))
    )
    corpus_id = deterministic_literature_id(
        "literature_corpus_",
        {"corpus_checksum_sha256": corpus_checksum, "schema_version": "1.0.0"},
    )
    return LiteratureCorpus(
        corpus_id=corpus_id,
        documents=tuple(documents),
        chunks=chunks,
        chunking_config=cfg,
        ingestion_findings=tuple(findings),
        corpus_checksum_sha256=corpus_checksum,
        created_at=timestamp,
    )


def corpus_manifest(corpus: LiteratureCorpus) -> CorpusManifest:
    """Return a deterministic manifest object for an ingested corpus."""

    return CorpusManifest(
        corpus_id=corpus.corpus_id,
        document_ids=tuple(document.document_id for document in corpus.documents),
        checksums={document.document_id: document.checksum_sha256 for document in corpus.documents},
        source_paths={
            document.document_id: document.local_source_path or "" for document in corpus.documents
        },
        metadata={"corpus_checksum_sha256": corpus.corpus_checksum_sha256},
        ingestion_timestamp=corpus.created_at,
        chunking_config=corpus.chunking_config,
        index_config={"retrieval_mode": "bm25", "index_version": "lexical_bm25_phase14_v1"},
    )


def _iter_supported_sources(root: Path) -> tuple[Path, ...]:
    suffixes = {".txt", ".md", ".markdown", ".json"}
    return tuple(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise LiteratureIngestionError(f"failed to read corpus manifest: {path}") from exc
    if not isinstance(payload, dict):
        raise LiteratureIngestionError("corpus manifest must be a JSON object")
    documents = payload.get("documents", payload)
    if isinstance(documents, list):
        return {
            str(item.get("source_path") or item.get("path") or item.get("document_id")): item
            for item in documents
            if isinstance(item, dict)
        }
    if isinstance(documents, dict):
        return documents
    raise LiteratureIngestionError("corpus manifest documents must be an object or list")


def _ingest_source(
    source: Path,
    *,
    root: Path,
    manifest: dict[str, Any],
    timestamp: datetime,
) -> LiteratureDocument:
    suffix = source.suffix.lower()
    checksum = sha256_file(source)
    metadata = _metadata_for(source, root=root, manifest=manifest)
    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise LiteratureIngestionError(f"JSON literature source must be an object: {source}")
        metadata = {**metadata, **payload}
        text = str(payload.get("full_text") or payload.get("text") or "")
        abstract = payload.get("abstract")
        source_type = LiteratureSourceType.JSON
    else:
        text = source.read_text(encoding="utf-8")
        abstract = metadata.get("abstract")
        source_type = (
            LiteratureSourceType.MARKDOWN
            if suffix in {".md", ".markdown"}
            else LiteratureSourceType.TXT
        )
    normalized_text = normalize_text(text)
    if not normalized_text and not abstract:
        raise LiteratureIngestionError(f"literature source is empty after normalization: {source}")
    document_id = str(
        metadata.get("document_id")
        or deterministic_literature_id(
            "lit_doc_",
            {"relative_path": source.relative_to(root).as_posix(), "checksum": checksum},
        )
    )
    try:
        return LiteratureDocument(
            document_id=document_id,
            title=metadata.get("title"),
            authors=tuple(metadata.get("authors") or ()),
            year=metadata.get("year"),
            publication=metadata.get("publication"),
            doi=metadata.get("doi"),
            url=metadata.get("url"),
            citation_text=metadata.get("citation_text"),
            abstract=normalize_text(str(abstract)) if abstract else None,
            full_text=normalized_text or None,
            text_source_reference=metadata.get("text_source_reference"),
            source_type=source_type,
            license=metadata.get("license"),
            checksum_sha256=checksum,
            import_timestamp=timestamp,
            local_source_path=source.relative_to(root).as_posix(),
            metadata={
                str(key): value
                for key, value in metadata.items()
                if key
                not in {
                    "document_id",
                    "title",
                    "authors",
                    "year",
                    "publication",
                    "doi",
                    "url",
                    "citation_text",
                    "abstract",
                    "full_text",
                    "text",
                    "text_source_reference",
                    "license",
                }
            },
        )
    except ValidationError as exc:
        raise LiteratureIngestionError(f"invalid literature metadata for {source}") from exc


def _metadata_for(source: Path, *, root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    relative = source.relative_to(root).as_posix()
    candidates = (relative, source.name, source.stem)
    for key in candidates:
        value = manifest.get(key)
        if isinstance(value, dict):
            return dict(value)
    return {}
