"""Deterministic JSON serialization helpers for MCP responses."""

from __future__ import annotations

import json
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def json_compatible(value: Any) -> Any:
    """Return JSON-compatible data without NumPy/Python repr leakage."""

    if isinstance(value, BaseModel):
        return json_compatible(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {
            str(key): json_compatible(inner)
            for key, inner in sorted(value.items(), key=lambda item: str(item[0]))
            if not _secret_key(str(key))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_compatible(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return None
        return value
    if hasattr(value, "item"):
        return json_compatible(value.item())
    return value


def deterministic_json(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(
        json_compatible(value),
        sort_keys=True,
        separators=None if indent else (",", ":"),
        indent=indent,
        allow_nan=False,
    )


def bounded_payload(value: Any, *, max_bytes: int) -> dict[str, Any]:
    payload = json_compatible(value)
    encoded = deterministic_json(payload)
    if len(encoded.encode("utf-8")) <= max_bytes:
        return {"truncated": False, "data": payload}
    return {
        "truncated": True,
        "max_bytes": max_bytes,
        "summary": _summary(payload),
    }


def _summary(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            "keys": sorted(value)[:50],
            "key_count": len(value),
            **{
                key: value[key]
                for key in ("artifact_id", "project_id", "report_id")
                if key in value
            },
        }
    if isinstance(value, list):
        return {"item_count": len(value), "first_items": value[:5]}
    return str(value)[:500]


def _secret_key(key: str) -> bool:
    lowered = key.casefold()
    return any(token in lowered for token in ("secret", "api_key", "apikey", "token", "password"))
