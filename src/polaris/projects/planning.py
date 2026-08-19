"""Deterministic execution planning for Phase 13 projects."""

from __future__ import annotations

from polaris.analysis.compatibility import resolve_procedure
from polaris.ingestion.loader import calculate_sha256
from polaris.projects.errors import DatasetResolutionError
from polaris.projects.models import (
    DatasetInputKind,
    ResearchExecutionPlan,
    ResearchProjectRequest,
    ResearchStage,
    deterministic_project_id,
)
from polaris.registry import DatasetRegistry


def plan_research_project(
    request: ResearchProjectRequest,
    *,
    registry: DatasetRegistry | None = None,
) -> ResearchExecutionPlan:
    dataset_refs = tuple(_dataset_ref(item, registry=registry) for item in request.dataset_inputs)
    required_datasets = tuple(ref["dataset_id"] for ref in dataset_refs)
    harmonization_required = _requires_harmonization(request)
    stages = (
        ResearchStage.RESOLVE_DATASETS,
        ResearchStage.INGEST,
        *(() if not harmonization_required else (ResearchStage.HARMONIZE,)),
        ResearchStage.ANALYZE,
        ResearchStage.EXTRACT_EVIDENCE,
        ResearchStage.RUN_AGENTS,
        ResearchStage.COORDINATE,
        *(() if request.literature is None else (ResearchStage.RETRIEVE_LITERATURE,)),
        *(() if not request.reasoning.enabled else (ResearchStage.REASON,)),
        ResearchStage.SYNTHESIZE,
        ResearchStage.REPORT,
        ResearchStage.COMPLETE,
    )
    procedure = resolve_procedure(request.statistical_specification)
    project_id = deterministic_project_id(
        {
            "schema_version": request.schema_version,
            "project_name": request.project_name,
            "research_question": request.research_question.model_dump(mode="json"),
            "datasets": dataset_refs,
            "harmonization": (
                request.harmonization.model_dump(mode="json") if request.harmonization else None
            ),
            "statistical_specification": request.statistical_specification.model_dump(mode="json"),
            "causal_specification": (
                request.causal_specification.model_dump(mode="json")
                if request.causal_specification is not None
                else None
            ),
            "selected_agents": [agent.value for agent in request.selected_agents],
            "reasoning": request.reasoning.model_dump(mode="json"),
            "synthesis": request.synthesis.model_dump(mode="json"),
            "report": request.report.model_dump(mode="json"),
            "literature": (
                request.literature.model_dump(mode="json") if request.literature else None
            ),
            "geographic_scope": (
                request.geographic_scope.model_dump(mode="json")
                if request.geographic_scope is not None
                else None
            ),
            "temporal_scope": (
                request.temporal_scope.model_dump(mode="json")
                if request.temporal_scope is not None
                else None
            ),
            "execution_settings": request.execution_settings.model_dump(
                mode="json", exclude={"raise_on_failure", "write_outputs"}
            ),
        }
    )
    return ResearchExecutionPlan(
        project_id=project_id,
        required_datasets=required_datasets,
        stages=stages,
        ingestion_dataset_ids=tuple(
            ref["dataset_id"]
            for ref, item in zip(dataset_refs, request.dataset_inputs, strict=True)
            if item.kind is not DatasetInputKind.HARMONIZED_DATASET
        ),
        harmonization_required=harmonization_required,
        statistical_analysis_step=procedure.value,
        selected_agents=request.selected_agents,
        synthesis_step=request.synthesis.mode,
        report_step=request.report.output_format,
    )


def _requires_harmonization(request: ResearchProjectRequest) -> bool:
    return len(request.dataset_inputs) > 1 and request.harmonization is not None


def _dataset_ref(item, *, registry: DatasetRegistry | None) -> dict[str, object]:
    if item.kind is DatasetInputKind.REGISTRY:
        if registry is None:
            raise DatasetResolutionError("registry dataset inputs require a DatasetRegistry")
        manifest = registry.get(item.dataset_id)
        return {
            "kind": item.kind.value,
            "dataset_id": item.dataset_id,
            "manifest_checksum": manifest.checksum,
            "source_path": str(item.source_path),
            "source_checksum": item.expected_checksum or _file_checksum(item.source_path),
        }
    if item.kind is DatasetInputKind.MANIFEST:
        return {
            "kind": item.kind.value,
            "dataset_id": item.manifest.dataset_id,
            "manifest_checksum": item.manifest.checksum,
            "source_path": str(item.source_path),
            "source_checksum": item.expected_checksum or _file_checksum(item.source_path),
        }
    if item.kind is DatasetInputKind.INGESTION_ARTIFACT:
        result = item.ingestion_result
        return {
            "kind": item.kind.value,
            "dataset_id": result.dataset_manifest.dataset_id,
            "source_checksum": result.checksum_sha256,
        }
    if item.kind is DatasetInputKind.HARMONIZED_DATASET:
        harmonized = item.harmonized_dataset
        return {
            "kind": item.kind.value,
            "dataset_id": harmonized.harmonized_dataset_id,
            "source_checksums": dict(sorted(harmonized.source_checksums.items())),
            "harmonization_ruleset": harmonized.ruleset_version,
        }
    raise DatasetResolutionError(f"unsupported dataset input kind: {item.kind}")


def _file_checksum(path) -> str | None:
    try:
        return calculate_sha256(path)
    except Exception:
        return None
