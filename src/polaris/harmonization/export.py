"""Phase 3-compatible exports for harmonized country-year datasets."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from polaris.harmonization.models import HarmonizedDataset
from polaris.ingestion.loader import calculate_sha256
from polaris.schemas.common import (
    DatasetStatus,
    DataType,
    GeographicScope,
    TemporalScope,
    VariableRole,
)
from polaris.schemas.dataset import DatasetManifest, DatasetVariable, RevisionMetadata


def export_harmonized_dataset(
    *,
    harmonized: HarmonizedDataset,
    csv_path: str | Path,
    manifest_path: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> DatasetManifest:
    """Write deterministic CSV plus a generated Phase 3 manifest."""

    destination = Path(csv_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    variable_ids = tuple(
        entry.canonical_variable_id for entry in harmonized.canonical_variable_catalog
    )
    fieldnames = ("canonical_country_code", "canonical_country_name", "year", *variable_ids)
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in sorted(
            harmonized.records,
            key=lambda item: (item.canonical_country_code, item.year),
        ):
            row = {
                "canonical_country_code": record.canonical_country_code,
                "canonical_country_name": record.canonical_country_name,
                "year": record.year,
            }
            for variable_id in variable_ids:
                value = record.values.get(variable_id)
                row[variable_id] = "" if value is None else value
            writer.writerow(row)

    checksum = calculate_sha256(destination)
    manifest = _manifest(harmonized, destination, checksum)
    if manifest_path is not None:
        Path(manifest_path).write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    if summary_path is not None:
        payload = {
            "harmonized_dataset_id": harmonized.harmonized_dataset_id,
            "quality_summary": harmonized.quality_summary.model_dump(mode="json"),
            "findings": [finding.model_dump(mode="json") for finding in harmonized.findings],
        }
        Path(summary_path).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return manifest


def _manifest(harmonized: HarmonizedDataset, csv_path: Path, checksum: str) -> DatasetManifest:
    variables = [
        DatasetVariable(
            variable_id="canonical_country_code",
            label="Canonical country code",
            data_type=DataType.STRING,
            role=VariableRole.IDENTIFIER,
            source_field_name="canonical_country_code",
        ),
        DatasetVariable(
            variable_id="canonical_country_name",
            label="Canonical country name",
            data_type=DataType.STRING,
            role=VariableRole.IDENTIFIER,
            source_field_name="canonical_country_name",
        ),
        DatasetVariable(
            variable_id="year",
            label="Year",
            data_type=DataType.INTEGER,
            role=VariableRole.TIME,
            source_field_name="year",
        ),
    ]
    for entry in harmonized.canonical_variable_catalog:
        variables.append(
            DatasetVariable(
                variable_id=entry.canonical_variable_id,
                label=entry.canonical_label,
                description=entry.conceptual_definition,
                unit=entry.unit,
                data_type=DataType.FLOAT,
                role=VariableRole.PREDICTOR,
                source_field_name=entry.canonical_variable_id,
            )
        )
    years = harmonized.quality_summary.years_represented
    return DatasetManifest(
        dataset_id=harmonized.harmonized_dataset_id,
        title="Phase 12 Harmonized Country-Year Dataset",
        provider="Polaris derived harmonization",
        source_url="derived:polaris-harmonization",
        access_url=str(csv_path),
        description=(
            "Derived country-year artifact produced by Phase 12 harmonization. "
            "Original provider files are not modified; value-level provenance is retained "
            "inside the HarmonizedDataset artifact."
        ),
        license="Derived from input provider licenses; see source manifests.",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(
            codes=list(harmonized.quality_summary.countries_represented) or ["NONE"],
            description="Country-year keys retained by deterministic harmonization.",
        ),
        temporal_coverage=TemporalScope(
            start=min(years) if years else None,
            end=max(years) if years else None,
            label="Annual country-year records",
        ),
        revision_metadata=RevisionMetadata(
            source_version=harmonized.ruleset_version,
            update_frequency="derived on request",
        ),
        variables=variables,
        units=["country-year"],
        frequency="annual",
        methodology_reference="docs/decisions/015-cross-dataset-country-year-harmonization.md",
        source_version=harmonized.ruleset_version,
        retrieval_timestamp=datetime.now(UTC),
        checksum=checksum,
    )
