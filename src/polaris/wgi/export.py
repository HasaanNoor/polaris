"""Exports for WGIGovernancePanel artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from polaris.ingestion.loader import calculate_sha256
from polaris.schemas.common import (
    DatasetStatus,
    DataType,
    GeographicScope,
    TemporalScope,
    VariableRole,
)
from polaris.schemas.dataset import DatasetManifest, DatasetVariable, RevisionMetadata
from polaris.wgi.models import WGI_SOURCE_URL, WGIGovernancePanel, WGIPanelExportResult


def export_wgi_governance_panel(
    *,
    panel: WGIGovernancePanel,
    output_dir: str | Path,
    csv_name: str = "wgi_governance_panel_sample.csv",
    write_provenance: bool = True,
) -> WGIPanelExportResult:
    """Export deterministic analytical CSV plus Phase 3-compatible metadata."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / csv_name
    manifest_path = output / "wgi_governance_panel_manifest.json"
    summary_path = output / "wgi_governance_quality_summary.json"
    catalog_path = output / "wgi_variable_catalog.json"
    provenance_path = output / "wgi_value_provenance.json"
    variable_ids = tuple(mapping.canonical_variable_id for mapping in panel.variable_catalog)
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        fieldnames = ("country_code", "country_name", "year", *variable_ids)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in panel.records:
            row = {
                "country_code": record.canonical_country_code,
                "country_name": record.canonical_country_name,
                "year": record.year,
            }
            row.update({variable: record.values.get(variable) for variable in variable_ids})
            writer.writerow(row)
    manifest = wgi_governance_panel_manifest(panel=panel, csv_path=csv_path)
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(panel.quality_summary.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    catalog_path.write_text(
        json.dumps(
            [mapping.model_dump(mode="json") for mapping in panel.variable_catalog],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if write_provenance:
        provenance_path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in panel.provenance],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    return WGIPanelExportResult(
        csv_path=csv_path,
        manifest_path=manifest_path,
        quality_summary_path=summary_path,
        variable_catalog_path=catalog_path,
        provenance_path=provenance_path if write_provenance else None,
        dataset_id=manifest.dataset_id,
        checksum_sha256=manifest.checksum or calculate_sha256(csv_path),
    )


def wgi_governance_panel_manifest(
    *,
    panel: WGIGovernancePanel,
    csv_path: str | Path,
) -> DatasetManifest:
    """Create a Phase 3-compatible manifest for the analytical WGI CSV export."""

    path = Path(csv_path)
    checksum = calculate_sha256(path)
    years = [record.year for record in panel.records]
    variables = [
        DatasetVariable(
            variable_id="country_code",
            label="Canonical country code",
            description="ISO-3 country code after reviewed exact normalization.",
            data_type=DataType.STRING,
            role=VariableRole.IDENTIFIER,
            source_field_name="country_code",
        ),
        DatasetVariable(
            variable_id="country_name",
            label="Canonical country name",
            description="Canonical country label from reviewed exact normalization.",
            data_type=DataType.STRING,
            role=VariableRole.IDENTIFIER,
            source_field_name="country_name",
        ),
        DatasetVariable(
            variable_id="year",
            label="Calendar year",
            data_type=DataType.INTEGER,
            role=VariableRole.TIME,
            source_field_name="year",
        ),
    ]
    for mapping in panel.variable_catalog:
        variables.append(
            DatasetVariable(
                variable_id=mapping.canonical_variable_id,
                label=mapping.canonical_label,
                description=mapping.definition,
                unit=mapping.estimate_unit,
                data_type=DataType.FLOAT,
                role=VariableRole.PREDICTOR,
                source_field_name=mapping.canonical_variable_id,
                comparability_notes=[
                    "Central WGI governance estimate is used analytically.",
                    (
                        "Standard error, absolute governance score, score bounds, and "
                        "source count are preserved separately as provenance metadata."
                    ),
                    (
                        "No composite governance score, interpolation, smoothing, "
                        "forward-fill, or imputation is applied."
                    ),
                ],
            )
        )
    return DatasetManifest(
        dataset_id=panel.panel_id,
        title="World Bank WGI Governance Country-Year Panel",
        provider="World Bank Worldwide Governance Indicators",
        source_url=WGI_SOURCE_URL,
        access_url=str(path),
        description=(
            "Derived Polaris Phase 16 panel from official World Bank WGI API CSV ZIP "
            "snapshots. Raw provider ZIP files are immutable and excluded from Git."
        ),
        license="Creative Commons Attribution 4.0",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(
            codes=sorted({record.canonical_country_code for record in panel.records}),
            description=(
                "Sovereign-country WGI rows; aggregates and territories excluded by default."
            ),
        ),
        temporal_coverage=TemporalScope(
            start=min(years) if years else None,
            end=max(years) if years else None,
            label="Annual country-year records",
        ),
        revision_metadata=RevisionMetadata(
            release_date="2026-03-18",
            update_frequency="provider snapshot",
            source_version="2025 Revision",
        ),
        variables=variables,
        units=["country-year", "standard normal governance estimate"],
        frequency="annual",
        methodology_reference="https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation",
        source_version=panel.ruleset_version,
        checksum=checksum,
        schema_version="1.0.0",
    )
