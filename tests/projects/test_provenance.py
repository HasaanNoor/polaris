from pathlib import Path

from polaris.projects import plan_research_project, run_research_project
from tests.projects.helpers import harmonized_project, single_manifest_project


def test_project_provenance_links_artifacts_and_source_checksums(tmp_path: Path) -> None:
    result = run_research_project(harmonized_project(tmp_path))
    provenance = result.project_provenance

    assert provenance.source_checksums["wdi"]
    assert provenance.source_checksums["who"]
    assert provenance.analysis_artifact_id == result.analysis_result.result_id
    assert provenance.evidence_artifact_id == result.evidence_artifact.artifact_id
    assert provenance.report_id == result.research_report.report.report_id


def test_timestamps_excluded_from_deterministic_project_id(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path)

    first = run_research_project(request)
    second = run_research_project(request)

    assert first.project_id == second.project_id == plan_research_project(request).project_id
    assert (
        first.project_provenance.execution_timestamp
        != second.project_provenance.execution_timestamp
    )
