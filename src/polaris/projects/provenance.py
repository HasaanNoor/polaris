"""Project-level provenance aggregation for Phase 13."""

from __future__ import annotations

from datetime import UTC, datetime

from polaris.projects.models import (
    ArtifactReference,
    ProjectProvenance,
    ReproducibilitySummary,
    ResearchExecutionPlan,
    ResearchStage,
    ResearchStageResult,
)


def artifact_ids_from_references(references: tuple[ArtifactReference, ...]) -> tuple[str, ...]:
    return tuple(sorted(reference.artifact_id for reference in references))


def build_project_provenance(
    *,
    project_id: str,
    resolved_datasets,
    ingestion_artifacts,
    harmonized_dataset,
    analysis_result,
    causal_analysis_result=None,
    robustness_result=None,
    evidence_artifact,
    domain_assessments,
    coordinated_assessment,
    synthesis_artifact,
    research_report,
    literature_context=None,
    reasoning_artifact=None,
    visualization_artifacts=(),
) -> ProjectProvenance:
    source_checksums = {
        result.dataset_manifest.dataset_id: result.checksum_sha256 for result in ingestion_artifacts
    }
    if harmonized_dataset is not None:
        source_checksums.update(dict(harmonized_dataset.source_checksums))
    return ProjectProvenance(
        project_id=project_id,
        dataset_ids=tuple(sorted(dataset.dataset_id for dataset in resolved_datasets)),
        source_checksums=dict(sorted(source_checksums.items())),
        manifest_ids=tuple(
            sorted(
                dataset.manifest.dataset_id
                for dataset in resolved_datasets
                if dataset.manifest is not None
            )
        ),
        harmonization_artifact_id=(
            harmonized_dataset.harmonized_dataset_id if harmonized_dataset is not None else None
        ),
        analysis_artifact_id=analysis_result.result_id if analysis_result is not None else None,
        causal_analysis_artifact_id=(
            causal_analysis_result.causal_analysis_id
            if causal_analysis_result is not None
            else None
        ),
        robustness_analysis_artifact_id=(
            robustness_result.robustness_analysis_id if robustness_result is not None else None
        ),
        visualization_artifact_ids=tuple(
            sorted(artifact.visualization_id for artifact in visualization_artifacts)
        ),
        evidence_artifact_id=(
            evidence_artifact.artifact_id if evidence_artifact is not None else None
        ),
        agent_assessment_ids=tuple(
            sorted(assessment.assessment_id for assessment in domain_assessments)
        ),
        coordination_id=(
            coordinated_assessment.coordinated_assessment_id
            if coordinated_assessment is not None
            else None
        ),
        literature_context_id=(
            literature_context.literature_context_id if literature_context is not None else None
        ),
        reasoning_id=reasoning_artifact.reasoning_id if reasoning_artifact is not None else None,
        synthesis_id=synthesis_artifact.synthesis_id if synthesis_artifact is not None else None,
        report_id=research_report.report.report_id if research_report is not None else None,
        execution_timestamp=datetime.now(UTC),
    )


def build_reproducibility_summary(
    *,
    plan: ResearchExecutionPlan,
    provenance: ProjectProvenance,
    stage_results: tuple[ResearchStageResult, ...],
    artifact_ids: tuple[str, ...],
) -> ReproducibilitySummary:
    completed = tuple(
        result.stage for result in stage_results if result.status.value == "completed"
    )
    failed = next(
        (result.stage for result in stage_results if result.status.value == "failed"),
        None,
    )
    return ReproducibilitySummary(
        project_id=plan.project_id,
        source_dataset_count=len(provenance.dataset_ids),
        source_checksums=provenance.source_checksums,
        harmonization_used=plan.harmonization_required
        or provenance.harmonization_artifact_id is not None,
        statistical_method=plan.statistical_analysis_step,
        selected_agents=plan.selected_agents,
        synthesis_mode=plan.synthesis_step,
        report_format=plan.report_step,
        completed_stages=completed,
        failed_stage=failed,
        artifact_ids=artifact_ids,
        reproducibility_ready=failed is None and ResearchStage.COMPLETE in completed,
    )
