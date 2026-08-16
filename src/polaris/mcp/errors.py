"""MCP-safe error translation."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError


class PolarisMCPError(Exception):
    """Base exception whose payload is safe to return to MCP clients."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "polaris_mcp_error",
        category: str = "request_error",
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.category = category
        self.stage = stage
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": {
                "code": self.code,
                "category": self.category,
                "message": str(self),
            }
        }
        if self.stage is not None:
            payload["error"]["stage"] = self.stage
        if self.details:
            payload["error"]["details"] = self.details
        return payload


class MCPValidationError(PolarisMCPError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code="validation_error",
            category="validation",
            details=details,
        )


class MCPNotFoundError(PolarisMCPError):
    def __init__(self, message: str, *, code: str = "not_found") -> None:
        super().__init__(message, code=code, category="not_found")


class MCPSafetyError(PolarisMCPError):
    def __init__(self, message: str, *, code: str = "safety_boundary_violation") -> None:
        super().__init__(message, code=code, category="safety")


class MCPExecutionError(PolarisMCPError):
    def __init__(self, message: str, *, stage: str | None = None) -> None:
        super().__init__(message, code="execution_failed", category="execution", stage=stage)


def translate_exception(exc: Exception, *, stage: str | None = None) -> PolarisMCPError:
    if isinstance(exc, PolarisMCPError):
        return exc
    if isinstance(exc, ValidationError):
        return MCPValidationError(
            "request payload failed validation",
            details={"errors": exc.errors(include_url=False)},
        )
    return MCPExecutionError(str(exc) or type(exc).__name__, stage=stage)
