"""Typed contracts for Phase 13 research-project orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from polaris import __version__
from polaris.agents.models import AgentAssessment, AgentDomain
from polaris.analysis.models import AnalysisExecutionSettings, AnalysisResult
from polaris.coordination.models import DOMAIN_ORDER, CoordinatedAssessment
from polaris.evidence.models import EvidenceArtifact
from polaris.harmonization.models import (
    DatasetHarmonizationConfig,
    HarmonizationRequest,
    HarmonizationStrictness,
    HarmonizedDataset,
    JoinType,
    ProviderPrecedenceRule,
    VariableMapping,
)
from polaris.ingestion.models import DatasetIngestionResult, IngestionConfiguration
from polaris.reporting.models import GeneratedReport, ReportFormat
from polaris.schemas.common import (
    AwareDatetime,
    DatasetId,
    FrozenPolarisBaseModel,
    GeographicScope,
    NonEmptyStr,
    SchemaVersion,
    TemporalScope,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from polaris.synthesis.models import SynthesisMode, SynthesisProviderConfig

ORCHESTRATION_SCHEMA_VERSION = "1.0.0"


class DatasetInputKind(StrEnum):
    REGISTRY = "registry"
    MANIFEST = "manifest"
    INGESTION_ARTIFACT = "ingestion_artifact"
    HARMONIZED_DATASET = "harmonized_dataset"


class RegistryDatasetInput(FrozenPolarisBaseModel):
    kind: Literal[DatasetInputKind.REGISTRY] = DatasetInputKind.REGISTRY
    dataset_id: DatasetId
    source_path: Path
    expected_checksum: str | None = None
    ingestion_configuration: IngestionConfiguration = Field(default_factory=IngestionConfiguration)


class ManifestDatasetInput(FrozenPolarisBaseModel):
    kind: Literal[DatasetInputKind.MANIFEST] = DatasetInputKind.MANIFEST
    manifest: DatasetManifest
    source_path: Path
    expected_checksum: str | None = None
    ingestion_configuration: IngestionConfiguration = Field(default_factory=IngestionConfiguration)


class IngestionArtifactInput(FrozenPolarisBaseModel):
    kind: Literal[DatasetInputKind.INGESTION_ARTIFACT] = DatasetInputKind.INGESTION_ARTIFACT
    ingestion_result: DatasetIngestionResult


class HarmonizedDatasetInput(FrozenPolarisBaseModel):
    kind: Literal[DatasetInputKind.HARMONIZED_DATASET] = DatasetInputKind.HARMONIZED_DATASET
    harmonized_dataset: HarmonizedDataset


DatasetInput = Annotated[
    RegistryDatasetInput | ManifestDatasetInput | IngestionArtifactInput | HarmonizedDatasetInput,
    Field(discriminator="kind"),
]


class ProjectHarmonizationConfig(FrozenPolarisBaseModel):
    """Explicit Phase 12 configuration without pre-execution ingestion artifacts."""

    dataset_configs: tuple[DatasetHarmonizationConfig, ...] = Field(min_length=2)
    variable_mappings: tuple[VariableMapping, ...] = Field(min_length=1)
    join_type: JoinType
    anchor_dataset_id: DatasetId | None = None
    provider_precedence: tuple[ProviderPrecedenceRule, ...] = Field(default_factory=tuple)
    strictness: HarmonizationStrictness = Field(default_factory=HarmonizationStrictness)
    output_dataset_id: DatasetId | None = None

    def to_request(
        self,
        *,
        ingestion_results: tuple[DatasetIngestionResult, ...],
        geographic_scope: GeographicScope | None,
        temporal_scope: TemporalScope | None,
    ) -> HarmonizationRequest:
        return HarmonizationRequest(
            ingestion_results=ingestion_results,
            dataset_configs=self.dataset_configs,
            variable_mappings=self.variable_mappings,
            join_type=self.join_type,
            anchor_dataset_id=self.anchor_dataset_id,
            geographic_scope=geographic_scope,
            temporal_scope=temporal_scope,
            provider_precedence=self.provider_precedence,
            strictness=self.strictness,
            output_dataset_id=self.output_dataset_id,
        )


class ProjectExecutionSettings(FrozenPolarisBaseModel):
    analysis_execution_settings: AnalysisExecutionSettings = Field(
        default_factory=AnalysisExecutionSettings
    )
    significance_threshold: float | None = Field(default=None, gt=0, lt=1)
    confidence_level: float | None = Field(default=None, gt=0, lt=1)
    write_outputs: bool = True
    raise_on_failure: bool = False


class ProjectSynthesisConfig(FrozenPolarisBaseModel):
    mode: SynthesisMode = SynthesisMode.DETERMINISTIC
    provider_config: SynthesisProviderConfig | None = None
    model_identifier: NonEmptyStr | None = None
    allow_deterministic_fallback: bool = True
    max_synthesis_length: int | None = Field(default=None, gt=0)


class ProjectReportConfig(FrozenPolarisBaseModel):
    output_format: ReportFormat = ReportFormat.MARKDOWN
    report_title: NonEmptyStr | None = None
    report_subtitle: NonEmptyStr | None = None
    author: NonEmptyStr | None = None
    organization: NonEmptyStr | None = None


class ResearchProjectRequest(FrozenPolarisBaseModel):
    project_name: NonEmptyStr
    research_question: ResearchQuestion
    dataset_inputs: tuple[DatasetInput, ...] = Field(min_length=1)
    statistical_specification: StatisticalSpecification
    selected_agents: tuple[AgentDomain, ...] = Field(min_length=1)
    synthesis: ProjectSynthesisConfig = Field(default_factory=ProjectSynthesisConfig)
    report: ProjectReportConfig = Field(default_factory=ProjectReportConfig)
    harmonization: ProjectHarmonizationConfig | None = None
    geographic_scope: GeographicScope | None = None
    temporal_scope: TemporalScope | None = None
    execution_settings: ProjectExecutionSettings = Field(default_factory=ProjectExecutionSettings)
    output_directory: Path | None = None
    schema_version: SchemaVersion = ORCHESTRATION_SCHEMA_VERSION

    @field_validator("selected_agents")
    @classmethod
    def sort_agents(cls, value: tuple[AgentDomain, ...]) -> tuple[AgentDomain, ...]:
        order = {domain: index for index, domain in enumerate(DOMAIN_ORDER)}
        return tuple(sorted(set(value), key=lambda domain: order[domain]))

    @model_validator(mode="after")
    def validate_harmonization_shape(self) -> ResearchProjectRequest:
        harmonized_inputs = [
            item for item in self.dataset_inputs if item.kind is DatasetInputKind.HARMONIZED_DATASET
        ]
        if harmonized_inputs and len(self.dataset_inputs) > 1:
            raise ValueError("a precomputed harmonized dataset must be the only project input")
        if len(self.dataset_inputs) > 1 and self.harmonization is None:
            raise ValueError("multi-dataset projects require explicit harmonization configuration")
        if len(self.dataset_inputs) == 1 and self.harmonization is not None:
            raise ValueError("single-dataset projects must not include harmonization configuration")
        return self


class ResearchStage(StrEnum):
    RESOLVE_DATASETS = "resolve_datasets"
    INGEST = "ingest"
    HARMONIZE = "harmonize"
    ANALYZE = "analyze"
    EXTRACT_EVIDENCE = "extract_evidence"
    RUN_AGENTS = "run_agents"
    COORDINATE = "coordinate"
    SYNTHESIZE = "synthesize"
    REPORT = "report"
    COMPLETE = "complete"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ProjectStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectArtifactKind(StrEnum):
    DATASET_MANIFEST = "dataset_manifest"
    INGESTION_RESULT = "ingestion_result"
    HARMONIZED_DATASET = "harmonized_dataset"
    ANALYSIS_RESULT = "analysis_result"
    EVIDENCE_ARTIFACT = "evidence_artifact"
    AGENT_ASSESSMENT = "agent_assessment"
    COORDINATED_ASSESSMENT = "coordinated_assessment"
    SYNTHESIS_ARTIFACT = "synthesis_artifact"
    RESEARCH_REPORT = "research_report"


class ArtifactReference(FrozenPolarisBaseModel):
    artifact_id: NonEmptyStr
    kind: ProjectArtifactKind
    path: str | None = None


class ErrorMetadata(FrozenPolarisBaseModel):
    error_type: NonEmptyStr
    message: NonEmptyStr
    details: dict[str, str] = Field(default_factory=dict)


class ResearchStageResult(FrozenPolarisBaseModel):
    stage: ResearchStage
    status: StageStatus
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    input_artifact_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    output_artifact_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    warnings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    error: ErrorMetadata | None = None
    provenance_references: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)


class ResearchExecutionPlan(FrozenPolarisBaseModel):
    project_id: NonEmptyStr
    required_datasets: tuple[DatasetId, ...]
    stages: tuple[ResearchStage, ...]
    ingestion_dataset_ids: tuple[DatasetId, ...]
    harmonization_required: bool
    statistical_analysis_step: NonEmptyStr
    evidence_step: NonEmptyStr = "phase5_extract_evidence"
    selected_agents: tuple[AgentDomain, ...]
    coordination_step: NonEmptyStr = "phase7_coordinate_assessments"
    synthesis_step: SynthesisMode
    report_step: ReportFormat
    schema_version: SchemaVersion = ORCHESTRATION_SCHEMA_VERSION


class ResolvedDataset(FrozenPolarisBaseModel):
    dataset_id: DatasetId
    input_kind: DatasetInputKind
    manifest: DatasetManifest | None = None
    source_path: str | None = None
    expected_checksum: str | None = None
    source_checksum_sha256: str | None = None
    ingestion_result: DatasetIngestionResult | None = None
    harmonized_dataset: HarmonizedDataset | None = None


class ProjectProvenance(FrozenPolarisBaseModel):
    project_id: NonEmptyStr
    dataset_ids: tuple[DatasetId, ...]
    source_checksums: dict[str, str] = Field(default_factory=dict)
    manifest_ids: tuple[DatasetId, ...] = Field(default_factory=tuple)
    harmonization_artifact_id: NonEmptyStr | None = None
    analysis_artifact_id: NonEmptyStr | None = None
    evidence_artifact_id: NonEmptyStr | None = None
    agent_assessment_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    coordination_id: NonEmptyStr | None = None
    synthesis_id: NonEmptyStr | None = None
    report_id: NonEmptyStr | None = None
    software_version: NonEmptyStr = f"polaris-{__version__}"
    orchestration_schema_version: SchemaVersion = ORCHESTRATION_SCHEMA_VERSION
    execution_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))


class ReproducibilitySummary(FrozenPolarisBaseModel):
    project_id: NonEmptyStr
    source_dataset_count: int = Field(ge=0)
    source_checksums: dict[str, str] = Field(default_factory=dict)
    harmonization_used: bool
    statistical_method: NonEmptyStr
    selected_agents: tuple[AgentDomain, ...]
    synthesis_mode: SynthesisMode
    report_format: ReportFormat
    completed_stages: tuple[ResearchStage, ...]
    failed_stage: ResearchStage | None = None
    artifact_ids: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    reproducibility_ready: bool


class ResearchProjectResult(FrozenPolarisBaseModel):
    project_id: NonEmptyStr
    request: ResearchProjectRequest
    execution_plan: ResearchExecutionPlan
    overall_status: ProjectStatus
    stage_results: tuple[ResearchStageResult, ...]
    resolved_datasets: tuple[ResolvedDataset, ...] = Field(default_factory=tuple)
    ingestion_artifacts: tuple[DatasetIngestionResult, ...] = Field(default_factory=tuple)
    harmonized_dataset: HarmonizedDataset | None = None
    analysis_result: AnalysisResult | None = None
    evidence_artifact: EvidenceArtifact | None = None
    domain_assessments: tuple[AgentAssessment, ...] = Field(default_factory=tuple)
    coordinated_assessment: CoordinatedAssessment | None = None
    synthesis_artifact: object | None = None
    research_report: GeneratedReport | None = None
    project_provenance: ProjectProvenance
    reproducibility_summary: ReproducibilitySummary
    warnings: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    execution_metadata: dict[str, str] = Field(default_factory=dict)


def deterministic_project_id(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "project_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
