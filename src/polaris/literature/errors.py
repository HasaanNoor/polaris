"""Errors for corpus-grounded literature retrieval."""


class LiteratureError(Exception):
    """Base error for literature retrieval failures."""


class LiteratureIngestionError(LiteratureError):
    """Raised when a local literature source cannot be ingested."""


class LiteratureRetrievalError(LiteratureError):
    """Raised when retrieval cannot be completed."""
