from pathlib import Path

from polaris.who.examples import run_phase15_wdi_who_example


def test_phase15_wdi_who_project_example_runs(tmp_path: Path) -> None:
    summary = run_phase15_wdi_who_example(output_dir=tmp_path)

    assert summary["project_status"] == "completed"
    assert summary["harmonized_rows"] == 3
    assert "who_life_expectancy_birth_years" in summary["harmonized_variables"]
    assert (tmp_path / "who_health_panel_sample.csv").exists()
    assert (tmp_path / "who_health_panel_manifest.json").exists()
    assert (tmp_path / "who_health_panel_quality_summary.json").exists()
    assert (tmp_path / "who_integrated_variables.json").exists()
    assert (tmp_path / "who_deferred_indicators.json").exists()
    assert (tmp_path / "wdi_who_phase15_project_summary.json").exists()
    assert (tmp_path / "wdi_who_phase15_report.md").exists()
