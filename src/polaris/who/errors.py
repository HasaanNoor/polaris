"""WHO GHO integration errors."""

from __future__ import annotations


class WHOIntegrationError(Exception):
    """Base error for curated WHO integration."""


class WHOCatalogError(WHOIntegrationError):
    """Raised when the WHO acquisition catalog is missing or invalid."""


class WHOChecksumError(WHOIntegrationError):
    """Raised when a local WHO snapshot checksum does not match the catalog."""


class WHOMappingError(WHOIntegrationError):
    """Raised when a reviewed WHO mapping is unavailable or invalid."""


class WHOIndicatorDeferredError(WHOIntegrationError):
    """Raised when an indicator cannot be promoted into the default panel."""
