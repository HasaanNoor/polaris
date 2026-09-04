"""Research project workflow commands."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Annotated, Any

import typer

from polaris.cli.config import (
    load_project_config,
    normalized_config,
    validate_project_config,
)
from polaris.cli.errors import CLIExecutionError, CLIResourceNotFoundError
from polaris.cli.output import echo, json_echo, progress
from polaris.cli.system import DEFAULT_OUTPUT_ROOT, dataset_registry
from polaris.projects import plan_research_project, run_research_project
from polaris.projects.models import ProjectStatus, ResearchProjectResult

app = typer.Typer(
    help="Validate, run, inspect, and reproduce research projects.",
    no_args_is_help=True,
)


@app.command("validate")
def validate(
    config: Path,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress human-readable output."),
) -> None:
    loaded = load_project_config(config)
    request = validate_project_config(loaded, config_path=config)
    plan = plan_research_project(request, registry=dataset_registry())
    payload = _validation_payload(loaded, plan.project_id)
    if json_output:
        json_echo(payload)
        return
    if quiet:
        return
    echo("Configuration valid.")
    echo(f"Project: {loaded.project.name}")
    echo(f"Datasets: {len(loaded.datasets)}")
    echo(f"Analysis: {loaded.analysis.procedure.value}")
    echo(f"Agents: {', '.join(agent.value for agent in loaded.agents)}")
    echo(f"Reasoning: {'enabled' if loaded.reasoning.enabled else 'disabled'}")
    echo(f"Visualizations: {'enabled' if bool(loaded.visualizations) else 'disabled'}")
    echo(f"Reports: {', '.join(item.value for item in loaded.reporting.formats)}")


@app.command("run")
def run(
    config: Path,
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and show plan only."),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Reuse only compatible deterministic outputs.",
    ),
    debug: bool = typer.Option(False, "--debug", help="Raise developer traceback on failure."),
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress human-readable output."),
) -> None:
    loaded = load_project_config(config)
    request = validate_project_config(loaded, config_path=config)
    plan = plan_research_project(request, registry=dataset_registry())
    if dry_run:
        payload = {"project_id": plan.project_id, "stages": [stage.value for stage in plan.stages]}
        if json_output:
            json_echo(payload)
            return
        echo("Execution Plan", quiet=quiet)
        for index, stage in enumerate(plan.stages, start=1):
            echo(f"{index}. {stage.value.upper()}", quiet=quiet)
        return
    if resume:
        _verify_reproducible_run(plan.project_id, request.output_directory or DEFAULT_OUTPUT_ROOT)
    progress("Polaris Research Project", quiet=quiet, json_output=json_output)
    progress("[OK] Configuration validated", quiet=quiet, json_output=json_output)
    try:
        result = run_research_project(request, registry=dataset_registry())
    except Exception as exc:
        if debug:
            raise
        raise CLIExecutionError(f"Project execution failed: {exc}") from exc
    _write_cli_metadata(result, loaded, config)
    if result.overall_status is not ProjectStatus.COMPLETED:
        failed = next((stage for stage in result.stage_results if stage.error is not None), None)
        message = "Project failed"
        if failed and failed.error:
            message = (
                f"Project failed during {failed.stage.value.upper()}.\n"
                f"Reason: {failed.error.message}"
            )
        raise CLIExecutionError(message, suggestion="Run again with --debug for developer details.")
    for stage in result.stage_results:
        progress(
            f"[OK] {stage.stage.value.replace('_', ' ').title()}",
            quiet=quiet,
            json_output=json_output,
        )
    payload = _project_summary(result)
    if json_output:
        json_echo(payload)
        return
    echo(f"Project ID: {result.project_id}", quiet=quiet)
    echo(f"Output: {_project_dir(result.project_id, request.output_directory)}", quiet=quiet)


@app.command("inspect")
def inspect(
    project_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    payload = _load_project(project_id)
    if json_output:
        json_echo(payload)
        return
    request = payload["request"]
    echo("Project")
    echo("-------")
    echo(f"ID: {payload['project_id']}")
    echo(f"Name: {request['project_name']}")
    echo(f"Question: {request['research_question']['raw_text']}")
    echo(f"Status: {payload['overall_status']}")
    echo(f"Datasets: {', '.join(payload['execution_plan']['required_datasets'])}")
    echo(f"Analysis: {payload['execution_plan']['statistical_analysis_step']}")
    echo(f"Agents: {', '.join(payload['execution_plan']['selected_agents'])}")
    visualization_count = len(
        payload.get("project_provenance", {}).get("visualization_artifact_ids", [])
    )
    echo(f"Visualizations: {visualization_count}")
    report_id = payload.get("project_provenance", {}).get("report_id")
    echo(f"Report: {report_id or 'not generated'}")
    warnings = payload.get("warnings") or []
    if warnings:
        echo("Warnings: " + "; ".join(warnings))


@app.command("list")
def list_projects(
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    projects = []
    for project_file in sorted(DEFAULT_OUTPUT_ROOT.glob("project_*/project.json")):
        try:
            payload = json.loads(project_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        question = payload["request"]["research_question"]["raw_text"]
        projects.append(
            {
                "project_id": payload["project_id"],
                "project_name": payload["request"]["project_name"],
                "research_question": question[:80],
                "analysis_type": payload["execution_plan"]["statistical_analysis_step"],
                "status": payload["overall_status"],
            }
        )
    if json_output:
        json_echo(projects)
        return
    echo("Projects")
    echo("--------")
    for item in projects:
        echo(
            f"{item['project_id']} | {item['project_name']} | "
            f"{item['analysis_type']} | {item['status']}"
        )


@app.command("init")
def init(
    output: Annotated[
        Path,
        typer.Argument(help="Configuration file to create."),
    ] = Path("polaris_project.yaml"),
    template: str = typer.Option(
        "basic",
        "--template",
        help="basic, panel, causal, or visualization.",
    ),
) -> None:
    if output.exists():
        raise CLIResourceNotFoundError(f"Refusing to overwrite existing file: {output}")
    source = Path("examples/projects") / _template_name(template)
    if not source.exists():
        raise CLIResourceNotFoundError(f"Unknown template: {template}")
    shutil.copyfile(source, output)
    echo(f"Created {output}")


@app.command("reproduce")
def reproduce(
    project_id: str,
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate stored config and show plan only.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    root = DEFAULT_OUTPUT_ROOT / project_id
    config_file = root / "normalized-config.json"
    if not config_file.exists():
        raise CLIResourceNotFoundError(f"Stored normalized configuration not found: {config_file}")
    config = load_project_config(config_file)
    request = validate_project_config(config, config_path=config_file)
    plan = plan_research_project(request, registry=dataset_registry())
    if plan.project_id != project_id:
        raise CLIExecutionError(
            "Stored configuration no longer resolves to the requested project ID."
        )
    if dry_run:
        payload = {"project_id": project_id, "stages": [stage.value for stage in plan.stages]}
        if json_output:
            json_echo(payload)
            return
        echo("Reproduction Plan")
        for index, stage in enumerate(plan.stages, start=1):
            echo(f"{index}. {stage.value.upper()}")
        return
    result = run_research_project(request, registry=dataset_registry())
    _write_cli_metadata(result, config, config_file)
    if json_output:
        json_echo(_project_summary(result))
    else:
        echo(f"Reproduced project: {result.project_id}")


def _validation_payload(config, project_id: str) -> dict[str, Any]:
    return {
        "valid": True,
        "project_id": project_id,
        "project": config.project.name,
        "datasets": [item.dataset_id for item in config.datasets],
        "analysis": config.analysis.procedure.value,
        "agents": [item.value for item in config.agents],
        "reasoning": config.reasoning.model_dump(mode="json"),
        "reports": [item.value for item in config.reporting.formats],
    }


def _write_cli_metadata(result: ResearchProjectResult, config, config_path: Path) -> None:
    root = _project_dir(result.project_id, result.request.output_directory)
    root.mkdir(parents=True, exist_ok=True)
    normalized = normalized_config(config)
    for dataset in normalized.get("datasets", []):
        for key in ("manifest_path", "source_path"):
            if key in dataset:
                path = Path(dataset[key])
                if not path.is_absolute():
                    dataset[key] = str((config_path.parent / path).resolve())
    (root / "normalized-config.json").write_text(
        json.dumps(normalized, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest = {
        "project_id": result.project_id,
        "normalized_configuration": normalized,
        "dataset_ids": list(result.reproducibility_summary.source_checksums.keys()),
        "dataset_versions": {
            item.dataset_id: item.manifest.source_version
            for item in result.resolved_datasets
            if item.manifest is not None
        },
        "checksums": result.reproducibility_summary.source_checksums,
        "analysis_specification": result.request.statistical_specification.model_dump(mode="json"),
        "agent_selection": [item.value for item in result.request.selected_agents],
        "reasoning_mode": result.request.reasoning.mode.value,
        "visualization_specifications": result.request.visualization.model_dump(mode="json"),
        "report_formats": [result.request.report.output_format.value],
        "software_version": result.project_provenance.software_version,
        "schema_versions": {
            "cli_config": normalized.get("schema_version"),
            "orchestration": result.project_provenance.orchestration_schema_version,
        },
        "source_config_path": str(config_path),
    }
    (root / "reproducibility-manifest.json").write_text(
        json.dumps(_jsonable(manifest), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _load_project(project_id: str) -> dict[str, Any]:
    path = DEFAULT_OUTPUT_ROOT / project_id / "project.json"
    if not path.exists():
        raise CLIResourceNotFoundError(f"Project not found: {project_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _project_summary(result: ResearchProjectResult) -> dict[str, Any]:
    return {
        "project_id": result.project_id,
        "status": result.overall_status.value,
        "output": str(_project_dir(result.project_id, result.request.output_directory)),
        "stages": [stage.model_dump(mode="json") for stage in result.stage_results],
    }


def _project_dir(project_id: str, output_root: Path | None) -> Path:
    return (output_root or DEFAULT_OUTPUT_ROOT) / project_id


def _verify_reproducible_run(project_id: str, output_root: Path) -> None:
    manifest = output_root / project_id / "reproducibility-manifest.json"
    if not manifest.exists():
        raise CLIResourceNotFoundError(f"No compatible stored manifest for resume: {manifest}")


def _template_name(template: str) -> str:
    names = {
        "basic": "basic_cross_sectional.yaml",
        "panel": "governance_health_panel.yaml",
        "causal": "causal_template.yaml",
        "visualization": "visualization_example.yaml",
    }
    return names.get(template, "")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
