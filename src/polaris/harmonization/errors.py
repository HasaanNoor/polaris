"""Errors raised by deterministic country-year harmonization."""


class HarmonizationError(ValueError):
    """Base class for harmonization request and execution failures."""


class HarmonizationRequestError(HarmonizationError):
    """Raised when a harmonization request is internally inconsistent."""


class HarmonizationCompatibilityError(HarmonizationError):
    """Raised when requested variables cannot be harmonized safely."""
