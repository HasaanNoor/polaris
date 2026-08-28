"""MCP tool handlers that delegate to existing Polaris public APIs."""

from __future__ import annotations

from typing import Any

from polaris.analysis.causal.service import run_causal_analysis as core_run_causal_analysis
from polaris.analysis.robustness.service import analyze_robustness as core_analyze_robustness
from polaris.analysis.service import run_analysis as core_run_analysis
from polaris.causal_studies.models import CausalStudySearchQuery
from polaris.causal_studies.service import (
    assess_causal_study_readiness as core_assess_causal_study_readiness,
)
from polaris.causal_studies.service import (
    inspect_causal_study as core_inspect_causal_study,
)
from polaris.causal_studies.service import (
    list_causal_studies as core_list_causal_studies,
)
from polaris.evaluation.service import evaluate_reasoning as core_evaluate_reasoning
from polaris.harmonization.service import harmonize_datasets
from polaris.literature.ingestion import ingest_literature_corpus
from polaris.literature.retrieval import retrieve_literature as core_retrieve_literature
from polaris.mcp.adapters import (
    EvaluateReasoningRequest,
    GetReportRequest,
    InspectDatasetRequest,
    IntegrateDatasetsRequest,
    ListDatasetsRequest,
    RetrieveLiteratureRequest,
    RunAnalysisRequest,
    RunCausalAnalysisRequest,
    RunReasoningRequest,
    RunResearchProjectRequest,
    RunRobustnessAnalysisRequest,
    artifact_reference,
)
from polaris.mcp.config import MCPServerConfig
from polaris.mcp.errors import MCPSafetyError, PolarisMCPError, translate_exception
from polaris.mcp.resources import MCPResourceStore, inspect_manifest
from polaris.mcp.serialization import bounded_payload, json_compatible
from polaris.projects.service import run_research_project as core_run_research_project
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.service import build_reasoning_artifact

TOOL_NAMES = (
    "list_datasets",
    "inspect_dataset",
    "run_analysis",
    "run_causal_analysis",
    "run_robustness_analysis",
    "list_causal_studies",
    "inspect_causal_study",
    "assess_causal_study_readiness",
    "integrate_datasets",
    "run_research_project",
    "retrieve_literature",
    "run_reasoning",
    "evaluate_reasoning",
    "get_report",
)


