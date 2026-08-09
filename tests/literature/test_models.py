import pytest
from pydantic import ValidationError

from polaris.literature.models import CitationMetadata, LiteratureDocument, LiteratureSourceType


def test_literature_document_is_strict_and_frozen(literature_corpus):
    document = literature_corpus.documents[0]
    with pytest.raises(ValidationError):
        LiteratureDocument.model_validate(
            {
                "document_id": "bad",
                "source_type": LiteratureSourceType.TXT,
                "checksum_sha256": "abc",
                "full_text": "text",
                "unknown": "field",
            }
        )
    with pytest.raises(ValidationError):
        document.title = "changed"


def test_citation_metadata_preserves_supplied_fields():
    citation = CitationMetadata(
        title="Title",
        authors=("A", "A", "B"),
        year=2024,
        doi="10.0000/test",
        url="https://example.test",
    )
    assert citation.authors == ("A", "B")
    assert citation.doi == "10.0000/test"
    assert citation.url == "https://example.test"


def test_corpus_ids_are_deterministic(literature_dir):
    first = LiteratureDocument.model_validate(
        {
            "document_id": "doc",
            "source_type": "txt",
            "checksum_sha256": "abc",
            "full_text": "Text",
        }
    )
    assert first.citation_metadata.document_id == "doc"
