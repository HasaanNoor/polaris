"""Optional embedding abstraction placeholder for Phase 14.

The default Polaris literature path does not use embeddings. This protocol exists only
so future provider-backed embedding retrieval can be added without making external
network providers mandatory.
"""

from typing import Protocol


class EmbeddingProvider(Protocol):
    provider_name: str

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        """Return embeddings for supplied texts using explicitly configured infrastructure."""
