from pathlib import Path

from polaris.harmonization import export_harmonized_dataset, harmonize_datasets
from polaris.ingestion import IngestionConfiguration, IngestionRequest, ingest_dataset
from polaris.registry import DatasetRegistry
from tests.harmonization.helpers import request_for, wdi_result, who_result


def test_export_is_phase3_compatible_and_deterministic(tmp_path: Path) -> None:
    harmonized = harmonize_datasets(request=request_for(wdi_result(tmp_path), who_result(tmp_path)))
    csv_path = tmp_path / "harmonized.csv"
    manifest_path = tmp_path / "harmonized_manifest.json"
    summary_path = tmp_path / "summary.json"

    manifest = export_harmonized_dataset(
        harmonized=harmonized,
        csv_path=csv_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
    )
    first = csv_path.read_text(encoding="utf-8")
    export_harmonized_dataset(harmonized=harmonized, csv_path=csv_path)

    assert csv_path.read_text(encoding="utf-8") == first
    assert first.splitlines()[0].split(",") == [
        "canonical_country_code",
        "canonical_country_name",
        "year",
        "wdi_gdp_per_capita_current_usd",
        "who_life_expectancy_at_birth_both_sexes",
    ]
    assert manifest_path.exists()
    assert summary_path.exists()

    ingested = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=csv_path,
            expected_checksum=manifest.checksum,
            configuration=IngestionConfiguration(),
        ),
    )
    assert ingested.validation_report.analysis_ready is True
    assert ingested.validation_report.accepted_row_count == 2
