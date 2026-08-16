from __future__ import annotations

import json

import pytest

from polaris.mcp.config import MCPServerConfig
from polaris.mcp.errors import MCPNotFoundError, MCPSafetyError
from polaris.mcp.resources import MCPResourceStore


def test_dataset_resource_listing_and_manifest_are_deterministic():
    store = MCPResourceStore()

    listing = store.read_resource("polaris://datasets")
    again = store.read_resource("polaris://datasets")
    manifest = store.read_resource("polaris://datasets/world_bank_wdi_illustrative/manifest")

    assert listing == again
    assert "world_bank_wdi_illustrative" in {item["dataset_id"] for item in listing["datasets"]}
    assert manifest["dataset_id"] == "world_bank_wdi_illustrative"
    assert manifest["variables"]


def test_variable_catalog_resources_cover_curated_providers():
    store = MCPResourceStore()

    who = store.read_resource("polaris://catalogs/who/variables")
    wgi = store.read_resource("polaris://catalogs/wgi/variables")
    unesco = store.read_resource("polaris://catalogs/unesco/variables")
    wdi = store.read_resource("polaris://catalogs/wdi/variables")

    assert who["integrated"]
    assert who["deferred"]
    assert wgi["integrated"]
    assert "uncertainty_metadata" in wgi
    assert unesco["integrated"]
    assert wdi["variables"]


def test_project_report_reasoning_evaluation_and_provenance_resources(tmp_path):
    project_root = tmp_path / "examples" / "project_abc"
    report_root = project_root / "report"
    report_root.mkdir(parents=True)
    (project_root / "project.json").write_text(
        json.dumps({"project_id": "project_abc", "stage_results": [], "project_provenance": {}}),
        encoding="utf-8",
    )
    (report_root / "report.markdown").write_text("# Report\n", encoding="utf-8")
    (tmp_path / "examples" / "reasoning_artifact.json").write_text(
        json.dumps({"reasoning_id": "reasoning_fixture", "schema_version": "1.0.0"}),
        encoding="utf-8",
    )
    (tmp_path / "examples" / "evaluation_fixture.json").write_text(
        json.dumps({"evaluation_id": "evaluation_fixture", "schema_version": "1.0.0"}),
        encoding="utf-8",
    )
    store = MCPResourceStore(
        MCPServerConfig(
            allowed_artifact_roots=(tmp_path / "examples",),
            allowed_project_output_directory=tmp_path / "examples",
        )
    )

    assert store.read_resource("polaris://projects/project_abc")["project_id"] == "project_abc"
    assert store.read_resource("polaris://reports/project_abc")["content"] == "# Report\n"
    assert (
        store.read_resource("polaris://reasoning/reasoning_fixture")["reasoning_id"]
        == "reasoning_fixture"
    )
    assert (
        store.read_resource("polaris://evaluations/evaluation_fixture")["evaluation_id"]
        == "evaluation_fixture"
    )
    assert (
        store.read_resource("polaris://provenance/project_abc")["artifact_type"]
        == "research_project"
    )


def test_unknown_resource_and_disallowed_paths_are_rejected():
    store = MCPResourceStore()

    with pytest.raises(MCPNotFoundError):
        store.read_resource("polaris://unknown")

    with pytest.raises(MCPSafetyError):
        store.config.resolve_under_allowed_roots("../data/raw/provider.csv")
