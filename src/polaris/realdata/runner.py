"""End-to-end Phase 11 real dataset validation runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polaris.agents.service import run_all_domain_agents
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.service import extract_evidence
from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.realdata.compatibility import validate_manifest_against_file, variable_summaries
from polaris.realdata.discovery import discover_real_datasets, inspect_schema
from polaris.realdata.models import PipelineValidationResult, RealDatasetValidationResult
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat, ReportRequest
from polaris.reporting.service import generate_report
from polaris.schemas.common import (
    CausalIdentificationLevel,
    EvidenceStrength,
    GeographicScope,
    QuestionCategory,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
    TemporalScope,
    VariableReference,
)
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from polaris.synthesis.models import SynthesisMode, SynthesisRequest
from polaris.synthesis.service import synthesize_assessment


def run_real_dataset_validation(
    *,
    raw_root: str | Path = "data/raw",
    output_root: str | Path = "examples/validation",
) -> RealDatasetValidationResult:
    """Run Phase 3 through Phase 9 against a prepared official WDI extract."""

    discovered = discover_real_datasets(raw_root)
    selected = _select_wdi(discovered)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)

    raw_inspection = inspect_schema(selected.path)
    prepared_path = prepare_wdi_validation_extract(
        source_path=selected.path,
        output_path=output / "world_bank_wdi_phase11_validation.csv",
    )
    manifest = wdi_validation_manifest(prepared_path=prepared_path, source_path=selected.path)
    manifest_path = output / "world_bank_wdi_phase11_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    manifest_validation = validate_manifest_against_file(
        manifest=manifest,
        source_path=prepared_path,
        manifest_path=manifest_path,
    )
    prepared_inspection = inspect_schema(prepared_path, max_rows=None)
    summaries = variable_summaries(manifest, prepared_path)

    ingestion = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=prepared_path,
            expected_checksum=manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
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
            evidence_artifact=evidence,
            mode=SynthesisMode.DETERMINISTIC,
        )
    )
    report = generate_report(
        request=ReportRequest(
            synthesis_artifact=synthesis,
            coordinated_assessment=coordinated,
            evidence_artifact=evidence,
            analysis_result=analysis,
            ingestion_result=ingestion,
            research_question=_research_question(),
            dataset_manifest=manifest,
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 11 Real Dataset Validation Report",
            report_subtitle="World Bank WDI official bulk CSV",
            author="Polaris",
            organization="Polaris",
        )
    )
    if report.rendered_content is not None:
        (output / "world_bank_wdi_phase11_report.md").write_text(
            report.rendered_content,
            encoding="utf-8",
        )

    pipeline = PipelineValidationResult(
        ingestion_succeeded=ingestion.validation_report.analysis_ready,
        analysis_succeeded=analysis.analysis_sample.sample_size > 0,
        evidence_extraction_succeeded=bool(evidence.evidence_records),
        domain_assessments_succeeded=len(assessments) == 4,
        coordination_succeeded=bool(coordinated.coordinated_assessment_id),
        synthesis_succeeded=bool(synthesis.synthesis_id),
        report_generation_succeeded=bool(report.report.report_id),
        analysis_result_id=analysis.result_id,
        evidence_artifact_id=evidence.artifact_id,
        coordinated_assessment_id=coordinated.coordinated_assessment_id,
        synthesis_artifact_id=synthesis.synthesis_id,
        report_id=report.report.report_id,
        accepted_row_count=ingestion.validation_report.accepted_row_count,
        analysis_sample_size=analysis.analysis_sample.sample_size,
    )
    result = RealDatasetValidationResult(
        discovered_datasets=discovered,
        selected_dataset=selected,
        raw_schema_inspection=raw_inspection,
        prepared_schema_inspection=prepared_inspection,
        manifest_validation=manifest_validation,
        variable_summaries=summaries,
        pipeline=pipeline,
        report=report,
    )
    (output / "world_bank_wdi_phase11_validation_summary.json").write_text(
        json.dumps(_summary_payload(result), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return result


def _select_wdi(discovered):
    for dataset in discovered:
        if dataset.provider == "world_bank" and dataset.dataset_key == "WDI":
            return dataset
    raise FileNotFoundError("data/raw/world_bank/WDI_CSV/WDICSV.csv was not discovered")


def _specification() -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": "spec_phase11_wdi_real_validation",
        "investigation_id": "investigation_phase11_real_dataset_validation",
        "analysis_type": StatisticalAnalysisType.REGRESSION,
        "model_family": StatisticalModelFamily.LINEAR,
        "procedure": StatisticalProcedure.ORDINARY_LEAST_SQUARES,
        "outcome_variable": {"variable_id": "life_expectancy_at_birth"},
        "exposure_variables": [{"variable_id": "secondary_school_enrollment"}],
        "covariates": [{"variable_id": "gdp_per_capita_current_usd"}],
        "unit_of_analysis": "country-year",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "Phase 11 validates the existing complete-case statistical pipeline.",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
    }
    return StatisticalSpecification.model_validate(payload)


def _research_question() -> ResearchQuestion:
    return ResearchQuestion(
        question_id="rq_phase11_wdi_real_validation",
        raw_text=(
            "How is secondary school enrollment associated with life expectancy at birth "
            "after accounting for GDP per capita in the official WDI validation extract?"
        ),
        category=QuestionCategory.CORRELATIONAL,
        outcome_variables=[VariableReference(variable_id="life_expectancy_at_birth")],
        exposure_variables=[VariableReference(variable_id="secondary_school_enrollment")],
        covariates=[VariableReference(variable_id="gdp_per_capita_current_usd")],
        population="Country-year observations in the WDI validation extract",
        geographic_scope=GeographicScope(codes=["GLOBAL"], description="World Bank WDI coverage"),
        temporal_scope=TemporalScope(start=2015, end=2023, label="Annual WDI observations"),
        unit_of_analysis="country-year",
        requested_evidence_level=EvidenceStrength.LIMITED,
        requested_analytical_methods=["ordinary_least_squares"],
        assumptions=["Associational validation only"],
        exclusions=["No retrieval, database, API, dashboard, or new statistical method"],
        created_at="2026-08-05T00:00:00Z",
    )


def _summary_payload(result: RealDatasetValidationResult) -> dict[str, Any]:
    payload = result.model_dump(mode="json", exclude={"report"})
    payload["report"] = {
        "report_id": result.report.report.report_id,
        "output_format": result.report.output_format.value,
        "rendered": result.report.rendered_content is not None,
    }
    return payload
