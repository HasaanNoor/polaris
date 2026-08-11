"""Errors for WGI governance panel integration."""


class WGIError(Exception):
    """Base error for WGI integration."""


class WGISourceValidationError(WGIError):
    """Raised when an official WGI source snapshot cannot be validated."""


class WGISchemaError(WGIError):
    """Raised when a WGI snapshot does not expose the expected source schema."""


class WGIMappingError(WGIError):
    """Raised when a WGI source indicator cannot be mapped deterministically."""
