from pathlib import Path

from polaris.harmonization import HarmonizationRequest, JoinType
from polaris.harmonization.service import harmonize_datasets
from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.who import build_who_health_panel, export_who_health_panel
from polaris.who.examples import _harmonization_request, _wdi_example_manifest

CATALOG = Path("data/raw/who/gho/acquisition_catalog.json")


def test_panel_creation_preserves_provenance_and_deterministic_id() -> None:
    panel = build_who_health_panel(
        catalog_path=CATALOG,
        selected_indicators=("WHOSIS_000001", "GHED_CHEGDP_SHA2011"),
    )
    rebuilt = build_who_health_panel(
        catalog_path=CATALOG,
        selected_indicators=("GHED_CHEGDP_SHA2011", "WHOSIS_000001"),
    )

    assert panel.panel_id == rebuilt.panel_id
    assert panel.quality_summary.analysis_ready is True
    assert panel.quality_summary.aggregate_exclusions > 0
    assert len(panel.value_provenance) > 0
    first = panel.value_provenance[0]
    assert first.who_indicator_id in {"WHOSIS_000001", "GHED_CHEGDP_SHA2011"}
    assert len(first.source_checksum) == 64


def test_source_checksum_changes_panel_identity() -> None:
    panel = build_who_health_panel(
        catalog_path=CATALOG,
        selected_indicators=("WHOSIS_000001",),
    )
    changed = panel.model_copy(update={"source_checksums": {"WHOSIS_000001": "0" * 64}})

    assert panel.source_checksums != changed.source_checksums


def test_export_is_phase3_ingestible(tmp_path: Path) -> None:
    panel = build_who_health_panel(
        catalog_path=CATALOG,
        selected_indicators=("WHOSIS_000001", "GHED_CHEGDP_SHA2011"),
    )
    exported = export_who_health_panel(panel=panel, output_dir=tmp_path, write_provenance=False)
    manifest = exported.manifest_path.read_text(encoding="utf-8")

    assert "who_life_expectancy_birth_years" in manifest
    result = ingest_dataset(
        registry=DatasetRegistry((panel_export_manifest(exported.manifest_path),)),
        request=IngestionRequest(
            dataset_id=panel.panel_id,
            source_path=exported.csv_path,
            expected_checksum=exported.checksum_sha256,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )

    assert result.validation_report.analysis_ready is True


def test_phase12_accepts_who_panel_generically(tmp_path: Path) -> None:
    panel = build_who_health_panel(
        catalog_path=CATALOG,
        selected_indicators=("WHOSIS_000001", "GHED_CHEGDP_SHA2011"),
    )
    exported = export_who_health_panel(panel=panel, output_dir=tmp_path, write_provenance=False)
    who_result = ingest_dataset(
        registry=DatasetRegistry((panel_export_manifest(exported.manifest_path),)),
        request=IngestionRequest(
            dataset_id=panel.panel_id,
            source_path=exported.csv_path,
            expected_checksum=exported.checksum_sha256,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    wdi_manifest = _wdi_example_manifest("data/examples/world_bank_wdi_sample.csv")
    wdi_result = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=Path("data/examples/world_bank_wdi_sample.csv"),
            expected_checksum=wdi_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    request = _harmonization_request(wdi_result=wdi_result, who_result=who_result)
    request = HarmonizationRequest(
        ingestion_results=request.ingestion_results,
        dataset_configs=request.dataset_configs,
        variable_mappings=tuple(
            mapping
            for mapping in request.variable_mappings
            if mapping.canonical_variable_id
            in {
                "wdi_gdp_per_capita_current_usd",
                "who_life_expectancy_birth_years",
                "who_health_expenditure_pct_gdp",
            }
        ),
        join_type=JoinType.LEFT,
        anchor_dataset_id=wdi_result.dataset_manifest.dataset_id,
        temporal_scope=request.temporal_scope,
    )
    harmonized = harmonize_datasets(request=request)

    assert harmonized.quality_summary.analysis_ready is True
    assert harmonized.quality_summary.output_country_year_record_count == 3


def panel_export_manifest(path: Path):
    from polaris.who.examples import panel_export_manifest as load_manifest

    return load_manifest(path)
