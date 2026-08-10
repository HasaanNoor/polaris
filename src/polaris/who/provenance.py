"""Deterministic provenance helpers for WHO panel artifacts."""

from __future__ import annotations

import hashlib
import json

from polaris.who.models import WHO_PANEL_SCHEMA_VERSION, WHO_RULESET_VERSION, json_ready


def deterministic_who_panel_id(*, payload: object) -> str:
    """Return a deterministic WHO panel ID from stable inputs only."""

    encoded = json.dumps(json_ready(payload), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"who_health_panel_{WHO_RULESET_VERSION}_{WHO_PANEL_SCHEMA_VERSION}_{digest}"
