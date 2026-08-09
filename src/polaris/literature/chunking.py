"""Deterministic text normalization and chunking for literature documents."""

import re

from polaris.literature.models import ChunkingConfig, LiteratureChunk, LiteratureDocument
from polaris.literature.provenance import deterministic_literature_id, sha256_text

_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_PARAGRAPH_RE = re.compile(r"\n{2,}")


def normalize_text(text: str) -> str:
    """Normalize text without changing source files."""

    lines = [
        _WHITESPACE_RE.sub(" ", line).strip() for line in text.replace("\r\n", "\n").split("\n")
    ]
    compact = "\n".join(line for line in lines)
    return _PARAGRAPH_RE.sub("\n\n", compact).strip()


def chunk_document(
    document: LiteratureDocument,
    *,
    config: ChunkingConfig | None = None,
) -> tuple[LiteratureChunk, ...]:
    """Create stable paragraph-aware chunks for one document."""

    cfg = config or ChunkingConfig()
    text = normalize_text(
        "\n\n".join(part for part in (document.abstract, document.full_text) if part)
    )
    paragraphs = [paragraph for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[LiteratureChunk] = []
    current = ""
    current_start = 0
    offset = 0
    heading: str | None = None
    for paragraph in paragraphs:
        stripped = paragraph.strip()
        paragraph_start = text.find(stripped, offset)
        if _is_heading(stripped):
            heading = stripped.lstrip("#").strip()
        candidate = stripped if not current else f"{current}\n\n{stripped}"
        if current and len(candidate) > cfg.max_characters:
            chunks.append(_build_chunk(document, chunks, current, current_start, heading))
            overlap = current[-cfg.overlap_characters :] if cfg.overlap_characters else ""
            current = f"{overlap}\n\n{stripped}".strip() if overlap else stripped
            current_start = max(paragraph_start - len(overlap), 0)
        else:
            if not current:
                current_start = paragraph_start
            current = candidate
        offset = paragraph_start + len(stripped)
        while len(current) > cfg.max_characters:
            piece = current[: cfg.max_characters].strip()
            chunks.append(_build_chunk(document, chunks, piece, current_start, heading))
            overlap = piece[-cfg.overlap_characters :] if cfg.overlap_characters else ""
            current = f"{overlap}{current[cfg.max_characters :]}".strip()
            current_start += max(len(piece) - len(overlap), 0)
    if current:
        chunks.append(_build_chunk(document, chunks, current, current_start, heading))
    return tuple(chunks)


def _build_chunk(
    document: LiteratureDocument,
    chunks: list[LiteratureChunk],
    text: str,
    start_offset: int,
    heading: str | None,
) -> LiteratureChunk:
    sequence = len(chunks)
    checksum = sha256_text(text)
    return LiteratureChunk(
        chunk_id=deterministic_literature_id(
            "lit_chunk_",
            {
                "document_id": document.document_id,
                "sequence": sequence,
                "checksum": checksum,
            },
        ),
        document_id=document.document_id,
        chunk_sequence=sequence,
        start_offset=start_offset,
        end_offset=start_offset + len(text),
        section_heading=heading,
        text=text,
        citation=document.citation_metadata,
        checksum_sha256=checksum,
    )


def _is_heading(text: str) -> bool:
    return text.startswith("#") or (len(text) <= 80 and text.isupper())
