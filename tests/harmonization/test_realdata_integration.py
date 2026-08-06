from pathlib import Path

import pytest

from polaris.realdata.harmonization import run_phase12_real_harmonization_example


def test_real_wdi_who_harmonization_runs_through_phase9(tmp_path: Path) -> None:
    raw_root = Path("data/raw")
    if not (raw_root / "world_bank" / "WDI_CSV" / "WDICSV.csv").exists():
        pytest.skip("local World Bank WDI raw file is unavailable")
    if not (raw_root / "who" / "life_expectancy_at_birth_and_age_60.csv").exists():
        pytest.skip("local WHO life expectancy raw file is unavailable")

    result = run_phase12_real_harmonization_example(
        raw_root=raw_root,
        output_root=tmp_path,
    )

    assert result["quality_summary"]["analysis_ready"] is True
    assert result["quality_summary"]["output_country_year_record_count"] > 1000
    assert result["quality_summary"]["aggregate_entities_excluded"] > 0
    assert result["value_provenance_count"] > 0
    assert result["integrated_variables"] == (
        "wdi_gdp_per_capita_current_usd",
        "who_life_expectancy_at_birth_both_sexes",
    )
    assert (tmp_path / "harmonized_country_year_sample.csv").exists()
    assert (tmp_path / "harmonized_country_year_manifest.json").exists()
    assert (tmp_path / "harmonization_summary.json").exists()
    assert (tmp_path / "harmonized_phase12_report.md").exists()
    report = (tmp_path / "harmonized_phase12_report.md").read_text(encoding="utf-8")
    assert "Phase 12 Harmonized Country-Year Validation Report" in report
