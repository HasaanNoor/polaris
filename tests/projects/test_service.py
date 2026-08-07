from pathlib import Path

from polaris.projects import run_research_project
from polaris.projects.models import ProjectStatus, ResearchStage
from tests.projects.helpers import harmonized_project, single_manifest_project


def test_successful_single_dataset_project(tmp_path: Path) -> None:
    result = run_research_project(single_manifest_project(tmp_path))

    assert result.overall_status is ProjectStatus.COMPLETED
    assert result.analysis_result is not None
    assert result.evidence_artifact is not None
    assert len(result.domain_assessments) == 2
    assert result.coordinated_assessment is not None
    assert result.synthesis_artifact is not None
    assert result.research_report is not None
    assert result.reproducibility_summary.reproducibility_ready is True


def test_successful_harmonized_multi_provider_project(tmp_path: Path) -> None:
    result = run_research_project(harmonized_project(tmp_path))

    assert result.overall_status is ProjectStatus.COMPLETED
    assert result.harmonized_dataset is not None
    assert result.analysis_result is not None
    assert result.project_provenance.harmonization_artifact_id == (
        result.harmonized_dataset.harmonized_dataset_id
    )
    assert (tmp_path / "outputs" / result.project_id / "reproducibility-summary.json").exists()
    assert ResearchStage.HARMONIZE in result.reproducibility_summary.completed_stages


def test_every_stage_produces_expected_artifact(tmp_path: Path) -> None:
    result = run_research_project(single_manifest_project(tmp_path))
    outputs = {stage.stage: stage.output_artifact_ids for stage in result.stage_results}

    assert outputs[ResearchStage.ANALYZE] == (result.analysis_result.result_id,)
    assert outputs[ResearchStage.EXTRACT_EVIDENCE] == (result.evidence_artifact.artifact_id,)
    assert outputs[ResearchStage.REPORT] == (result.research_report.report.report_id,)
