"""Deterministic identity and provenance helpers for harmonization."""

from __future__ import annotations

import hashlib
import json

from polaris.harmonization.models import HarmonizationRequest


def deterministic_harmonized_dataset_id(request: HarmonizationRequest) -> str:
    """Build a stable ID from content-affecting request fields, never timestamps."""

    if request.output_dataset_id is not None:
        return request.output_dataset_id
    checksums = {
        result.dataset_manifest.dataset_id: result.checksum_sha256
        for result in request.ingestion_results
    }
    payload = {
        "input_dataset_ids": sorted(checksums),
        "source_checksums": {key: checksums[key] for key in sorted(checksums)},
        "dataset_configs": [
            config.model_dump(mode="json")
            for config in sorted(request.dataset_configs, key=lambda item: item.dataset_id)
        ],
        "variable_mappings": [
            mapping.model_dump(mode="json")
            for mapping in sorted(
                request.variable_mappings,
                key=lambda item: (
                    item.canonical_variable_id,
                    item.source_dataset_id,
                    item.source_field_name,
                ),
            )
        ],
        "join_type": request.join_type.value,
        "anchor_dataset_id": request.anchor_dataset_id,
        "geographic_scope": (
            request.geographic_scope.model_dump(mode="json")
            if request.geographic_scope is not None
            else None
        ),
        "temporal_scope": (
            request.temporal_scope.model_dump(mode="json")
            if request.temporal_scope is not None
            else None
        ),
        "provider_precedence": [
            rule.model_dump(mode="json")
            for rule in sorted(
                request.provider_precedence,
                key=lambda item: item.canonical_variable_id,
            )
        ],
        "strictness": request.strictness.model_dump(mode="json"),
        "ruleset_version": request.ruleset_version,
        "schema_version": request.schema_version,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return f"harmonized_country_year_{digest[:16]}"
