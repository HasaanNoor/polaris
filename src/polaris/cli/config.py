"""User-facing project configuration loading and translation."""

from __future__ import annotations

import difflib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from polaris.agents.models import AgentDomain
from polaris.cli.errors import CLIConfigurationError, CLIResourceNotFoundError
from polaris.cli.system import DEFAULT_OUTPUT_ROOT, dataset_registry
from polaris.harmonization.models import (
    DatasetHarmonizationConfig,
    JoinType,
    VariableMapping,
)
from polaris.projects.models import (
    ManifestDatasetInput,
    ProjectExecutionSettings,
    ProjectHarmonizationConfig,
    ProjectReportConfig,
    ReasoningProjectConfig,
    RegistryDatasetInput,
    ResearchProjectRequest,
    VisualizationProjectConfig,
)
from polaris.reasoning.taxonomy import ReasoningMode
from polaris.registry import DatasetRegistry
from polaris.registry.errors import DatasetNotFoundError
from polaris.registry.loader import load_manifest
from polaris.reporting.models import ReportFormat
from polaris.schemas.common import (
    CausalIdentificationLevel,
    EvidenceStrength,
    QuestionCategory,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
    VariableReference,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import MissingDataStrategy, StatisticalSpecification
from polaris.visualization.models import VisualizationSpecification

CONFIG_SCHEMA_VERSION = "1.0.0"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectSection(_StrictModel):
    name: str
    description: str | None = None


class ResearchQuestionSection(_StrictModel):
    text: str
    category: QuestionCategory = QuestionCategory.CORRELATIONAL
    population: str = "Configured analysis sample"
    unit_of_analysis: str = "country-year"
    evidence_level: EvidenceStrength = EvidenceStrength.LIMITED


class DatasetSection(_StrictModel):
    dataset_id: str
    source_path: Path | None = None
    manifest_path: Path | None = None
    expected_checksum: str | None = None


class HarmonizationSection(_StrictModel):
    join_type: JoinType = JoinType.INNER
    dataset_configs: list[DatasetHarmonizationConfig] = Field(default_factory=list)
    variable_mappings: list[VariableMapping] = Field(default_factory=list)
    anchor_dataset_id: str | None = None
    output_dataset_id: str | None = None


class AnalysisSection(_StrictModel):
    procedure: StatisticalProcedure
    outcome: str
    predictors: list[str] = Field(default_factory=list)
    covariates: list[str] = Field(default_factory=list)
    entity: str | None = None
    time: str | None = None
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    causal_identification: CausalIdentificationLevel = CausalIdentificationLevel.ASSOCIATIONAL
    unit_of_analysis: str = "country-year"


class ReasoningSection(_StrictModel):
    enabled: bool = False
    mode: Literal["deterministic", "provider", "provider_backed"] = "deterministic"
    allow_fallback: bool = False


class ReportingSection(_StrictModel):
    formats: list[ReportFormat] = Field(default_factory=lambda: [ReportFormat.MARKDOWN])
    title: str | None = None


class OutputsSection(_StrictModel):
    root: Path = DEFAULT_OUTPUT_ROOT


class ResearchProjectConfig(_StrictModel):
    schema_version: str = CONFIG_SCHEMA_VERSION
    project: ProjectSection
    research_question: ResearchQuestionSection
    datasets: list[DatasetSection] = Field(min_length=1)
    harmonization: HarmonizationSection | None = None
    analysis: AnalysisSection
    agents: list[AgentDomain] = Field(default_factory=lambda: [AgentDomain.ECONOMICS])
    reasoning: ReasoningSection = Field(default_factory=ReasoningSection)
    visualizations: list[VisualizationSpecification] | bool | dict[str, Any] = Field(default=False)
    reporting: ReportingSection = Field(default_factory=ReportingSection)
    outputs: OutputsSection = Field(default_factory=OutputsSection)

    @field_validator("schema_version")
    @classmethod
    def require_known_schema(cls, value: str) -> str:
        if value != CONFIG_SCHEMA_VERSION:
            raise ValueError(f"unsupported project config schema_version {value!r}")
        return value


def load_project_config(path: Path) -> ResearchProjectConfig:
    checked = _safe_existing_file(path)
    text = checked.read_text(encoding="utf-8")
    try:
        if checked.suffix.lower() == ".json":
            payload = json.loads(text)
        elif checked.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise CLIConfigurationError(
                    "YAML support requires the cli dependency extra.",
                    suggestion='Install with: pip install -e ".[cli]"',
                ) from exc
            payload = yaml.safe_load(text)
        else:
            raise CLIConfigurationError("Project configuration must be .yaml, .yml, or .json.")
    except CLIConfigurationError:
        raise
    except Exception as exc:
        raise CLIConfigurationError(f"Unable to parse project configuration: {exc}") from exc
    if not isinstance(payload, dict):
        raise CLIConfigurationError("Project configuration must be a mapping/object.")
    try:
        return ResearchProjectConfig.model_validate(payload)
    except ValidationError as exc:
        raise CLIConfigurationError(_format_validation_error(exc)) from exc


def validate_project_config(
    config: ResearchProjectConfig,
    *,
    config_path: Path,
    registry: DatasetRegistry | None = None,
) -> ResearchProjectRequest:
    active_registry = registry or dataset_registry()
    manifests = _resolve_manifests(config, config_path=config_path, registry=active_registry)
    request = to_project_request(config, config_path=config_path, registry=active_registry)
    variable_ids = _available_variables(config, manifests)
    requested = _requested_variables(config)
    unknown = [item for item in requested if item not in variable_ids]
    if unknown:
        first = unknown[0]
        suggestions = difflib.get_close_matches(first, sorted(variable_ids), n=3)
        message = f"Analysis variable not found:\n  {first}"
        if suggestions:
            message += "\nDid you mean:\n  " + "\n  ".join(suggestions)
        raise CLIConfigurationError(message)
    return request


def to_project_request(
    config: ResearchProjectConfig,
    *,
    config_path: Path,
    registry: DatasetRegistry | None = None,
) -> ResearchProjectRequest:
    active_registry = registry or dataset_registry()
    dataset_inputs = []
    for item in config.datasets:
        if item.manifest_path is not None:
            manifest_path = _resolve_relative_path(item.manifest_path, config_path.parent)
            manifest = load_manifest(manifest_path)
            if manifest.dataset_id != item.dataset_id:
                raise CLIConfigurationError(
                    f"Dataset not found:\n  {item.dataset_id}\n"
                    f"Manifest declares dataset_id:\n  {manifest.dataset_id}\n"
                    f"Did you mean:\n  {manifest.dataset_id}"
                )
            source_path = _source_path(item, manifest=manifest, base=config_path.parent)
            dataset_inputs.append(
                ManifestDatasetInput(
                    manifest=manifest,
                    source_path=source_path,
                    expected_checksum=item.expected_checksum or manifest.checksum,
                )
            )
            continue
        try:
            manifest = active_registry.get(item.dataset_id)
        except DatasetNotFoundError as exc:
            raise _unknown_dataset(item.dataset_id, active_registry) from exc
        source_path = _source_path(item, manifest=manifest, base=config_path.parent)
        dataset_inputs.append(
            RegistryDatasetInput(
                dataset_id=item.dataset_id,
                source_path=source_path,
                expected_checksum=item.expected_checksum,
            )
        )
    return ResearchProjectRequest(
        project_name=config.project.name,
        research_question=_research_question(config),
        dataset_inputs=tuple(dataset_inputs),
        statistical_specification=_statistical_specification(config),
        selected_agents=tuple(config.agents),
        harmonization=_harmonization(config),
        reasoning=_reasoning(config),
        visualization=_visualization(config),
        report=ProjectReportConfig(
            output_format=config.reporting.formats[0],
            report_title=config.reporting.title or config.project.name,
        ),
        execution_settings=ProjectExecutionSettings(write_outputs=True, raise_on_failure=False),
        output_directory=config.outputs.root,
    )


def normalized_config(config: ResearchProjectConfig) -> dict[str, Any]:
    return config.model_dump(mode="json", exclude_none=True)


def _research_question(config: ResearchProjectConfig) -> ResearchQuestion:
    analysis = config.analysis
    return ResearchQuestion(
        question_id=f"rq_{_slug(config.project.name)}",
        raw_text=config.research_question.text,
        category=config.research_question.category,
        outcome_variables=[VariableReference(variable_id=analysis.outcome)],
        exposure_variables=[VariableReference(variable_id=item) for item in analysis.predictors],
        covariates=[VariableReference(variable_id=item) for item in analysis.covariates],
        population=config.research_question.population,
        geographic_scope={"codes": ["CONFIGURED"]},
        temporal_scope={},
        unit_of_analysis=config.research_question.unit_of_analysis,
        requested_evidence_level=config.research_question.evidence_level,
        requested_analytical_methods=[analysis.procedure.value],
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _statistical_specification(config: ResearchProjectConfig) -> StatisticalSpecification:
    procedure = config.analysis.procedure
    if procedure in {
        StatisticalProcedure.ORDINARY_LEAST_SQUARES,
        StatisticalProcedure.PANEL_ENTITY_FE,
        StatisticalProcedure.PANEL_TWO_WAY_FE,
        StatisticalProcedure.FIRST_DIFFERENCE,
    }:
        analysis_type = StatisticalAnalysisType.REGRESSION
        family = StatisticalModelFamily.LINEAR
    elif procedure in {
        StatisticalProcedure.PEARSON_CORRELATION,
        StatisticalProcedure.SPEARMAN_CORRELATION,
    }:
        analysis_type = StatisticalAnalysisType.CORRELATION
        family = StatisticalModelFamily.NONE
    else:
        analysis_type = StatisticalAnalysisType.DESCRIPTIVE
        family = StatisticalModelFamily.NONE
    return StatisticalSpecification(
        specification_id=f"spec_{_slug(config.project.name)}_{procedure.value}",
        investigation_id=f"investigation_{_slug(config.project.name)}",
        analysis_type=analysis_type,
        model_family=family,
        procedure=procedure,
        outcome_variable=VariableReference(variable_id=config.analysis.outcome),
        exposure_variables=[
            VariableReference(variable_id=item) for item in config.analysis.predictors
        ],
        covariates=[VariableReference(variable_id=item) for item in config.analysis.covariates],
        entity_variable=VariableReference(variable_id=config.analysis.entity)
        if config.analysis.entity
        else None,
        time_variable=VariableReference(variable_id=config.analysis.time)
        if config.analysis.time
        else None,
        unit_of_analysis=config.analysis.unit_of_analysis,
        missing_data_strategy=MissingDataStrategy(
            strategy="complete_case",
            rationale="Configured by Polaris CLI project workflow.",
        ),
        confidence_level=config.analysis.confidence_level,
        causal_identification_claim_level=config.analysis.causal_identification,
    )


def _harmonization(config: ResearchProjectConfig) -> ProjectHarmonizationConfig | None:
    if config.harmonization is None:
        return None
    return ProjectHarmonizationConfig(
        dataset_configs=tuple(config.harmonization.dataset_configs),
        variable_mappings=tuple(config.harmonization.variable_mappings),
        join_type=config.harmonization.join_type,
        anchor_dataset_id=config.harmonization.anchor_dataset_id,
        output_dataset_id=config.harmonization.output_dataset_id,
    )


def _reasoning(config: ResearchProjectConfig) -> ReasoningProjectConfig:
    if not config.reasoning.enabled:
        return ReasoningProjectConfig(enabled=False)
    if config.reasoning.mode in {"provider", "provider_backed"}:
        raise CLIConfigurationError(
            "Provider-backed reasoning was explicitly requested, but the CLI has no provider "
            "configured for this local run.",
            suggestion="Use reasoning.mode: deterministic or configure a provider-backed API path.",
        )
    return ReasoningProjectConfig(enabled=True, mode=ReasoningMode.DETERMINISTIC)


def _visualization(config: ResearchProjectConfig) -> VisualizationProjectConfig:
    value = config.visualizations
    if value is False or value == {"enabled": False}:
        return VisualizationProjectConfig(enabled=False)
    if isinstance(value, dict):
        specs = value.get("specifications", [])
    else:
        specs = value
    if not specs:
        return VisualizationProjectConfig(enabled=False)
    parsed = tuple(
        item
        if isinstance(item, VisualizationSpecification)
        else VisualizationSpecification.model_validate(item)
        for item in specs
    )
    return VisualizationProjectConfig(enabled=True, specifications=parsed)


def _resolve_manifests(
    config: ResearchProjectConfig,
    *,
    config_path: Path,
    registry: DatasetRegistry,
) -> dict[str, DatasetManifest]:
    manifests = {}
    for item in config.datasets:
        if item.manifest_path is not None:
            manifest = load_manifest(_resolve_relative_path(item.manifest_path, config_path.parent))
            if manifest.dataset_id != item.dataset_id:
                raise CLIConfigurationError(
                    f"Dataset not found:\n  {item.dataset_id}\n"
                    f"Manifest declares dataset_id:\n  {manifest.dataset_id}\n"
                    f"Did you mean:\n  {manifest.dataset_id}"
                )
        else:
            try:
                manifest = registry.get(item.dataset_id)
            except DatasetNotFoundError as exc:
                raise _unknown_dataset(item.dataset_id, registry) from exc
        manifests[item.dataset_id] = manifest
    return manifests


def _available_variables(
    config: ResearchProjectConfig, manifests: dict[str, DatasetManifest]
) -> set[str]:
    if config.harmonization is not None and config.harmonization.variable_mappings:
        values = {
            mapping.canonical_variable_id for mapping in config.harmonization.variable_mappings
        }
        values.update({"canonical_country_code", "canonical_country_name", "year"})
        return values
    return {
        variable.variable_id for manifest in manifests.values() for variable in manifest.variables
    }


def _requested_variables(config: ResearchProjectConfig) -> tuple[str, ...]:
    values = [
        config.analysis.outcome,
        *config.analysis.predictors,
        *config.analysis.covariates,
    ]
    if config.analysis.entity:
        values.append(config.analysis.entity)
    if config.analysis.time:
        values.append(config.analysis.time)
    return tuple(dict.fromkeys(values))


def _source_path(item: DatasetSection, *, manifest: DatasetManifest, base: Path) -> Path:
    path = item.source_path or Path(manifest.access_url or "")
    if not str(path):
        raise CLIConfigurationError(f"Dataset {item.dataset_id} requires source_path.")
    resolved = _resolve_relative_path(path, base)
    if not resolved.exists():
        raise CLIResourceNotFoundError(
            f"Dataset source not found for {item.dataset_id}: {resolved}",
            suggestion="Check source_path or run the appropriate provider acquisition step first.",
        )
    return resolved


def _resolve_relative_path(path: Path, base: Path) -> Path:
    candidate = path if path.is_absolute() else (base / path)
    if not candidate.exists() and not path.is_absolute():
        repo_candidate = Path.cwd() / path
        if repo_candidate.exists():
            candidate = repo_candidate
        else:
            examples_candidate = Path.cwd() / "examples" / "projects" / path
            if examples_candidate.exists():
                candidate = examples_candidate
    resolved = candidate.resolve()
    workspace = Path.cwd().resolve()
    if workspace not in (resolved, *resolved.parents):
        raise CLIConfigurationError(f"Path escapes the Polaris workspace: {path}")
    return resolved


def _safe_existing_file(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise CLIResourceNotFoundError(f"Configuration file not found: {resolved}")
    return resolved


def _unknown_dataset(dataset_id: str, registry: DatasetRegistry) -> CLIConfigurationError:
    ids = [manifest.dataset_id for manifest in registry.list_all()]
    suggestions = difflib.get_close_matches(dataset_id, ids, n=3)
    message = f"Dataset not found:\n  {dataset_id}"
    if suggestions:
        message += "\nDid you mean:\n  " + "\n  ".join(suggestions)
    return CLIConfigurationError(message)


def _format_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    loc = ".".join(str(item) for item in first.get("loc", ())) or "configuration"
    return f"Invalid project configuration at {loc}: {first.get('msg', 'validation failed')}"


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "project"
