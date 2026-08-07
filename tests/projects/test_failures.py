from pathlib import Path

from polaris.projects import ManifestDatasetInput, ResearchProjectRequest, run_research_project
from polaris.projects.models import ProjectStatus, ResearchStage, StageStatus
from polaris.schemas.common import (
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
)
from tests.projects.helpers import single_manifest_project, specification


def test_dataset_resolution_failure_records_stage_and_skips_downstream(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path)
    bad_input = ManifestDatasetInput(
        manifest=request.dataset_inputs[0].manifest,  # type: ignore[attr-defined]
        source_path=tmp_path / "missing.csv",
    )
    bad_request = ResearchProjectRequest.model_validate(
        {**request.model_dump(mode="python"), "dataset_inputs": (bad_input,)}
    )

    result = run_research_project(bad_request)

    assert result.overall_status is ProjectStatus.FAILED
    failed = next(stage for stage in result.stage_results if stage.status is StageStatus.FAILED)
    assert failed.stage is ResearchStage.INGEST
    assert failed.error is not None
    assert all(
        stage.status is StageStatus.SKIPPED
        for stage in result.stage_results
        if result.execution_plan.stages.index(stage.stage)
        > result.execution_plan.stages.index(ResearchStage.INGEST)
    )


def test_analysis_failure_retains_completed_ingestion(tmp_path: Path) -> None:
    request = single_manifest_project(tmp_path)
    bad_spec = specification(
        procedure=StatisticalProcedure.PEARSON_CORRELATION,
        analysis_type=StatisticalAnalysisType.CORRELATION,
        model_family=StatisticalModelFamily.NONE,
        outcome="y",
        exposures=("missing_x",),
    )
    bad_request = ResearchProjectRequest.model_validate(
        {**request.model_dump(mode="python"), "statistical_specification": bad_spec}
    )

    result = run_research_project(bad_request)

    assert result.overall_status is ProjectStatus.FAILED
    assert result.ingestion_artifacts
    failed_stage = next(
        stage for stage in result.stage_results if stage.status is StageStatus.FAILED
    )
    assert failed_stage.stage is ResearchStage.ANALYZE
