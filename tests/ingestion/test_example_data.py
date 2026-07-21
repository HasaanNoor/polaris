from polaris.ingestion import (
    IngestionConfiguration,
    IngestionRequest,
    UnexpectedColumnMode,
    ingest_dataset,
)
from tests.ingestion.helpers import DATA_EXAMPLES_DIR


def test_ingest_world_bank_example(registry) -> None:
    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id="world_bank_wdi_illustrative",
            source_path=DATA_EXAMPLES_DIR / "world_bank_wdi_sample.csv",
            configuration=_permissive_configuration(),
        ),
    )

    assert result.validation_report.accepted_row_count == 3
    assert result.validation_report.unexpected_columns == ("Country Code", "Year")
    assert result.validation_report.analysis_ready is True


def test_ingest_who_example_with_type_issue(registry) -> None:
    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id="who_gho_illustrative",
            source_path=DATA_EXAMPLES_DIR / "who_gho_sample.csv",
            configuration=_permissive_configuration(),
        ),
    )

    assert result.validation_report.accepted_row_count == 2
    assert result.validation_report.rejected_row_count == 1
    assert result.quality_profile.variables[0].invalid_value_count == 1


def test_ingest_unesco_example(registry) -> None:
    result = ingest_dataset(
        registry=registry,
        request=IngestionRequest(
            dataset_id="unesco_uis_illustrative",
            source_path=DATA_EXAMPLES_DIR / "unesco_uis_sample.csv",
            configuration=_permissive_configuration(),
        ),
    )

    assert result.validation_report.accepted_row_count == 3
    assert result.quality_profile.variables[0].null_count == 1
    assert result.quality_profile.variables[1].null_count == 1


def test_registry_search_behavior_remains_available(registry) -> None:
    results = registry.search()

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
        "unesco_uis_illustrative",
    ]


def _permissive_configuration() -> IngestionConfiguration:
    return IngestionConfiguration(unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE)
