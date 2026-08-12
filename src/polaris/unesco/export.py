"""Exports for UNESCOEducationPanel artifacts."""

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
from polaris.unesco.models import UNESCOEducationPanel, UNESCOEducationPanelExportResult


def export_unesco_education_panel(
    *,
    panel: UNESCOEducationPanel,
    output_dir: str | Path,
    csv_name: str = "unesco_education_panel_sample.csv",
    write_provenance: bool = True,
) -> UNESCOEducationPanelExportResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / csv_name
    manifest_path = output / "unesco_education_panel_manifest.json"
    summary_path = output / "unesco_education_quality_summary.json"
    variable_catalog_path = output / "unesco_integrated_variables.json"
    deferred_path = output / "unesco_deferred_indicators.json"
    provenance_path = output / "unesco_education_value_provenance.json"
    variable_ids = tuple(
        mapping.canonical_variable_id for mapping in panel.integrated_variable_catalog
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=("country_code", "country_name", "year", *variable_ids)
        )
        writer.writeheader()
        for record in panel.records:
            row = {
                "country_code": record.canonical_country_code,
                "country_name": record.canonical_country_name,
                "year": record.year,
            }
            row.update(
                {variable_id: record.values.get(variable_id) for variable_id in variable_ids}
            )
            writer.writerow(row)

    manifest = unesco_education_panel_manifest(panel=panel, csv_path=csv_path)
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps(panel.quality_summary.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    variable_catalog_path.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in panel.integrated_variable_catalog],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    deferred_path.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in panel.deferred_indicator_registry],
            separators=(",", ":"),
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
    return UNESCOEducationPanelExportResult(
        csv_path=csv_path,
        manifest_path=manifest_path,
        quality_summary_path=summary_path,
        variable_catalog_path=variable_catalog_path,
        deferred_indicators_path=deferred_path,
        provenance_path=provenance_path if write_provenance else None,
        dataset_id=manifest.dataset_id,
        checksum_sha256=manifest.checksum or calculate_sha256(csv_path),
    )


def unesco_education_panel_manifest(
    *,
    panel: UNESCOEducationPanel,
    csv_path: str | Path,
) -> DatasetManifest:
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
    for mapping in panel.integrated_variable_catalog:
        variables.append(
            DatasetVariable(
                variable_id=mapping.canonical_variable_id,
                label=mapping.canonical_label,
                description=mapping.definition,
                unit=mapping.unit,
                data_type=DataType.FLOAT,
                role=VariableRole.OUTCOME,
                source_field_name=mapping.canonical_variable_id,
                comparability_notes=list(mapping.notes),
            )
        )
    return DatasetManifest(
        dataset_id=panel.panel_id,
        title="Curated UNESCO UIS Education Country-Year Panel",
        provider="UNESCO Institute for Statistics",
        source_url="https://uis.unesco.org/",
        access_url=str(path),
        description=(
            "Derived Polaris Phase 17 panel from locally downloaded UNESCO UIS SDG national "
            "data. Raw provider files are immutable and not included in this CSV."
        ),
        license="UNESCO UIS data terms",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(
            codes=sorted({record.canonical_country_code for record in panel.records}),
            description="Country-level UNESCO rows; aggregate entities excluded by default.",
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
            *sorted({mapping.unit for mapping in panel.integrated_variable_catalog}),
        ],
        frequency="annual",
        methodology_reference="data/raw/unesco/SDG/SDG_LABEL.csv",
        comparability_warnings=[],
        source_version=panel.ruleset_version,
        checksum=checksum,
        schema_version="1.0.0",
    )
