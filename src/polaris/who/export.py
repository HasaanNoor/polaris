"""Exports for WHOHealthPanel artifacts."""

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
from polaris.who.models import WHOHealthPanel, WHOPanelExportResult


def export_who_health_panel(
    *,
    panel: WHOHealthPanel,
    output_dir: str | Path,
    csv_name: str = "who_health_panel_sample.csv",
    write_variable_catalog: bool = True,
    write_deferred_indicators: bool = True,
    write_provenance: bool = True,
) -> WHOPanelExportResult:
    """Export deterministic analytical CSV plus Phase 3-compatible metadata."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / csv_name
    manifest_path = output / "who_health_panel_manifest.json"
    summary_path = output / "who_health_panel_quality_summary.json"
    variable_catalog_path = output / "who_integrated_variables.json"
    deferred_path = output / "who_deferred_indicators.json"
    provenance_path = output / "who_health_panel_value_provenance.json"

    variable_ids = tuple(
        mapping.canonical_variable_id for mapping in panel.selected_indicator_definitions
    )
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

    manifest = who_health_panel_manifest(panel=panel, csv_path=csv_path)
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(panel.quality_summary.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if write_variable_catalog:
        variable_catalog_path.write_text(
            json.dumps(
                [
                    mapping.model_dump(mode="json")
                    for mapping in panel.selected_indicator_definitions
                ],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    if write_deferred_indicators:
        deferred_path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in panel.deferred_indicators],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    if write_provenance:
        provenance_path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in panel.value_provenance],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    return WHOPanelExportResult(
        csv_path=csv_path,
        manifest_path=manifest_path,
        quality_summary_path=summary_path,
        variable_catalog_path=variable_catalog_path if write_variable_catalog else None,
        deferred_indicators_path=deferred_path if write_deferred_indicators else None,
        provenance_path=provenance_path if write_provenance else None,
        dataset_id=manifest.dataset_id,
        checksum_sha256=manifest.checksum or calculate_sha256(csv_path),
    )


def who_health_panel_manifest(*, panel: WHOHealthPanel, csv_path: str | Path) -> DatasetManifest:
    """Create a Phase 3-compatible manifest for the analytical WHO CSV export."""

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
    for mapping in panel.selected_indicator_definitions:
        variables.append(
            DatasetVariable(
                variable_id=mapping.canonical_variable_id,
                label=mapping.canonical_label,
                description=mapping.conceptual_definition,
                unit=mapping.unit,
                data_type=DataType.FLOAT,
                role=VariableRole.OUTCOME,
                source_field_name=mapping.canonical_variable_id,
                comparability_notes=list(mapping.notes),
            )
        )
    return DatasetManifest(
        dataset_id=panel.panel_id,
        title="Curated WHO GHO Health Country-Year Panel",
        provider="World Health Organization",
        source_url="https://www.who.int/data/gho",
        access_url=str(path),
        description=(
            "Derived Polaris Phase 15 panel from official locally downloaded WHO GHO "
            "OData snapshots. Raw provider files are immutable and not included in this CSV."
        ),
        license="WHO data terms and conditions",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(
            codes=sorted({record.canonical_country_code for record in panel.records}),
            description="Country-level WHO rows; aggregate entities excluded by default.",
        ),
        temporal_coverage=TemporalScope(
            start=min(years) if years else None,
            end=max(years) if years else None,
            label="Annual country-year records",
        ),
        revision_metadata=RevisionMetadata(update_frequency="provider snapshot"),
        variables=variables,
        units=[
            "country-year",
            *sorted({mapping.unit for mapping in panel.selected_indicator_definitions}),
        ],
        frequency="annual",
        methodology_reference="https://www.who.int/data/gho/indicator-metadata-registry",
        comparability_warnings=[],
        source_version=panel.ruleset_version,
        checksum=checksum,
        schema_version="1.0.0",
    )
