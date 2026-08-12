"""Deterministic identifiers for UNESCO education panels."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from polaris.unesco.models import json_ready


def deterministic_unesco_panel_id(*, payload: dict[str, Any]) -> str:
    encoded = json.dumps(json_ready(payload), sort_keys=True, separators=(",", ":")).encode()
    return f"unesco_education_panel_{hashlib.sha256(encoded).hexdigest()}"
