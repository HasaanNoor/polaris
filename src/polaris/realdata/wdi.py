"""World Bank WDI compatibility preparation for Phase 11 validation."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from polaris.ingestion.loader import calculate_sha256
from polaris.providers.world_bank import build_provider
from polaris.schemas.common import DatasetStatus
from polaris.schemas.dataset import DatasetManifest, DatasetVariable, RevisionMetadata

WDI_INDICATORS = {
    "SP.DYN.LE00.IN": "life_expectancy_at_birth",
    "NY.GDP.PCAP.CD": "gdp_per_capita_current_usd",
    "SE.SEC.ENRR": "secondary_school_enrollment",
}


def prepare_wdi_validation_extract(
    *,
    source_path: str | Path,
    output_path: str | Path,
    min_year: int = 2015,
    max_year: int = 2023,
) -> Path:
    """Convert official WDI wide indicator rows into Phase 3 country-year columns."""

    source = Path(source_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    records: dict[tuple[str, int], dict[str, str]] = {}
    country_names: dict[str, str] = {}
    with source.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        year_columns = tuple(
            column
            for column in reader.fieldnames or ()
            if column.isdigit() and min_year <= int(column) <= max_year
        )
        for row in reader:
            indicator = row.get("Indicator Code", "")
            variable_id = WDI_INDICATORS.get(indicator)
            if variable_id is None:
                continue
            country_code = (row.get("Country Code") or "").strip()
            if not country_code:
                continue
            country_names[country_code] = (row.get("Country Name") or "").strip()
            for year_column in year_columns:
                value = (row.get(year_column) or "").strip()
                key = (country_code, int(year_column))
                record = records.setdefault(
                    key,
                    {
                        "country_code": country_code,
                        "country_name": country_names[country_code],
                        "year": year_column,
                    },
                )
                record[variable_id] = value

    fieldnames = (
        "country_code",
        "country_name",
        "year",
        "life_expectancy_at_birth",
        "gdp_per_capita_current_usd",
        "secondary_school_enrollment",
    )
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for _, record in sorted(records.items()):
            writer.writerow({field: record.get(field, "") for field in fieldnames})
    return destination


def wdi_validation_manifest(
    *,
    prepared_path: str | Path,
    source_path: str | Path,
) -> DatasetManifest:
    """Create a Phase 3-compatible manifest for the prepared official WDI extract."""

    provider = build_provider()
    dataset = provider.get_dataset("WDI")
    if dataset is None:
        raise ValueError("World Bank WDI provider metadata is unavailable")
    checksum = calculate_sha256(prepared_path)
    variables = [
        _copy_variable(variable, source_field_name=variable.variable_id)
        for variable in dataset.variables
    ]
    variables.insert(
        1,
        DatasetVariable(
            variable_id="country_name",
            label="Country name",
            data_type="string",
            role="identifier",
            source_field_name="country_name",
        ),
    )
    return DatasetManifest(
        dataset_id=f"world_bank_wdi_real_validation_{checksum[:12]}",
        title="World Bank WDI Real Validation Extract",
        provider=provider.metadata().name,
        source_url=dataset.source_url,
        access_url=str(prepared_path),
        description=(
            "Phase 11 validation extract prepared from the official downloaded WDI bulk CSV. "
            f"Original source file: {Path(source_path)}."
        ),
        license=dataset.license,
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=dataset.geographic_coverage,
        temporal_coverage=dataset.temporal_coverage,
        revision_metadata=RevisionMetadata(
            release_date=dataset.publication_date,
            update_frequency=dataset.frequency,
            source_version=dataset.version,
        ),
        variables=variables,
        units=list(dataset.units),
        frequency=dataset.frequency,
        methodology_reference=dataset.methodology_reference,
        source_version=dataset.version,
        retrieval_timestamp=datetime.now(UTC),
        checksum=checksum,
    )


def _copy_variable(variable: DatasetVariable, *, source_field_name: str) -> DatasetVariable:
    return DatasetVariable(
        variable_id=variable.variable_id,
        label=variable.label,
        description=variable.description,
        unit=variable.unit,
        data_type=variable.data_type,
        role=variable.role,
        source_field_name=source_field_name,
        missing_value_representation=variable.missing_value_representation,
        comparability_notes=variable.comparability_notes,
    )
