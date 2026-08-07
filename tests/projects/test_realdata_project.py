from pathlib import Path

import pytest

from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.projects import run_research_project
from polaris.projects.models import ProjectStatus
from polaris.realdata.harmonization import (
    _phase12_request,
    _phase12_specification,
    prepare_who_life_expectancy_extract,
    who_life_expectancy_manifest,
)
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from tests.projects.helpers import base_request


def test_realdata_project_runs_when_local_raw_files_exist(tmp_path: Path) -> None:
    raw_root = Path("data/raw")
    wdi_raw = raw_root / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    who_raw = raw_root / "who" / "life_expectancy_at_birth_and_age_60.csv"
    if not wdi_raw.exists() or not who_raw.exists():
        pytest.skip("local Phase 11/12 raw files are unavailable")

    wdi_prepared = prepare_wdi_validation_extract(
        source_path=wdi_raw,
        output_path=tmp_path / "wdi.csv",
        min_year=2015,
        max_year=2021,
    )
    who_prepared = prepare_who_life_expectancy_extract(
        source_path=who_raw,
        output_path=tmp_path / "who.csv",
        min_year=2015,
        max_year=2021,
    )
    wdi_manifest = wdi_validation_manifest(prepared_path=wdi_prepared, source_path=wdi_raw)
    who_manifest = who_life_expectancy_manifest(prepared_path=who_prepared, source_path=who_raw)
    wdi = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=wdi_prepared,
            expected_checksum=wdi_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )
    who = ingest_dataset(
        registry=DatasetRegistry((who_manifest,)),
        request=IngestionRequest(
            dataset_id=who_manifest.dataset_id,
            source_path=who_prepared,
            expected_checksum=who_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )
    hrequest = _phase12_request(wdi_result=wdi, who_result=who)
    request = base_request(
        dataset_inputs=(
            {"kind": "ingestion_artifact", "ingestion_result": wdi},
            {"kind": "ingestion_artifact", "ingestion_result": who},
        ),
        harmonization={
            "dataset_configs": hrequest.dataset_configs,
            "variable_mappings": hrequest.variable_mappings,
            "join_type": hrequest.join_type,
            "anchor_dataset_id": hrequest.anchor_dataset_id,
        },
        statistical_specification=_phase12_specification(),
        output_directory=tmp_path / "outputs",
    )

    result = run_research_project(request)

    assert result.overall_status is ProjectStatus.COMPLETED
    assert result.harmonized_dataset is not None
    assert result.analysis_result is not None
    assert result.research_report is not None
