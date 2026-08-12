"""Phase 17 real-data examples for UNESCO education integration."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from polaris.agents.models import AgentDomain
from polaris.harmonization import (
    DatasetHarmonizationConfig,
    HarmonizationRequest,
    JoinType,
    VariableMapping,
    export_harmonized_dataset,
    harmonize_datasets,
)
from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.projects import (
    IngestionArtifactInput,
    ProjectExecutionSettings,
    ProjectHarmonizationConfig,
    ProjectReportConfig,
    ResearchProjectRequest,
    run_research_project,
)
from polaris.projects.models import ProjectStatus
from polaris.realdata.harmonization import (
    prepare_who_life_expectancy_extract,
    who_life_expectancy_manifest,
)
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat
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
from polaris.unesco import build_unesco_education_panel, export_unesco_education_panel
from polaris.wgi.examples import _trim_wgi_csv
from polaris.wgi.export import wgi_governance_panel_manifest
from polaris.wgi.panel import build_wgi_governance_panel


def run_phase17_unesco_examples(
    *,
    raw_root: str | Path = "data/raw",
    output_root: str | Path = "examples/unesco",
    min_year: int = 2015,
    max_year: int = 2021,
) -> dict[str, Any]:
    raw = Path(raw_root)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    panel = build_unesco_education_panel(raw_root=raw / "unesco")
    unesco_export = export_unesco_education_panel(
        panel=panel, output_dir=output, write_provenance=False
    )
    unesco_trimmed = _trim_unesco_csv(
        source_path=unesco_export.csv_path,
        output_path=output / "unesco_education_panel_sample.csv",
        min_year=min_year,
        max_year=max_year,
    )
    from polaris.unesco.export import unesco_education_panel_manifest

    unesco_manifest = unesco_education_panel_manifest(panel=panel, csv_path=unesco_trimmed)
    (output / "unesco_education_panel_manifest.json").write_text(
        json.dumps(unesco_manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    wdi_raw = raw / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    who_raw = raw / "who" / "life_expectancy_at_birth_and_age_60.csv"
    wdi_prepared = prepare_wdi_validation_extract(
        source_path=wdi_raw,
        output_path=output / "phase17_wdi_extract.csv",
        min_year=min_year,
        max_year=max_year,
    )
    who_prepared = prepare_who_life_expectancy_extract(
        source_path=who_raw,
        output_path=output / "phase17_who_life_expectancy_extract.csv",
        min_year=min_year,
        max_year=max_year,
    )
    wdi = _ingest(
        wdi_validation_manifest(prepared_path=wdi_prepared, source_path=wdi_raw), wdi_prepared
    )
    who = _ingest(
        who_life_expectancy_manifest(prepared_path=who_prepared, source_path=who_raw), who_prepared
    )
    unesco = _ingest(unesco_manifest, unesco_trimmed)
    wdi_unesco = harmonize_datasets(
        request=_wdi_unesco_request(wdi_result=wdi, unesco_result=unesco)
    )
    wdi_unesco_manifest = export_harmonized_dataset(
        harmonized=wdi_unesco,
        csv_path=output / "wdi_unesco_harmonized_sample.csv",
        manifest_path=output / "wdi_unesco_harmonized_manifest.json",
        summary_path=output / "wdi_unesco_harmonization_summary.json",
    )
    wgi_panel = build_wgi_governance_panel(raw_root=raw)
    from polaris.wgi import export_wgi_governance_panel

    wgi_export = export_wgi_governance_panel(
        panel=wgi_panel, output_dir=output, write_provenance=False
    )
    wgi_trimmed = _trim_wgi_csv(
        source_path=wgi_export.csv_path,
        output_path=output / "phase17_wgi_panel_sample.csv",
        min_year=min_year,
        max_year=max_year,
    )
    for generated_path in (
        wgi_export.csv_path,
        wgi_export.manifest_path,
        wgi_export.quality_summary_path,
        wgi_export.variable_catalog_path,
    ):
        if generated_path is not None and Path(generated_path).exists():
            Path(generated_path).unlink()
    wgi_manifest = wgi_governance_panel_manifest(panel=wgi_panel, csv_path=wgi_trimmed)
    wgi = _ingest(wgi_manifest, wgi_trimmed)
    multi = harmonize_datasets(
        request=_multi_domain_request(
            wdi_result=wdi, who_result=who, wgi_result=wgi, unesco_result=unesco
        )
    )
    multi_manifest = export_harmonized_dataset(
        harmonized=multi,
        csv_path=output / "multi_domain_phase17_sample.csv",
        manifest_path=output / "multi_domain_phase17_manifest.json",
        summary_path=output / "multi_domain_phase17_summary.json",
    )
    project = run_research_project(
        _phase17_project_request(
            wdi=wdi, who=who, unesco=unesco, output_directory=output / "project_outputs"
        )
    )
    report_content = project.research_report.rendered_content if project.research_report else ""
    (output / "phase17_report.md").write_text(report_content or "", encoding="utf-8")
    payload = {
        "panel_id": panel.panel_id,
        "panel_quality_summary": panel.quality_summary.model_dump(mode="json"),
        "dataset_profiles": __import__(
            "polaris.unesco.profiling", fromlist=["profile_all_downloaded_datasets"]
        ).profile_all_downloaded_datasets(raw_root=raw / "unesco"),
        "unesco_manifest_id": unesco_manifest.dataset_id,
        "wdi_unesco_manifest_id": wdi_unesco_manifest.dataset_id,
        "multi_domain_manifest_id": multi_manifest.dataset_id,
        "wdi_unesco_quality_summary": wdi_unesco.quality_summary.model_dump(mode="json"),
        "multi_domain_quality_summary": multi.quality_summary.model_dump(mode="json"),
        "project_id": project.project_id,
        "project_status": project.overall_status.value,
        "analysis_result_id": project.analysis_result.result_id
        if project.analysis_result
        else None,
        "selected_agents": [agent.value for agent in project.request.selected_agents],
        "domain_assessments": [
            assessment.agent_domain.value for assessment in project.domain_assessments
        ],
        "research_question": project.request.research_question.raw_text,
        "non_causal_language": True,
    }
    (output / "phase17_project_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    if project.overall_status is not ProjectStatus.COMPLETED:
        raise RuntimeError("Phase 17 real-data project did not complete")
    return payload


def _trim_unesco_csv(*, source_path: Path, output_path: Path, min_year: int, max_year: int) -> Path:
    keep = {"AFG", "ALB", "CHN", "IND", "PAK", "USA", "GBR"}
    with source_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows = [
            row
            for row in reader
            if row["country_code"] in keep and min_year <= int(row["year"]) <= max_year
        ]
        fieldnames = reader.fieldnames or []
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _ingest(manifest, source_path: Path):
    return ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=source_path,
            expected_checksum=manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE
            ),
        ),
    )


def _config(result, alias: str, provider: str) -> DatasetHarmonizationConfig:
    return DatasetHarmonizationConfig(
        dataset_id=result.dataset_manifest.dataset_id,
        alias=alias,
        provider=provider,
        country_field="country_code",
        country_name_field="country_name",
        year_field="year",
    )


def _wdi_unesco_request(*, wdi_result, unesco_result) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi_result, unesco_result),
        dataset_configs=(
            _config(wdi_result, "wdi", "world_bank"),
            _config(unesco_result, "unesco", "unesco"),
        ),
        variable_mappings=(
            _wdi_gdp_mapping(wdi_result),
            _unesco_mapping(unesco_result, "uis_upper_secondary_attainment_rate_25plus"),
        ),
        join_type=JoinType.INNER,
        temporal_scope=TemporalScope(start=2015, end=2021),
    )


def _multi_domain_request(
    *, wdi_result, who_result, wgi_result, unesco_result
) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi_result, who_result, wgi_result, unesco_result),
        dataset_configs=(
            _config(wdi_result, "wdi", "world_bank"),
            _config(who_result, "who", "who"),
            _config(wgi_result, "wgi", "world_bank_wgi"),
            _config(unesco_result, "unesco", "unesco"),
        ),
        variable_mappings=(
            _wdi_gdp_mapping(wdi_result),
            _who_life_mapping(who_result),
            _wgi_mapping(wgi_result, "wgi_government_effectiveness"),
            _unesco_mapping(unesco_result, "uis_upper_secondary_attainment_rate_25plus"),
        ),
        join_type=JoinType.INNER,
        temporal_scope=TemporalScope(start=2015, end=2021),
    )


def _wdi_gdp_mapping(result) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="world_bank",
        source_variable_id="gdp_per_capita_current_usd",
        source_field_name="gdp_per_capita_current_usd",
        canonical_variable_id="wdi_gdp_per_capita_current_usd",
        canonical_label="GDP per capita, current US dollars",
        source_unit="current US dollars",
        canonical_unit="current US dollars",
        conceptual_definition="WDI GDP per capita in current US dollars.",
        expected_data_type="float",
    )


def _who_life_mapping(result) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="who",
        source_variable_id="who_life_expectancy_at_birth",
        source_field_name="who_life_expectancy_at_birth",
        canonical_variable_id="who_life_expectancy_at_birth_both_sexes",
        canonical_label="WHO life expectancy at birth, both sexes",
        source_unit="years",
        canonical_unit="years",
        conceptual_definition="WHO GHO WHOSIS_000001 life expectancy at birth, both sexes.",
        expected_data_type="float",
    )


def _wgi_mapping(result, variable_id: str) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="world_bank_wgi",
        source_variable_id=variable_id,
        source_field_name=variable_id,
        canonical_variable_id=variable_id,
        canonical_label="WGI Government Effectiveness",
        source_unit="standard normal governance estimate",
        canonical_unit="standard normal governance estimate",
        conceptual_definition="World Bank WGI Government Effectiveness central estimate.",
        expected_data_type="float",
    )


def _unesco_mapping(result, variable_id: str) -> VariableMapping:
    variable = next(v for v in result.dataset_manifest.variables if v.variable_id == variable_id)
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="unesco",
        source_variable_id=variable_id,
        source_field_name=variable_id,
        canonical_variable_id=variable_id,
        canonical_label=variable.label,
        source_unit=variable.unit or "percent",
        canonical_unit=variable.unit or "percent",
        conceptual_definition=variable.description or variable.label,
        expected_data_type="float",
    )


def _phase17_project_request(*, wdi, who, unesco, output_directory: Path) -> ResearchProjectRequest:
    hrequest = HarmonizationRequest(
        ingestion_results=(wdi, who, unesco),
        dataset_configs=(
            _config(wdi, "wdi", "world_bank"),
            _config(who, "who", "who"),
            _config(unesco, "unesco", "unesco"),
        ),
        variable_mappings=(
            _wdi_gdp_mapping(wdi),
            _who_life_mapping(who),
            _unesco_mapping(unesco, "uis_upper_secondary_attainment_rate_25plus"),
        ),
        join_type=JoinType.INNER,
    )
    return ResearchProjectRequest(
        project_name="Phase 17 Education, GDP, and Life Expectancy",
        research_question=ResearchQuestion(
            question_id="rq_phase17_education_life_expectancy",
            raw_text=(
                "How is educational attainment associated with life expectancy after "
                "accounting for GDP per capita?"
            ),
            category=QuestionCategory.CORRELATIONAL,
            outcome_variables=[
                VariableReference(variable_id="who_life_expectancy_at_birth_both_sexes")
            ],
            exposure_variables=[
                VariableReference(variable_id="uis_upper_secondary_attainment_rate_25plus"),
                VariableReference(variable_id="wdi_gdp_per_capita_current_usd"),
            ],
            population="Country-year observations with WDI, WHO, and UNESCO coverage",
            geographic_scope=GeographicScope(codes=["GLOBAL"]),
            temporal_scope=TemporalScope(start=2015, end=2021),
            unit_of_analysis="country-year",
            requested_evidence_level=EvidenceStrength.LIMITED,
            requested_analytical_methods=["ordinary_least_squares"],
            assumptions=["Complete-case associational model; no causal identification claim."],
            exclusions=[
                "No interpolation, imputation, smoothing, sex averaging, or education index."
            ],
            created_at="2026-08-12T00:00:00Z",
        ),
        dataset_inputs=(
            IngestionArtifactInput(ingestion_result=wdi),
            IngestionArtifactInput(ingestion_result=who),
            IngestionArtifactInput(ingestion_result=unesco),
        ),
        harmonization=ProjectHarmonizationConfig(
            dataset_configs=hrequest.dataset_configs,
            variable_mappings=hrequest.variable_mappings,
            join_type=hrequest.join_type,
        ),
        statistical_specification=StatisticalSpecification.model_validate(
            {
                "specification_id": "spec_phase17_education_life_expectancy",
                "investigation_id": "investigation_phase17_unesco",
                "analysis_type": StatisticalAnalysisType.CORRELATION,
                "model_family": StatisticalModelFamily.LINEAR,
                "procedure": StatisticalProcedure.ORDINARY_LEAST_SQUARES,
                "outcome_variable": {"variable_id": "who_life_expectancy_at_birth_both_sexes"},
                "exposure_variables": [
                    {"variable_id": "uis_upper_secondary_attainment_rate_25plus"},
                    {"variable_id": "wdi_gdp_per_capita_current_usd"},
                ],
                "unit_of_analysis": "country-year",
                "missing_data_strategy": {
                    "strategy": "complete_case",
                    "rationale": "Conservative Phase 17 associational validation.",
                },
                "confidence_level": 0.95,
                "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
            }
        ),
        selected_agents=(AgentDomain.EDUCATION, AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH),
        report=ProjectReportConfig(
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 17 UNESCO Education Integration Validation",
            report_subtitle="Education, income, and life expectancy",
            author="Polaris",
            organization="Polaris",
        ),
        execution_settings=ProjectExecutionSettings(write_outputs=True, raise_on_failure=True),
        output_directory=output_directory,
    )
