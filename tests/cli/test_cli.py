from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from polaris.cli.app import app

runner = CliRunner()


def invoke(args: list[str]):
    return runner.invoke(app, args)


def test_top_level_help() -> None:
    result = invoke(["--help"])
    assert result.exit_code == 0
    assert "datasets" in result.output
    assert "project" in result.output


def test_dataset_listing() -> None:
    result = invoke(["datasets", "list"])
    assert result.exit_code == 0
    assert "world_bank_wdi_illustrative" in result.output


def test_dataset_inspection() -> None:
    result = invoke(["datasets", "inspect", "world_bank_wdi_illustrative"])
    assert result.exit_code == 0
    assert "World Bank" in result.output


def test_yaml_loading_and_valid_project_config() -> None:
    result = invoke(["project", "validate", "examples/projects/basic_cross_sectional.yaml"])
    assert result.exit_code == 0
    assert "Configuration valid." in result.output


def test_json_loading(tmp_path: Path) -> None:
    import yaml

    yaml_payload = yaml.safe_load(Path("examples/projects/basic_cross_sectional.yaml").read_text())
    path = tmp_path / "project.json"
    path.write_text(json.dumps(yaml_payload), encoding="utf-8")
    result = invoke(["project", "validate", path.as_posix(), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["valid"] is True


def test_invalid_project_configuration(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("schema_version: 1.0.0\nproject: {}\n", encoding="utf-8")
    result = invoke(["project", "validate", path.as_posix()])
    assert result.exit_code == 2
    assert "Invalid project configuration" in result.output


def test_unknown_dataset(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        Path("examples/projects/basic_cross_sectional.yaml")
        .read_text(encoding="utf-8")
        .replace("harmonized_country_year_610b7b1c05b09044", "harmonized_country_year_typo"),
        encoding="utf-8",
    )
    result = invoke(["project", "validate", path.as_posix()])
    assert result.exit_code == 2
    assert "Dataset not found" in result.output
    assert "Did you mean" in result.output


def test_unknown_variable(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        Path("examples/projects/basic_cross_sectional.yaml")
        .read_text(encoding="utf-8")
        .replace("wgi_government_effectiveness", "wgi_government_effect"),
        encoding="utf-8",
    )
    result = invoke(["project", "validate", path.as_posix()])
    assert result.exit_code == 2
    assert "Analysis variable not found" in result.output
    assert "Did you mean" in result.output


def test_dry_run() -> None:
    result = invoke(["project", "run", "examples/projects/basic_cross_sectional.yaml", "--dry-run"])
    assert result.exit_code == 0
    assert "Execution Plan" in result.output
    assert "ANALYZE" in result.output


def test_successful_deterministic_project_run_and_inspection(tmp_path: Path) -> None:
    config = tmp_path / "project.yaml"
    text = Path("examples/projects/visualization_example.yaml").read_text(encoding="utf-8")
    config.write_text(text.replace("outputs/projects", tmp_path.as_posix()), encoding="utf-8")
    result = invoke(["project", "run", config.as_posix()])
    assert result.exit_code == 0
    project_id = _project_id(result.output)
    root = tmp_path / project_id
    assert (root / "project.json").exists()
    assert (root / "reproducibility-manifest.json").exists()
    assert list((root / "visualizations").glob("*/figure.png"))

    default_root_config = tmp_path / "default.yaml"
    default_root_config.write_text(text, encoding="utf-8")
    default_run = invoke(["project", "run", default_root_config.as_posix()])
    assert default_run.exit_code == 0
    default_project_id = _project_id(default_run.output)
    inspect = invoke(["project", "inspect", default_project_id])
    assert inspect.exit_code == 0
    assert "Project" in inspect.output


def test_project_listing_and_json_output() -> None:
    run = invoke(["project", "run", "examples/projects/basic_cross_sectional.yaml"])
    assert run.exit_code == 0
    result = invoke(["project", "list", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert any(item["project_name"] == "basic-cross-sectional-example" for item in payload)


def test_causal_study_listing_and_readiness() -> None:
    result = invoke(["causal", "studies", "list"])
    assert result.exit_code == 0
    assert "Causal Studies" in result.output
    study_id = result.output.splitlines()[2].split("|")[0].strip()
    readiness = invoke(["causal", "studies", "readiness", study_id])
    assert readiness.exit_code == 0
    assert "Causal Readiness" in readiness.output


def test_visualization_command() -> None:
    result = invoke(["visualize", "create", "examples/projects/visualization_example.yaml"])
    assert result.exit_code == 0
    assert "Visualization plan" in result.output


def test_report_command() -> None:
    run = invoke(["project", "run", "examples/projects/basic_cross_sectional.yaml"])
    assert run.exit_code == 0
    project_id = _project_id(run.output)
    result = invoke(["report", "generate", project_id])
    assert result.exit_code == 0
    assert "Report already generated" in result.output


def test_system_info() -> None:
    result = invoke(["system", "info", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["polaris_version"]
    assert "python_version" in payload


def test_invalid_path_handling() -> None:
    path = Path("outputs/projects/bad_path.yaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        Path("examples/projects/basic_cross_sectional.yaml")
        .read_text(encoding="utf-8")
        .replace("../wgi/wdi_who_wgi_harmonized_sample.csv", "../../../etc/passwd"),
        encoding="utf-8",
    )
    result = invoke(["project", "validate", path.as_posix()])
    assert result.exit_code == 2
    assert "Path escapes" in result.output


def test_safe_yaml_behavior(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.yaml"
    path.write_text("!!python/object/apply:os.system ['echo unsafe']\n", encoding="utf-8")
    result = invoke(["project", "validate", path.as_posix()])
    assert result.exit_code == 2
    assert "Unable to parse" in result.output


def test_deterministic_config_normalization() -> None:
    args = ["project", "validate", "examples/projects/basic_cross_sectional.yaml", "--json"]
    first = invoke(args)
    second = invoke(args)
    assert json.loads(first.output)["project_id"] == json.loads(second.output)["project_id"]


def test_project_reproduction() -> None:
    run = invoke(["project", "run", "examples/projects/basic_cross_sectional.yaml"])
    assert run.exit_code == 0
    project_id = _project_id(run.output)
    result = invoke(["project", "reproduce", project_id, "--dry-run"])
    assert result.exit_code == 0
    assert "Reproduction Plan" in result.output


def test_debug_error_behavior(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        Path("examples/projects/basic_cross_sectional.yaml")
        .read_text(encoding="utf-8")
        .replace("pearson_correlation", "binary_logistic_regression"),
        encoding="utf-8",
    )
    result = invoke(["project", "run", path.as_posix()])
    assert result.exit_code == 3
    assert "Project failed during ANALYZE" in result.output


def _project_id(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("Project ID:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(output)
