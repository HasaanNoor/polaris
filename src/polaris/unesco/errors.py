"""UNESCO education integration errors."""


class UNESCOEducationError(Exception):
    """Base error for UNESCO education panel integration."""


class UNESCOEducationSchemaError(UNESCOEducationError):
    """Raised when a local UNESCO file does not match the reviewed schema."""


class UNESCOEducationMappingError(UNESCOEducationError):
    """Raised for unknown or unsafe UNESCO education mappings."""
