"""Deterministic identity helpers for WGI artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from polaris.wgi.models import WGI_PANEL_SCHEMA_VERSION, WGI_RULESET_VERSION, json_ready


def deterministic_wgi_panel_id(payload: dict[str, Any]) -> str:
    """Build a stable WGI panel identifier excluding creation timestamps."""

    stable = {
        "artifact": "wgi_governance_panel",
        "schema_version": WGI_PANEL_SCHEMA_VERSION,
        "ruleset_version": WGI_RULESET_VERSION,
        **payload,
    }
    digest = hashlib.sha256(
        json.dumps(json_ready(stable), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"wgi_governance_panel_{digest[:16]}"
