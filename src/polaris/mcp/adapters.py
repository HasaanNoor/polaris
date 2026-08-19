"""Typed MCP request/response adapters over existing Polaris public APIs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from polaris.analysis.causal.models import CausalAnalysisRequest, CausalSpecification
from polaris.analysis.models import AnalysisExecutionSettings, AnalysisRequest
from polaris.evaluation.models import BenchmarkCase
from polaris.harmonization.models import HarmonizationRequest
from polaris.ingestion.models import DatasetIngestionResult
from polaris.literature.models import RetrievalMode, RetrievalRequest
from polaris.projects.models import ResearchProjectRequest
from polaris.reasoning.models import ReasoningRequest
from polaris.registry.models import (
    DatasetCollectionType,
    DatasetSearchQuery,
    TemporalRequirement,
)
from polaris.schemas.common import FrozenPolarisBaseModel, NonEmptyStr
from polaris.schemas.statistics import StatisticalSpecification


class MCPArtifactReference(FrozenPolarisBaseModel):
    artifact_id: NonEmptyStr
    artifact_type: NonEmptyStr
    resource_uri: NonEmptyStr
    schema_version: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


class ListDatasetsRequest(FrozenPolarisBaseModel):
    provider: str | None = None
    research_domain: str | None = None
    collection_type: DatasetCollectionType | None = None
    geographic_coverage: tuple[str, ...] = Field(default_factory=tuple)
    temporal_start: int | None = None
    temporal_end: int | None = None

    def to_search_query(self) -> DatasetSearchQuery:
        keywords = (self.research_domain,) if self.research_domain else ()
        providers = (self.provider,) if self.provider else ()
        temporal = (
            TemporalRequirement(start=self.temporal_start, end=self.temporal_end)
            if self.temporal_start is not None or self.temporal_end is not None
            else None
        )
        return DatasetSearchQuery(
            keywords=keywords,
            providers=providers,
            geographic=self.geographic_coverage,
            temporal=temporal,
        )


class InspectDatasetRequest(FrozenPolarisBaseModel):
    dataset_id: NonEmptyStr


class RunAnalysisRequest(FrozenPolarisBaseModel):
    ingestion_result: dict[str, Any]
    statistical_specification: dict[str, Any]
    execution_settings: dict[str, Any] = Field(default_factory=dict)
    significance_threshold: float | None = Field(default=None, gt=0, lt=1)
    confidence_level: float | None = Field(default=None, gt=0, lt=1)

    def to_core(self) -> AnalysisRequest:
        return AnalysisRequest(
            ingestion_result=DatasetIngestionResult.model_validate(self.ingestion_result),
            statistical_specification=StatisticalSpecification.model_validate(
                self.statistical_specification
            ),
            execution_settings=AnalysisExecutionSettings.model_validate(self.execution_settings),
            significance_threshold=self.significance_threshold,
            confidence_level=self.confidence_level,
        )


class RunCausalAnalysisRequest(FrozenPolarisBaseModel):
    ingestion_result: dict[str, Any]
    causal_specification: dict[str, Any]
    significance_threshold: float | None = Field(default=None, gt=0, lt=1)
    confidence_level: float | None = Field(default=None, gt=0, lt=1)

    @model_validator(mode="after")
    def require_explicit_causal_design(self) -> RunCausalAnalysisRequest:
        required = (
            "method",
            "entity_variable",
            "time_variable",
            "outcome_variable",
            "treatment",
            "treated_group_description",
            "comparison_group_description",
            "pre_treatment_window",
            "post_treatment_window",
            "estimand",
            "standard_error_strategy",
        )
        missing = [key for key in required if key not in self.causal_specification]
        if missing:
            raise ValueError(
                "run_causal_analysis requires explicit causal specification fields: "
                + ", ".join(missing)
            )
        return self

    def to_core(self) -> CausalAnalysisRequest:
        return CausalAnalysisRequest(
            ingestion_result=DatasetIngestionResult.model_validate(self.ingestion_result),
            causal_specification=CausalSpecification.model_validate(self.causal_specification),
            significance_threshold=self.significance_threshold,
            confidence_level=self.confidence_level,
        )


class IntegrateDatasetsRequest(FrozenPolarisBaseModel):
    harmonization_request: dict[str, Any]

    @model_validator(mode="after")
    def require_explicit_join_configuration(self) -> IntegrateDatasetsRequest:
        payload = self.harmonization_request
        required = ("ingestion_results", "dataset_configs", "variable_mappings", "join_type")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(
                "integrate_datasets requires explicit harmonization fields: " + ", ".join(missing)
            )
        if payload.get("join_type") == "left" and not payload.get("anchor_dataset_id"):
            raise ValueError("left joins require an explicit anchor_dataset_id")
        return self

    def to_core(self) -> HarmonizationRequest:
        return HarmonizationRequest.model_validate(self.harmonization_request)


class RunResearchProjectRequest(FrozenPolarisBaseModel):
    project_request: dict[str, Any]

    def to_core(self) -> ResearchProjectRequest:
        return ResearchProjectRequest.model_validate(self.project_request)


class RetrieveLiteratureRequest(FrozenPolarisBaseModel):
    corpus_id: NonEmptyStr
    corpus_path: str | None = None
    query: NonEmptyStr
    top_k: int = Field(default=5, ge=1)
    retrieval_mode: RetrievalMode = RetrievalMode.BM25
    year_range: tuple[int, int] | None = None
    domain_filters: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    publication_filters: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    document_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)

    def to_retrieval_request(self) -> RetrievalRequest:
        return RetrievalRequest(
            query=self.query,
            corpus_id=self.corpus_id,
            top_k=self.top_k,
            retrieval_mode=self.retrieval_mode,
            year_range=self.year_range,
            domain_filters=self.domain_filters,
            publication_filters=self.publication_filters,
            document_ids=self.document_ids,
        )


class RunReasoningRequest(FrozenPolarisBaseModel):
    reasoning_request: dict[str, Any]

    def to_core(self) -> ReasoningRequest:
        return ReasoningRequest.model_validate(self.reasoning_request)


class EvaluateReasoningRequest(FrozenPolarisBaseModel):
    benchmark_case: dict[str, Any]
    reasoning_artifact: dict[str, Any]
    check_reproducibility: bool = False

    def benchmark(self) -> BenchmarkCase:
        return BenchmarkCase.model_validate(self.benchmark_case)


class GetReportRequest(FrozenPolarisBaseModel):
    report_id: NonEmptyStr
    format: Literal["json", "markdown", "html"] = "json"


def artifact_reference(
    *,
    artifact_id: str,
    artifact_type: str,
    resource_uri: str,
    schema_version: str | None = None,
    summary: dict[str, Any] | None = None,
) -> MCPArtifactReference:
    return MCPArtifactReference(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        resource_uri=resource_uri,
        schema_version=schema_version,
        summary=summary or {},
    )
