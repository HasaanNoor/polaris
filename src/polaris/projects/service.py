"""Synchronous Phase 13 research-project orchestration service."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from polaris.agents.service import run_domain_agent
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.service import extract_evidence
from polaris.harmonization.export import export_harmonized_dataset
from polaris.harmonization.service import harmonize_datasets
from polaris.ingestion.models import DatasetIngestionResult, IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.literature import build_literature_context, ingest_literature_corpus
from polaris.projects.errors import DatasetResolutionError, ResearchProjectExecutionError
from polaris.projects.models import (
    ArtifactReference,
    DatasetInputKind,
    ErrorMetadata,
    ProjectArtifactKind,
    ProjectStatus,
    ResearchProjectRequest,
    ResearchProjectResult,
    ResearchStage,
    ResearchStageResult,
    ResolvedDataset,
    StageStatus,
)
from polaris.projects.planning import plan_research_project
from polaris.projects.provenance import (
    artifact_ids_from_references,
    build_project_provenance,
    build_reproducibility_summary,
)
from polaris.reasoning.models import ReasoningRequest
from polaris.reasoning.provider import ReasoningProvider
from polaris.reasoning.service import build_reasoning_artifact
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportRequest
from polaris.reporting.service import generate_report
from polaris.synthesis.models import SynthesisRequest
from polaris.synthesis.provider import SynthesisProvider
from polaris.synthesis.service import synthesize_assessment


def run_research_project(
    request: ResearchProjectRequest,
    *,
    registry: DatasetRegistry | None = None,
    reasoning_provider: ReasoningProvider | None = None,
    synthesis_provider: SynthesisProvider | None = None,
) -> ResearchProjectResult:
    """Execute an explicit research project through existing Polaris phase services."""

    plan = plan_research_project(request, registry=registry)
    context = _ExecutionContext(request=request, registry=registry, plan_project_id=plan.project_id)
    stage_results: list[ResearchStageResult] = []
    failed_stage: ResearchStage | None = None
    for stage in plan.stages:
        if failed_stage is not None:
            stage_results.append(ResearchStageResult(stage=stage, status=StageStatus.SKIPPED))
            continue
        started = datetime.now(UTC)
        try:
            _run_stage(
                stage,
                context=context,
                reasoning_provider=reasoning_provider,
                synthesis_provider=synthesis_provider,
            )
            completed = datetime.now(UTC)
            stage_results.append(
                ResearchStageResult(
                    stage=stage,
                    status=StageStatus.COMPLETED,
                    started_at=started,
                    completed_at=completed,
                    input_artifact_ids=context.stage_inputs(stage),
                    output_artifact_ids=context.stage_outputs(stage),
                    provenance_references=context.stage_provenance(stage),
                )
            )
        except Exception as exc:
            failed_stage = stage
            completed = datetime.now(UTC)
            error = ErrorMetadata(
                error_type=type(exc).__name__,
                message=str(exc) or type(exc).__name__,
                details=_error_details(exc),
            )
            stage_results.append(
                ResearchStageResult(
                    stage=stage,
                    status=StageStatus.FAILED,
                    started_at=started,
                    completed_at=completed,
                    input_artifact_ids=context.stage_inputs(stage),
                    output_artifact_ids=context.stage_outputs(stage),
                    error=error,
                )
            )
            if request.execution_settings.raise_on_failure:
                raise ResearchProjectExecutionError(
                    f"research project failed at stage {stage.value}",
                    stage=stage,
                    original_error=exc,
                ) from exc

    status = ProjectStatus.FAILED if failed_stage is not None else ProjectStatus.COMPLETED
    provenance = build_project_provenance(
        project_id=plan.project_id,
        resolved_datasets=context.resolved_datasets,
        ingestion_artifacts=context.ingestion_artifacts,
        harmonized_dataset=context.harmonized_dataset,
        analysis_result=context.analysis_result,
        evidence_artifact=context.evidence_artifact,
        domain_assessments=context.domain_assessments,
        coordinated_assessment=context.coordinated_assessment,
        literature_context=context.literature_context,
        reasoning_artifact=context.reasoning_artifact,
        synthesis_artifact=context.synthesis_artifact,
        research_report=context.research_report,
    )
    artifact_ids = artifact_ids_from_references(context.artifact_references)
    summary = build_reproducibility_summary(
        plan=plan,
        provenance=provenance,
        stage_results=tuple(stage_results),
        artifact_ids=artifact_ids,
    )
    result = ResearchProjectResult(
        project_id=plan.project_id,
        request=request,
        execution_plan=plan,
        overall_status=status,
        stage_results=tuple(stage_results),
        resolved_datasets=context.resolved_datasets,
        ingestion_artifacts=context.ingestion_artifacts,
        harmonized_dataset=context.harmonized_dataset,
        analysis_result=context.analysis_result,
        evidence_artifact=context.evidence_artifact,
        domain_assessments=context.domain_assessments,
        coordinated_assessment=context.coordinated_assessment,
        literature_context=context.literature_context,
        reasoning_artifact=context.reasoning_artifact,
        synthesis_artifact=context.synthesis_artifact,
        research_report=context.research_report,
        project_provenance=provenance,
        reproducibility_summary=summary,
        warnings=context.warnings,
        execution_metadata={"orchestrator": "phase13_in_process"},
    )
    if request.output_directory is not None and request.execution_settings.write_outputs:
        _write_outputs(result)
    return result


class _ExecutionContext:
    def __init__(
        self,
        *,
        request: ResearchProjectRequest,
        registry: DatasetRegistry | None,
        plan_project_id: str,
    ) -> None:
        self.request = request
        self.registry = registry
        self.plan_project_id = plan_project_id
        self.resolved_datasets: tuple[ResolvedDataset, ...] = ()
        self.ingestion_artifacts: tuple[DatasetIngestionResult, ...] = ()
        self.harmonized_dataset = None
        self.analysis_ingestion: DatasetIngestionResult | None = None
        self.analysis_result = None
        self.evidence_artifact = None
        self.domain_assessments = ()
        self.coordinated_assessment = None
        self.literature_context = None
        self.reasoning_artifact = None
        self.synthesis_artifact = None
        self.research_report = None
        self.artifact_references: tuple[ArtifactReference, ...] = ()
        self.warnings: tuple[str, ...] = ()

    def add_artifact(
        self,
        artifact_id: str,
        kind: ProjectArtifactKind,
        path: str | None = None,
    ) -> None:
        self.artifact_references = (
            *self.artifact_references,
            ArtifactReference(artifact_id=artifact_id, kind=kind, path=path),
        )

    def stage_inputs(self, stage: ResearchStage) -> tuple[str, ...]:
        mapping = {
            ResearchStage.INGEST: tuple(dataset.dataset_id for dataset in self.resolved_datasets),
            ResearchStage.HARMONIZE: tuple(
                result.dataset_manifest.dataset_id for result in self.ingestion_artifacts
            ),
            ResearchStage.ANALYZE: (
                (self.analysis_ingestion.dataset_manifest.dataset_id,)
                if self.analysis_ingestion is not None
                else ()
            ),
            ResearchStage.EXTRACT_EVIDENCE: (
                (self.analysis_result.result_id,) if self.analysis_result is not None else ()
            ),
            ResearchStage.RUN_AGENTS: (
                (self.evidence_artifact.artifact_id,) if self.evidence_artifact is not None else ()
            ),
            ResearchStage.COORDINATE: tuple(
                assessment.assessment_id for assessment in self.domain_assessments
            ),
            ResearchStage.SYNTHESIZE: (
                tuple(
                    item
                    for item in (
                        self.coordinated_assessment.coordinated_assessment_id
                        if self.coordinated_assessment is not None
                        else None,
                        self.literature_context.literature_context_id
                        if self.literature_context is not None
                        else None,
                        self.reasoning_artifact.reasoning_id
                        if self.reasoning_artifact is not None
                        else None,
                    )
                    if item is not None
                )
            ),
            ResearchStage.REASON: (
                tuple(
                    item
                    for item in (
                        self.evidence_artifact.artifact_id
                        if self.evidence_artifact is not None
                        else None,
                        self.coordinated_assessment.coordinated_assessment_id
                        if self.coordinated_assessment is not None
                        else None,
                        self.literature_context.literature_context_id
                        if self.literature_context is not None
                        else None,
                    )
                    if item is not None
                )
            ),
            ResearchStage.RETRIEVE_LITERATURE: (
                tuple(
                    item
                    for item in (
                        self.evidence_artifact.artifact_id
                        if self.evidence_artifact is not None
                        else None,
                        self.coordinated_assessment.coordinated_assessment_id
                        if self.coordinated_assessment is not None
                        else None,
                    )
                    if item is not None
                )
            ),
        }
        return mapping.get(stage, ())

    def stage_outputs(self, stage: ResearchStage) -> tuple[str, ...]:
        mapping = {
            ResearchStage.RESOLVE_DATASETS: tuple(
                dataset.dataset_id for dataset in self.resolved_datasets
            ),
            ResearchStage.INGEST: tuple(
                result.dataset_manifest.dataset_id for result in self.ingestion_artifacts
            ),
            ResearchStage.HARMONIZE: (
                (self.harmonized_dataset.harmonized_dataset_id,)
                if self.harmonized_dataset is not None
                else ()
            ),
            ResearchStage.ANALYZE: (
                (self.analysis_result.result_id,) if self.analysis_result is not None else ()
            ),
            ResearchStage.EXTRACT_EVIDENCE: (
                (self.evidence_artifact.artifact_id,) if self.evidence_artifact is not None else ()
            ),
            ResearchStage.RUN_AGENTS: tuple(
                assessment.assessment_id for assessment in self.domain_assessments
            ),
            ResearchStage.COORDINATE: (
                (self.coordinated_assessment.coordinated_assessment_id,)
                if self.coordinated_assessment is not None
                else ()
            ),
            ResearchStage.RETRIEVE_LITERATURE: (
                (self.literature_context.literature_context_id,)
                if self.literature_context is not None
                else ()
            ),
            ResearchStage.REASON: (
                (self.reasoning_artifact.reasoning_id,)
                if self.reasoning_artifact is not None
                else ()
            ),
            ResearchStage.SYNTHESIZE: (
                (self.synthesis_artifact.synthesis_id,)
                if self.synthesis_artifact is not None
                else ()
            ),
            ResearchStage.REPORT: (
                (self.research_report.report.report_id,) if self.research_report is not None else ()
            ),
            ResearchStage.COMPLETE: (self.plan_project_id,),
        }
        return mapping.get(stage, ())

    def stage_provenance(self, stage: ResearchStage) -> tuple[str, ...]:
        return self.stage_inputs(stage) + self.stage_outputs(stage)


def _run_stage(
    stage: ResearchStage,
    *,
    context: _ExecutionContext,
    reasoning_provider: ReasoningProvider | None,
    synthesis_provider: SynthesisProvider | None,
) -> None:
    handlers: dict[ResearchStage, Callable[[], None]] = {
        ResearchStage.RESOLVE_DATASETS: lambda: _resolve_datasets(context),
        ResearchStage.INGEST: lambda: _ingest_inputs(context),
        ResearchStage.HARMONIZE: lambda: _harmonize(context),
        ResearchStage.ANALYZE: lambda: _analyze(context),
        ResearchStage.EXTRACT_EVIDENCE: lambda: _extract(context),
        ResearchStage.RUN_AGENTS: lambda: _run_agents(context),
        ResearchStage.COORDINATE: lambda: _coordinate(context),
        ResearchStage.RETRIEVE_LITERATURE: lambda: _retrieve_literature(context),
        ResearchStage.REASON: lambda: _reason(
            context,
            reasoning_provider=reasoning_provider,
        ),
        ResearchStage.SYNTHESIZE: lambda: _synthesize(
            context,
            synthesis_provider=synthesis_provider,
        ),
        ResearchStage.REPORT: lambda: _report(context),
        ResearchStage.COMPLETE: lambda: None,
    }
    handlers[stage]()


def _resolve_datasets(context: _ExecutionContext) -> None:
    resolved: list[ResolvedDataset] = []
    for item in context.request.dataset_inputs:
        if item.kind is DatasetInputKind.REGISTRY:
            if context.registry is None:
                raise DatasetResolutionError("registry dataset inputs require a DatasetRegistry")
            manifest = context.registry.get(item.dataset_id)
            resolved.append(
                ResolvedDataset(
                    dataset_id=item.dataset_id,
                    input_kind=item.kind,
                    manifest=manifest,
                    source_path=str(item.source_path),
                    expected_checksum=item.expected_checksum,
                )
            )
        elif item.kind is DatasetInputKind.MANIFEST:
            resolved.append(
                ResolvedDataset(
                    dataset_id=item.manifest.dataset_id,
                    input_kind=item.kind,
                    manifest=item.manifest,
                    source_path=str(item.source_path),
                    expected_checksum=item.expected_checksum,
                )
            )
        elif item.kind is DatasetInputKind.INGESTION_ARTIFACT:
            result = item.ingestion_result
            resolved.append(
                ResolvedDataset(
                    dataset_id=result.dataset_manifest.dataset_id,
                    input_kind=item.kind,
                    manifest=result.dataset_manifest,
                    source_path=result.ingestion_request.source_path.as_posix(),
                    source_checksum_sha256=result.checksum_sha256,
                    ingestion_result=result,
                )
            )
        elif item.kind is DatasetInputKind.HARMONIZED_DATASET:
            harmonized = item.harmonized_dataset
            resolved.append(
                ResolvedDataset(
                    dataset_id=harmonized.harmonized_dataset_id,
                    input_kind=item.kind,
                    harmonized_dataset=harmonized,
                    source_checksum_sha256=json.dumps(
                        dict(sorted(harmonized.source_checksums.items())),
                        sort_keys=True,
                    ),
                )
            )
    context.resolved_datasets = tuple(resolved)


def _ingest_inputs(context: _ExecutionContext) -> None:
    ingestion_results: list[DatasetIngestionResult] = []
    for resolved, item in zip(
        context.resolved_datasets,
        context.request.dataset_inputs,
        strict=True,
    ):
        if item.kind is DatasetInputKind.INGESTION_ARTIFACT:
            result = item.ingestion_result
        elif item.kind is DatasetInputKind.HARMONIZED_DATASET:
            context.harmonized_dataset = item.harmonized_dataset
            result = _ingest_harmonized_for_analysis(context, item.harmonized_dataset)
            context.analysis_ingestion = result
        else:
            if resolved.manifest is None or resolved.source_path is None:
                raise DatasetResolutionError(f"dataset {resolved.dataset_id} is not ingestible")
            result = ingest_dataset(
                registry=DatasetRegistry((resolved.manifest,)),
                request=IngestionRequest(
                    dataset_id=resolved.manifest.dataset_id,
                    source_path=Path(resolved.source_path),
                    expected_checksum=resolved.expected_checksum,
                    configuration=item.ingestion_configuration,
                ),
            )
        ingestion_results.append(result)
        context.add_artifact(
            result.dataset_manifest.dataset_id,
            ProjectArtifactKind.INGESTION_RESULT,
        )
    context.ingestion_artifacts = tuple(ingestion_results)
    if context.analysis_ingestion is None and len(ingestion_results) == 1:
        context.analysis_ingestion = ingestion_results[0]


def _harmonize(context: _ExecutionContext) -> None:
    if context.request.harmonization is None:
        return
    harmonized = harmonize_datasets(
        request=context.request.harmonization.to_request(
            ingestion_results=context.ingestion_artifacts,
            geographic_scope=context.request.geographic_scope,
            temporal_scope=context.request.temporal_scope,
        )
    )
    context.harmonized_dataset = harmonized
    context.add_artifact(harmonized.harmonized_dataset_id, ProjectArtifactKind.HARMONIZED_DATASET)
    context.analysis_ingestion = _ingest_harmonized_for_analysis(context, harmonized)


def _ingest_harmonized_for_analysis(
    context: _ExecutionContext,
    harmonized,
) -> DatasetIngestionResult:
    project_root = _project_output_root(context.request, context.plan_project_id)
    artifact_dir = project_root / "artifacts"
    csv_path = artifact_dir / "harmonized_country_year.csv"
    manifest_path = artifact_dir / "harmonized_country_year_manifest.json"
    summary_path = artifact_dir / "harmonization_summary.json"
    manifest = export_harmonized_dataset(
        harmonized=harmonized,
        csv_path=csv_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
    )
    result = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=csv_path,
            expected_checksum=manifest.checksum,
        ),
    )
    context.add_artifact(
        result.dataset_manifest.dataset_id,
        ProjectArtifactKind.INGESTION_RESULT,
        path=str(csv_path),
    )
    return result


def _analyze(context: _ExecutionContext) -> None:
    if context.analysis_ingestion is None:
        raise DatasetResolutionError("no analysis-ready ingestion artifact was produced")
    settings = context.request.execution_settings
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=context.analysis_ingestion,
            statistical_specification=context.request.statistical_specification,
            execution_settings=settings.analysis_execution_settings,
            significance_threshold=settings.significance_threshold,
            confidence_level=settings.confidence_level,
        )
    )
    context.analysis_result = analysis
    context.add_artifact(analysis.result_id, ProjectArtifactKind.ANALYSIS_RESULT)


def _extract(context: _ExecutionContext) -> None:
    if context.analysis_result is None:
        raise DatasetResolutionError("analysis result is required before evidence extraction")
    evidence = extract_evidence(analysis_result=context.analysis_result)
    context.evidence_artifact = evidence
    context.add_artifact(evidence.artifact_id, ProjectArtifactKind.EVIDENCE_ARTIFACT)


def _run_agents(context: _ExecutionContext) -> None:
    if context.evidence_artifact is None:
        raise DatasetResolutionError("evidence artifact is required before agent execution")
    assessments = tuple(
        run_domain_agent(domain=domain, evidence_artifact=context.evidence_artifact)
        for domain in context.request.selected_agents
    )
    context.domain_assessments = assessments
    for assessment in assessments:
        context.add_artifact(assessment.assessment_id, ProjectArtifactKind.AGENT_ASSESSMENT)


def _coordinate(context: _ExecutionContext) -> None:
    coordinated = coordinate_assessments(assessments=context.domain_assessments)
    context.coordinated_assessment = coordinated
    context.add_artifact(
        coordinated.coordinated_assessment_id,
        ProjectArtifactKind.COORDINATED_ASSESSMENT,
    )


def _retrieve_literature(context: _ExecutionContext) -> None:
    if context.request.literature is None:
        return
    if context.evidence_artifact is None:
        raise DatasetResolutionError("evidence is required before literature retrieval")
    config = context.request.literature
    corpus = ingest_literature_corpus(
        config.corpus_path,
        manifest_path=config.manifest_path,
        chunking_config=config.chunking,
    )
    literature_context = build_literature_context(
        evidence_artifact=context.evidence_artifact,
        corpus=corpus,
        research_question=context.request.research_question,
        project_id=context.plan_project_id,
        top_k=config.top_k,
        retrieval_mode=config.retrieval_mode,
    )
    context.literature_context = literature_context
    context.add_artifact(
        literature_context.literature_context_id,
        ProjectArtifactKind.LITERATURE_CONTEXT,
    )


def _reason(
    context: _ExecutionContext,
    *,
    reasoning_provider: ReasoningProvider | None,
) -> None:
    if context.evidence_artifact is None or context.coordinated_assessment is None:
        raise DatasetResolutionError("evidence and coordination are required before reasoning")
    config = context.request.reasoning
    reasoning = build_reasoning_artifact(
        request=ReasoningRequest(
            research_question=context.request.research_question.raw_text,
            evidence_artifact=context.evidence_artifact,
            coordinated_assessment=context.coordinated_assessment,
            literature_context=context.literature_context,
            mode=config.mode,
            requested_categories=config.categories,
            max_statement_count=config.max_statements,
            provider_config=config.provider_config,
            model_identifier=config.model_identifier,
            strictness=config.strictness,
        ),
        provider=reasoning_provider,
    )
    context.reasoning_artifact = reasoning
    context.add_artifact(reasoning.reasoning_id, ProjectArtifactKind.REASONING_ARTIFACT)


def _synthesize(
    context: _ExecutionContext,
    *,
    synthesis_provider: SynthesisProvider | None,
) -> None:
    if context.coordinated_assessment is None or context.evidence_artifact is None:
        raise DatasetResolutionError("coordination and evidence are required before synthesis")
    config = context.request.synthesis
    synthesis = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=context.coordinated_assessment,
            evidence_artifact=context.evidence_artifact,
            literature_context=context.literature_context,
            reasoning_artifact=context.reasoning_artifact,
            mode=config.mode,
            provider_config=config.provider_config,
            model_identifier=config.model_identifier,
            allow_deterministic_fallback=config.allow_deterministic_fallback,
            max_synthesis_length=config.max_synthesis_length,
        ),
        provider=synthesis_provider,
    )
    context.synthesis_artifact = synthesis
    context.add_artifact(synthesis.synthesis_id, ProjectArtifactKind.SYNTHESIS_ARTIFACT)


def _report(context: _ExecutionContext) -> None:
    if (
        context.synthesis_artifact is None
        or context.coordinated_assessment is None
        or context.evidence_artifact is None
        or context.analysis_result is None
        or context.analysis_ingestion is None
    ):
        raise DatasetResolutionError("all upstream artifacts are required before report generation")
    config = context.request.report
    report = generate_report(
        request=ReportRequest(
            synthesis_artifact=context.synthesis_artifact,
            coordinated_assessment=context.coordinated_assessment,
            evidence_artifact=context.evidence_artifact,
            analysis_result=context.analysis_result,
            ingestion_result=context.analysis_ingestion,
            research_question=context.request.research_question,
            literature_context=context.literature_context,
            reasoning_artifact=context.reasoning_artifact,
            dataset_manifest=context.analysis_ingestion.dataset_manifest,
            output_format=config.output_format,
            report_title=config.report_title,
            report_subtitle=config.report_subtitle,
            author=config.author,
            organization=config.organization,
        )
    )
    context.research_report = report
    context.add_artifact(report.report.report_id, ProjectArtifactKind.RESEARCH_REPORT)


def _project_output_root(request: ResearchProjectRequest, project_id: str) -> Path:
    base = request.output_directory or Path("outputs")
    return base / project_id


def _write_outputs(result: ResearchProjectResult) -> None:
    root = _project_output_root(result.request, result.project_id)
    report_dir = root / "report"
    root.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    (root / "project.json").write_text(
        result.model_dump_json(
            indent=2,
            exclude={
                "ingestion_artifacts",
                "harmonized_dataset",
                "analysis_result",
                "evidence_artifact",
                "domain_assessments",
                "coordinated_assessment",
                "reasoning_artifact",
                "synthesis_artifact",
                "research_report",
            },
        ),
        encoding="utf-8",
    )
    (root / "execution-plan.json").write_text(
        result.execution_plan.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (root / "reproducibility-summary.json").write_text(
        result.reproducibility_summary.model_dump_json(indent=2),
        encoding="utf-8",
    )
    if result.research_report is not None:
        rendered = result.research_report.rendered_content
        extension = result.research_report.output_format.value
        content = (
            rendered
            if rendered is not None
            else result.research_report.report.model_dump_json(indent=2)
        )
        (report_dir / f"report.{extension}").write_text(content, encoding="utf-8")


def _error_details(exc: Exception) -> dict[str, str]:
    details: dict[str, str] = {}
    for key in ("dataset_id", "source_path", "method", "row_number", "column_name"):
        value = getattr(exc, key, None)
        if value is not None:
            details[key] = str(value)
    return details
