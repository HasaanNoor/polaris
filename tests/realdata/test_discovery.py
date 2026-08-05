from pathlib import Path

from polaris.realdata.discovery import discover_real_datasets, inspect_schema


def test_discover_real_datasets_finds_provider_layouts(tmp_path: Path) -> None:
    wdi_dir = tmp_path / "world_bank" / "WDI_CSV"
    who_dir = tmp_path / "who"
    unesco_dir = tmp_path / "unesco" / "SDG"
    wdi_dir.mkdir(parents=True)
    who_dir.mkdir()
    unesco_dir.mkdir(parents=True)
    _write(wdi_dir / "WDICSV.csv", "Country Code,Indicator Code,2020\nAAA,X,1\n")
    _write(wdi_dir / "WDISeries.csv", "x\n1\n")
    _write(who_dir / "life_expectancy_at_birth_and_age_60.csv", "Location,Period,Value\nA,2020,1\n")
    _write(unesco_dir / "SDG_DATA_NATIONAL.csv", "COUNTRY_ID,YEAR,INDICATOR_ID,VALUE\nA,2020,X,1\n")

    discovered = discover_real_datasets(tmp_path)

    assert [(item.provider, item.dataset_key) for item in discovered] == [
        ("world_bank", "WDI"),
        ("who", "life_expectancy_at_birth_and_age_60"),
        ("unesco", "SDG_DATA_NATIONAL"),
    ]
    assert discovered[0].companion_files == (wdi_dir / "WDISeries.csv",)


def test_inspect_schema_profiles_identifiers_variables_and_missing_values(tmp_path: Path) -> None:
    path = tmp_path / "who.csv"
    _write(
        path,
        "\n".join(
            [
                "SpatialDimValueCode,Location,Period,IndicatorCode,NumericValue",
                "AFG,Afghanistan,2020,WHOSIS_000001,60.1",
                "ALB,Albania,2020,WHOSIS_000001,",
            ]
        )
        + "\n",
    )

    inspection = inspect_schema(path, max_rows=None)

    assert inspection.country_identifier.present is True
    assert inspection.country_identifier.column == "SpatialDimValueCode"
    assert inspection.year_identifier.present is True
    assert inspection.year_identifier.invalid_count == 0
    assert "IndicatorCode" in inspection.variable_columns
    assert ("NumericValue", 1) in inspection.missing_value_counts


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
