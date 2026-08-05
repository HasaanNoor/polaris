from pathlib import Path

from polaris.realdata.compatibility import validate_manifest_against_file, variable_summaries
from polaris.realdata.runner import run_real_dataset_validation
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest


def test_wdi_preparation_manifest_and_variable_summaries(tmp_path: Path) -> None:
    source = _write_wdi(tmp_path)
    prepared = prepare_wdi_validation_extract(
        source_path=source,
        output_path=tmp_path / "prepared.csv",
        min_year=2020,
        max_year=2021,
    )
    manifest = wdi_validation_manifest(prepared_path=prepared, source_path=source)

    validation = validate_manifest_against_file(manifest=manifest, source_path=prepared)
    summaries = variable_summaries(manifest, prepared)

    assert validation.checksum_matches is True
    assert validation.access_url_matches is True
    assert validation.compatible_with_phase3 is True
    assert validation.missing_manifest_columns == ()
    assert {summary.variable_id for summary in summaries} >= {
        "country_code",
        "year",
        "life_expectancy_at_birth",
        "gdp_per_capita_current_usd",
        "secondary_school_enrollment",
    }


def test_run_real_dataset_validation_executes_phase3_to_phase9(tmp_path: Path) -> None:
    source = _write_wdi(tmp_path / "raw")

    result = run_real_dataset_validation(
        raw_root=source.parents[2],
        output_root=tmp_path / "validation",
    )

    assert result.manifest_validation.compatible_with_phase3 is True
    assert result.pipeline.ingestion_succeeded is True
    assert result.pipeline.analysis_succeeded is True
    assert result.pipeline.evidence_extraction_succeeded is True
    assert result.pipeline.domain_assessments_succeeded is True
    assert result.pipeline.coordination_succeeded is True
    assert result.pipeline.synthesis_succeeded is True
    assert result.pipeline.report_generation_succeeded is True
    assert result.pipeline.analysis_sample_size >= 6
    assert (tmp_path / "validation" / "world_bank_wdi_phase11_validation_summary.json").exists()
    assert (tmp_path / "validation" / "world_bank_wdi_phase11_report.md").exists()


def _write_wdi(root: Path) -> Path:
    wdi_dir = root / "world_bank" / "WDI_CSV"
    wdi_dir.mkdir(parents=True)
    path = wdi_dir / "WDICSV.csv"
    lines = ["Country Name,Country Code,Indicator Name,Indicator Code,2020,2021"]
    rows = {
        "AAA": {
            "name": "Alpha",
            "life": (60.0, 61.0),
            "gdp": (1000.0, 1100.0),
            "school": (50.0, 51.0),
        },
        "BBB": {
            "name": "Beta",
            "life": (65.0, 66.0),
            "gdp": (2000.0, 2100.0),
            "school": (60.0, 61.0),
        },
        "CCC": {
            "name": "Gamma",
            "life": (70.0, 71.0),
            "gdp": (3000.0, 3100.0),
            "school": (70.0, 71.0),
        },
        "DDD": {
            "name": "Delta",
            "life": (75.0, 76.0),
            "gdp": (4000.0, 4100.0),
            "school": (80.0, 81.0),
        },
    }
    for code, values in rows.items():
        lines.extend(
            [
                _wdi_row(values["name"], code, "Life expectancy", "SP.DYN.LE00.IN", values["life"]),
                _wdi_row(
                    values["name"],
                    code,
                    "GDP per capita",
                    "NY.GDP.PCAP.CD",
                    values["gdp"],
                ),
                _wdi_row(
                    values["name"],
                    code,
                    "Secondary enrollment",
                    "SE.SEC.ENRR",
                    values["school"],
                ),
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _wdi_row(
    country_name: str,
    country_code: str,
    indicator_name: str,
    indicator_code: str,
    values: tuple[float, float],
) -> str:
    return (
        f"{country_name},{country_code},{indicator_name},{indicator_code},{values[0]},{values[1]}"
    )
