from __future__ import annotations

from pathlib import Path
from typing import Any

from polaris.agents.models import AgentDomain
from polaris.harmonization import JoinType
from polaris.projects import (
    IngestionArtifactInput,
    ManifestDatasetInput,
    ProjectHarmonizationConfig,
    ProjectReportConfig,
    ResearchProjectRequest,
)
from polaris.reporting.models import ReportFormat
from polaris.schemas.common import (
    CausalIdentificationLevel,
    DataType,
    EvidenceStrength,
    QuestionCategory,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
    VariableReference,
    VariableRole,
)
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from tests.harmonization.helpers import request_for, wdi_result, who_result
from tests.ingestion.helpers import manifest_with_variables, variable, write_csv


def single_manifest_project(tmp_path: Path) -> ResearchProjectRequest:
    data_path = write_csv(
        tmp_path / "single.csv",
        [
            ["country", "year", "x", "y"],
            ["A", "2020", "1", "2"],
            ["B", "2020", "2", "3"],
            ["C", "2020", "3", "5"],
            ["D", "2020", "4", "8"],
        ],
    )
    manifest = manifest_with_variables(
        [
            variable("country", DataType.STRING, role=VariableRole.IDENTIFIER),
            variable("year", DataType.INTEGER, role=VariableRole.TIME),
            variable("x", DataType.FLOAT, role=VariableRole.EXPOSURE),
            variable("y", DataType.FLOAT, role=VariableRole.OUTCOME),
        ],
        dataset_id="single_project_dataset",
    )
    return base_request(
        dataset_inputs=(ManifestDatasetInput(manifest=manifest, source_path=data_path),),
        statistical_specification=specification(
            procedure=StatisticalProcedure.PEARSON_CORRELATION,
            analysis_type=StatisticalAnalysisType.CORRELATION,
            model_family=StatisticalModelFamily.NONE,
            outcome="y",
            exposures=("x",),
        ),
    )


def harmonized_project(tmp_path: Path) -> ResearchProjectRequest:
    wdi = wdi_result(tmp_path)
    who = who_result(tmp_path)
    hrequest = request_for(wdi, who, join_type=JoinType.LEFT)
    return base_request(
        dataset_inputs=(
            IngestionArtifactInput(ingestion_result=wdi),
            IngestionArtifactInput(ingestion_result=who),
        ),
        harmonization=ProjectHarmonizationConfig(
            dataset_configs=hrequest.dataset_configs,
            variable_mappings=hrequest.variable_mappings,
            join_type=hrequest.join_type,
            anchor_dataset_id=hrequest.anchor_dataset_id,
        ),
        statistical_specification=specification(
            procedure=StatisticalProcedure.PEARSON_CORRELATION,
            analysis_type=StatisticalAnalysisType.CORRELATION,
            model_family=StatisticalModelFamily.NONE,
            outcome="who_life_expectancy_at_birth_both_sexes",
            exposures=("wdi_gdp_per_capita_current_usd",),
        ),
        output_directory=tmp_path / "outputs",
    )


def base_request(
    *,
    dataset_inputs,
    statistical_specification: StatisticalSpecification,
    harmonization: ProjectHarmonizationConfig | None = None,
    output_directory: Path | None = None,
    selected_agents: tuple[AgentDomain, ...] = (AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH),
) -> ResearchProjectRequest:
    return ResearchProjectRequest(
        project_name="Test Project",
        research_question=question(),
        dataset_inputs=dataset_inputs,
        harmonization=harmonization,
        statistical_specification=statistical_specification,
        selected_agents=selected_agents,
        report=ProjectReportConfig(output_format=ReportFormat.MARKDOWN),
        output_directory=output_directory,
    )


def question() -> ResearchQuestion:
    return ResearchQuestion(
        question_id="rq_project_test",
        raw_text="How is x associated with y?",
        category=QuestionCategory.CORRELATIONAL,
        outcome_variables=[VariableReference(variable_id="y")],
        exposure_variables=[VariableReference(variable_id="x")],
        population="Test country-year rows",
        geographic_scope={"codes": ["TEST"]},
        temporal_scope={"start": 2020, "end": 2021},
        unit_of_analysis="country-year",
        requested_evidence_level=EvidenceStrength.LIMITED,
        requested_analytical_methods=["pearson_correlation"],
        created_at="2026-08-07T00:00:00Z",
    )


def specification(
    *,
    procedure: StatisticalProcedure,
    analysis_type: StatisticalAnalysisType,
    model_family: StatisticalModelFamily,
    outcome: str,
    exposures: tuple[str, ...],
    extra: dict[str, Any] | None = None,
) -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": f"spec_project_{procedure.value}",
        "investigation_id": "investigation_project_test",
        "analysis_type": analysis_type,
        "model_family": model_family,
        "procedure": procedure,
        "outcome_variable": {"variable_id": outcome},
        "exposure_variables": [{"variable_id": value} for value in exposures],
        "unit_of_analysis": "country-year",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "project orchestration test",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
    }
    if extra:
        payload.update(extra)
    return StatisticalSpecification.model_validate(payload)
