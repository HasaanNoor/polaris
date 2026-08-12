from pathlib import Path

from polaris.harmonization import (
    DatasetHarmonizationConfig,
    HarmonizationRequest,
    JoinType,
    VariableMapping,
    harmonize_datasets,
)
from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from polaris.schemas.common import TemporalScope
from polaris.schemas.dataset import DatasetManifest
from polaris.unesco import build_unesco_education_panel, export_unesco_education_panel

RAW_ROOT = Path("data/raw")


def test_panel_determinism_and_value_provenance(tmp_path):
    panel_a = build_unesco_education_panel(raw_root=RAW_ROOT / "unesco")
    panel_b = build_unesco_education_panel(raw_root=RAW_ROOT / "unesco")
    assert panel_a.panel_id == panel_b.panel_id
    assert panel_a.creation_timestamp != panel_b.creation_timestamp
    assert panel_a.records == panel_b.records
    assert panel_a.quality_summary.analysis_ready
    assert panel_a.value_provenance
    first = panel_a.value_provenance[0]
    assert first.source_checksum == panel_a.source_checksums["SDG:data"]
    assert first.sex == "both sexes"


def test_export_is_phase3_ingestable(tmp_path):
    panel = build_unesco_education_panel(raw_root=RAW_ROOT / "unesco")
    export = export_unesco_education_panel(panel=panel, output_dir=tmp_path, write_provenance=False)
    manifest = DatasetManifest.model_validate_json(export.manifest_path.read_text(encoding="utf-8"))
    result = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(dataset_id=export.dataset_id, source_path=export.csv_path),
    )
    assert result.validation_report.analysis_ready


def test_wdi_unesco_phase12_harmonization(tmp_path):
    panel = build_unesco_education_panel(raw_root=RAW_ROOT / "unesco")
    export = export_unesco_education_panel(panel=panel, output_dir=tmp_path, write_provenance=False)
    from polaris.unesco.export import unesco_education_panel_manifest

    unesco_manifest = unesco_education_panel_manifest(panel=panel, csv_path=export.csv_path)
    unesco = ingest_dataset(
        registry=DatasetRegistry((unesco_manifest,)),
        request=IngestionRequest(
            dataset_id=unesco_manifest.dataset_id,
            source_path=export.csv_path,
            expected_checksum=unesco_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )
    wdi_source = RAW_ROOT / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    wdi_csv = prepare_wdi_validation_extract(
        source_path=wdi_source,
        output_path=tmp_path / "wdi.csv",
        min_year=2015,
        max_year=2021,
    )
    wdi_manifest = wdi_validation_manifest(prepared_path=wdi_csv, source_path=wdi_source)
    wdi = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=wdi_csv,
            expected_checksum=wdi_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )
    harmonized = harmonize_datasets(
        request=HarmonizationRequest(
            ingestion_results=(wdi, unesco),
            dataset_configs=(
                _config(wdi, "wdi", "world_bank"),
                _config(unesco, "unesco", "unesco"),
            ),
            variable_mappings=(
                _mapping(
                    wdi,
                    "gdp_per_capita_current_usd",
                    "wdi_gdp_per_capita_current_usd",
                    "GDP per capita",
                    "current US dollars",
                ),
                _mapping(
                    unesco,
                    "uis_upper_secondary_attainment_rate_25plus",
                    "uis_upper_secondary_attainment_rate_25plus",
                    "Upper secondary attainment",
                    "percent",
                ),
            ),
            join_type=JoinType.INNER,
            temporal_scope=TemporalScope(start=2015, end=2021),
        )
    )
    assert harmonized.records
    assert any(
        "uis_upper_secondary_attainment_rate_25plus" in record.values
        for record in harmonized.records
    )


def _config(result, alias: str, provider: str) -> DatasetHarmonizationConfig:
    return DatasetHarmonizationConfig(
        dataset_id=result.dataset_manifest.dataset_id,
        alias=alias,
        provider=provider,
        country_field="country_code",
        country_name_field="country_name",
        year_field="year",
    )


def _mapping(result, source_id: str, canonical_id: str, label: str, unit: str) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider=result.dataset_manifest.provider,
        source_variable_id=source_id,
        source_field_name=source_id,
        canonical_variable_id=canonical_id,
        canonical_label=label,
        source_unit=unit,
        canonical_unit=unit,
        conceptual_definition=label,
        expected_data_type="float",
    )