class MCPToolService:
    """Validated tool surface for Polaris MCP clients."""

    def __init__(
        self,
        *,
        config: MCPServerConfig | None = None,
        resources: MCPResourceStore | None = None,
    ) -> None:
        self.config = config or MCPServerConfig()
        self.resources = resources or MCPResourceStore(self.config)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in TOOL_NAMES:
            return _error_payload(PolarisMCPError(f"unknown MCP tool: {name}", code="unknown_tool"))
        try:
            handler = getattr(self, name)
            return handler(arguments or {})
        except Exception as exc:
            return _error_payload(translate_exception(exc, stage=name))

    def list_datasets(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = ListDatasetsRequest.model_validate(arguments)
        results = self.resources.registry.search(request.to_search_query())
        if request.collection_type is not None:
            results = tuple(
                result for result in results if result.collection_type is request.collection_type
            )
        payload = [
            {
                "dataset_id": result.dataset_id,
                "title": result.title,
                "provider": result.manifest.provider,
                "collection_type": result.collection_type.value,
                "matched_variable_ids": result.matched_variable_ids,
                "match_reasons": result.match_reasons,
                "warnings": result.warnings,
                "temporal_overlap": result.temporal_overlap,
                "geographic_match": result.geographic_match,
                "resource_uri": f"polaris://datasets/{result.dataset_id}",
            }
            for result in results
        ]
        return {"datasets": json_compatible(payload)}

    def inspect_dataset(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = InspectDatasetRequest.model_validate(arguments)
        manifest = self.resources.registry.get(request.dataset_id)
        return inspect_manifest(
            manifest,
            self.resources.registry.collection_type(request.dataset_id),
        )

    def run_analysis(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RunAnalysisRequest.model_validate(arguments)
        result = core_run_analysis(request=request.to_core())
        reference = artifact_reference(
            artifact_id=result.result_id,
            artifact_type="analysis_result",
            resource_uri=f"polaris://provenance/{result.result_id}",
            schema_version=result.schema_version,
            summary={
                "dataset_id": result.dataset_id,
                "analysis_method": result.analysis_method.value,
                "sample_size": result.analysis_sample.sample_size,
                "finding_count": len(result.findings),
            },
        )
        return {
            "artifact": json_compatible(reference),
            "result": bounded_payload(result, max_bytes=self.config.maximum_tool_output_bytes),
        }

    def run_causal_analysis(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RunCausalAnalysisRequest.model_validate(arguments)
        result = core_run_causal_analysis(request=request.to_core())
        reference = artifact_reference(
            artifact_id=result.causal_analysis_id,
            artifact_type="causal_analysis_result",
            resource_uri=f"polaris://provenance/{result.causal_analysis_id}",
            schema_version=result.schema_version,
            summary={
                "dataset_id": result.dataset_id,
                "causal_method": result.method.value,
                "estimator": result.estimator.value,
                "estimand": result.estimand.value,
                "treated_entities": result.sample_summary.treated_entity_count,
                "control_entities": result.sample_summary.control_entity_count,
            },
        )
        return {
            "artifact": json_compatible(reference),
            "result": bounded_payload(result, max_bytes=self.config.maximum_tool_output_bytes),
        }

    def run_robustness_analysis(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RunRobustnessAnalysisRequest.model_validate(arguments)
        from polaris.analysis.causal.models import CausalAnalysisResult
        from polaris.analysis.robustness.models import RobustnessSpecification
        from polaris.ingestion.models import DatasetIngestionResult

        result = core_analyze_robustness(
            ingestion_result=DatasetIngestionResult.model_validate(request.ingestion_result),
            baseline_result=CausalAnalysisResult.model_validate(request.baseline_result),
            specification=RobustnessSpecification.model_validate(request.robustness_specification),
            significance_threshold=request.significance_threshold,
        )
        reference = artifact_reference(
            artifact_id=result.robustness_analysis_id,
            artifact_type="robustness_analysis_result",
            resource_uri=f"polaris://provenance/{result.robustness_analysis_id}",
            schema_version=result.schema_version,
            summary={
                "baseline_analysis_id": result.baseline.baseline_analysis_id,
                "successful_variants": len(result.variant_results),
                "failed_variants": len(result.failed_variants),
                "robustness_status": result.robustness_evidence_status.value,
            },
        )
        return {
            "artifact": json_compatible(reference),
            "result": bounded_payload(result, max_bytes=self.config.maximum_tool_output_bytes),
        }

    def list_causal_studies(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = CausalStudySearchQuery.model_validate(arguments)
        return {"studies": json_compatible(core_list_causal_studies(query=query))}

    def inspect_causal_study(self, arguments: dict[str, Any]) -> dict[str, Any]:
        study_id = arguments.get("study_id")
        if not isinstance(study_id, str) or not study_id.strip():
            raise ValueError("inspect_causal_study requires study_id")
        return {"study": json_compatible(core_inspect_causal_study(study_id))}

    def assess_causal_study_readiness(self, arguments: dict[str, Any]) -> dict[str, Any]:
        study_id = arguments.get("study_id")
        if not isinstance(study_id, str) or not study_id.strip():
            raise ValueError("assess_causal_study_readiness requires study_id")
        assessment = core_assess_causal_study_readiness(
            study_id,
            dataset_registry=self.resources.registry,
        )
        return {
            "artifact": json_compatible(
                artifact_reference(
                    artifact_id=assessment.assessment_id,
                    artifact_type="causal_study_readiness",
                    resource_uri=f"polaris://causal-studies/{study_id}/readiness",
                    schema_version=assessment.schema_version,
                    summary={
                        "study_id": study_id,
                        "readiness_status": assessment.readiness_status.value,
                        "blocking_findings": len(assessment.blocking_findings),
                    },
                )
            ),
            "assessment": bounded_payload(
                assessment,
                max_bytes=self.config.maximum_tool_output_bytes,
            ),
        }

    def integrate_datasets(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = IntegrateDatasetsRequest.model_validate(arguments)
        result = harmonize_datasets(request=request.to_core())
        reference = artifact_reference(
            artifact_id=result.harmonized_dataset_id,
            artifact_type="harmonized_dataset",
            resource_uri=f"polaris://provenance/{result.harmonized_dataset_id}",
            schema_version=result.harmonization_schema_version,
            summary={
                "input_dataset_ids": result.input_dataset_references,
                "records": len(result.records),
                "variables": [
                    item.canonical_variable_id for item in result.canonical_variable_catalog
                ],
                "finding_count": len(result.findings),
            },
        )
        return {
            "artifact": json_compatible(reference),
            "quality_summary": json_compatible(result.quality_summary),
        }

    def run_research_project(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RunResearchProjectRequest.model_validate(arguments).to_core()
        if request.output_directory is not None:
            self.config.resolve_under_allowed_roots(
                request.output_directory,
                roots=(self.config.allowed_project_output_directory,),
            )
        if request.reasoning.enabled and request.reasoning.mode == "provider_backed":
            if not self.config.provider_backed_reasoning_enabled:
                raise MCPSafetyError("provider-backed reasoning is disabled in MCP config")
        result = core_run_research_project(request, registry=self.resources.registry)
        artifact_ids = {
            "analysis_result_id": (
                result.analysis_result.result_id if result.analysis_result else None
            ),
            "report_id": (
                result.research_report.report.report_id if result.research_report else None
            ),
            "reasoning_id": (
                result.reasoning_artifact.reasoning_id if result.reasoning_artifact else None
            ),
            "provenance_reference": f"polaris://provenance/{result.project_id}",
        }
        return {
            "project_id": result.project_id,
            "status": result.overall_status.value,
            "stage_results": json_compatible(result.stage_results),
            "artifact_ids": artifact_ids,
            "artifact": json_compatible(
                artifact_reference(
                    artifact_id=result.project_id,
                    artifact_type="research_project",
                    resource_uri=f"polaris://projects/{result.project_id}",
                    schema_version=result.schema_version
                    if hasattr(result, "schema_version")
                    else result.request.schema_version,
                    summary={"status": result.overall_status.value},
                )
            ),
        }

    def retrieve_literature(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RetrieveLiteratureRequest.model_validate(arguments)
        if request.corpus_path is None:
            raise MCPSafetyError("retrieve_literature requires an explicit configured corpus_path")
        corpus_path = self.config.resolve_under_allowed_roots(
            request.corpus_path,
            roots=self.config.allowed_literature_corpus_roots,
        )
        corpus = ingest_literature_corpus(corpus_path, manifest_path=corpus_path / "manifest.json")
        if corpus.corpus_id != request.corpus_id:
            raise MCPSafetyError("corpus_id must match the ingested local corpus")
        result = core_retrieve_literature(corpus=corpus, request=request.to_retrieval_request())
        return {
            "artifact": json_compatible(
                artifact_reference(
                    artifact_id=f"retrieval_{result.corpus_id}",
                    artifact_type="literature_retrieval",
                    resource_uri=f"polaris://provenance/{result.corpus_id}",
                    schema_version=None,
                    summary={
                        "query": result.query,
                        "retrieved_chunk_count": len(result.ranked_chunks),
                    },
                )
            ),
            "result": bounded_payload(result, max_bytes=self.config.maximum_tool_output_bytes),
        }

    def run_reasoning(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = RunReasoningRequest.model_validate(arguments).to_core()
        if request.mode == "provider_backed" and not self.config.provider_backed_reasoning_enabled:
            raise MCPSafetyError("provider-backed reasoning is disabled in MCP config")
        artifact = build_reasoning_artifact(request=request)
        return {
            "artifact": json_compatible(
                artifact_reference(
                    artifact_id=artifact.reasoning_id,
                    artifact_type="reasoning_artifact",
                    resource_uri=f"polaris://reasoning/{artifact.reasoning_id}",
                    schema_version=artifact.schema_version,
                    summary=json_compatible(artifact.grounding_summary),
                )
            ),
            "reasoning": bounded_payload(
                artifact,
                max_bytes=self.config.maximum_tool_output_bytes,
            ),
        }

    def evaluate_reasoning(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.config.evaluation_enabled:
            raise MCPSafetyError("reasoning evaluation is disabled in MCP config")
        request = EvaluateReasoningRequest.model_validate(arguments)
        reasoning = ReasoningArtifact.model_validate(request.reasoning_artifact)
        result = core_evaluate_reasoning(
            case=request.benchmark(),
            reasoning=reasoning,
            check_reproducibility=request.check_reproducibility,
        )
        return {
            "artifact": json_compatible(
                artifact_reference(
                    artifact_id=result.evaluation_id,
                    artifact_type="reasoning_evaluation",
                    resource_uri=f"polaris://evaluations/{result.evaluation_id}",
                    schema_version=result.schema_version,
                    summary={
                        "benchmark_case_id": result.benchmark_case_id,
                        "failed_expectations": result.failed_expectations,
                        "passed_expectations": result.passed_expectations,
                    },
                )
            ),
            "evaluation": bounded_payload(
                result,
                max_bytes=self.config.maximum_tool_output_bytes,
            ),
        }

    def get_report(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = GetReportRequest.model_validate(arguments)
        resource = self.resources.read_resource(f"polaris://reports/{request.report_id}")
        if resource.get("format") != request.format and request.format != "json":
            raise MCPSafetyError("requested report format is not available as a derived artifact")
        return resource


def _error_payload(error: PolarisMCPError) -> dict[str, Any]:
    return error.to_payload()
