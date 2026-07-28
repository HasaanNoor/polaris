from pathlib import Path
from typing import Any

import pytest

from polaris.agents.service import run_all_domain_agents
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.service import extract_evidence
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat, ReportRequest
from polaris.schemas.common import (
    DataType,
    EvidenceStrength,
    GeographicScope,
    QuestionCategory,
    TemporalScope,
    VariableReference,
    VariableRole,
)
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from polaris.synthesis.models import SynthesisMode, SynthesisRequest
from polaris.synthesis.service import synthesize_assessment


@pytest.fixture
def reporting_pipeline(tmp_path: Path):
    path = tmp_path / "literacy_fertility_gdp.csv"
    path.write_text(
        "\n".join(
            [
                "country,fertility_rate,female_literacy,gdp_per_capita",
                "a,5.0,45,1000",
                "b,4.5,50,1400",
                "c,3.7,62,2100",
                "d,3.1,70,3000",
                "e,2.6,78,4500",
                "f,,82,5200",
                "g,2.1,88,6500",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = _manifest()
    ingestion = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=path),
    )
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=ingestion,
            statistical_specification=_specification(),
            significance_threshold=0.05,
        )
    )
    evidence = extract_evidence(analysis_result=analysis)
    assessments = run_all_domain_agents(evidence_artifact=evidence)
    coordinated = coordinate_assessments(assessments=assessments)
    synthesis = synthesize_assessment(
        request=SynthesisRequest(
            coordinated_assessment=coordinated,
            mode=SynthesisMode.DETERMINISTIC,
            evidence_artifact=evidence,
        )
    )
    return {
        "manifest": manifest,
        "ingestion": ingestion,
        "analysis": analysis,
        "evidence": evidence,
        "assessments": assessments,
        "coordinated": coordinated,
        "synthesis": synthesis,
        "research_question": _research_question(),
    }


@pytest.fixture
def report_request(reporting_pipeline):
    return ReportRequest(
        synthesis_artifact=reporting_pipeline["synthesis"],
        coordinated_assessment=reporting_pipeline["coordinated"],
        evidence_artifact=reporting_pipeline["evidence"],
        analysis_result=reporting_pipeline["analysis"],
        ingestion_result=reporting_pipeline["ingestion"],
        research_question=reporting_pipeline["research_question"],
        dataset_manifest=reporting_pipeline["manifest"],
        output_format=ReportFormat.MARKDOWN,
        report_title="Illustrative Literacy, Fertility, and GDP Report",
        report_subtitle="Illustrative Polaris Phase 9 example",
        author="Polaris",
        organization="Polaris Examples",
    )


def _manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "reporting_literacy_fertility_gdp_sample",
            "title": "Illustrative Literacy, Fertility, and GDP Sample",
            "provider": "Polaris synthetic example",
            "source_url": "local://examples/reporting",
            "description": "Illustrative sample data for local report-generation tests.",
            "status": "candidate",
            "geographic_coverage": {"codes": ["TEST"], "description": "Illustrative countries"},
            "temporal_coverage": {"start": 2020, "end": 2020},
            "variables": [
                _variable("country", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("fertility_rate", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("female_literacy", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("gdp_per_capita", DataType.FLOAT, VariableRole.COVARIATE),
            ],
        }
    )


def _specification() -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": "spec_reporting_ols",
        "investigation_id": "investigation_reporting",
        "analysis_type": "regression",
        "model_family": "linear",
        "procedure": "ordinary_least_squares",
        "outcome_variable": {"variable_id": "fertility_rate"},
        "exposure_variables": [{"variable_id": "female_literacy"}],
        "covariates": [{"variable_id": "gdp_per_capita"}],
        "unit_of_analysis": "country",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "Illustrative report fixture",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": "associational",
    }
    return StatisticalSpecification.model_validate(payload)


def _research_question() -> ResearchQuestion:
    return ResearchQuestion(
        question_id="rq_reporting_illustrative",
        raw_text=(
            "How is female literacy associated with fertility rate after accounting for GDP "
            "per capita in the illustrative sample?"
        ),
        category=QuestionCategory.CORRELATIONAL,
        outcome_variables=[VariableReference(variable_id="fertility_rate")],
        exposure_variables=[VariableReference(variable_id="female_literacy")],
        covariates=[VariableReference(variable_id="gdp_per_capita")],
        population="Illustrative country observations",
        geographic_scope=GeographicScope(codes=["TEST"], description="Illustrative countries"),
        temporal_scope=TemporalScope(start=2020, end=2020),
        unit_of_analysis="country",
        requested_evidence_level=EvidenceStrength.LIMITED,
        requested_analytical_methods=["ordinary_least_squares"],
        assumptions=["Illustrative sample only"],
        exclusions=["No external literature integration"],
        created_at="2026-07-28T00:00:00Z",
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "label": variable_id,
        "data_type": data_type,
        "role": role,
    }
