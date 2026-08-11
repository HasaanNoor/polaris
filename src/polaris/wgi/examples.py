"""Phase 16 real-data examples for WGI governance integration."""

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
from polaris.wgi import build_wgi_governance_panel, export_wgi_governance_panel
from polaris.wgi.export import wgi_governance_panel_manifest


def run_phase16_wgi_examples(
    *,
    raw_root: str | Path = "data/raw",
    output_root: str | Path = "examples/wgi",
    min_year: int = 2015,
    max_year: int = 2021,
) -> dict[str, Any]:
    """Build WGI exports and cross-domain examples from local official snapshots."""

    raw = Path(raw_root)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    wdi_raw = raw / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    who_raw = raw / "who" / "life_expectancy_at_birth_and_age_60.csv"
    panel = build_wgi_governance_panel(raw_root=raw)
    wgi_export = export_wgi_governance_panel(
        panel=panel,
        output_dir=output,
        write_provenance=False,
    )
    wgi_trimmed = _trim_wgi_csv(
        source_path=wgi_export.csv_path,
        output_path=output / "wgi_governance_panel_sample.csv",
        min_year=min_year,
        max_year=max_year,
    )
    wgi_manifest = wgi_governance_panel_manifest(panel=panel, csv_path=wgi_trimmed)
    (output / "wgi_governance_panel_manifest.json").write_text(
        json.dumps(wgi_manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    wdi_prepared = prepare_wdi_validation_extract(
        source_path=wdi_raw,
        output_path=output / "phase16_wdi_extract.csv",
        min_year=min_year,
        max_year=max_year,
    )
    who_prepared = prepare_who_life_expectancy_extract(
        source_path=who_raw,
        output_path=output / "phase16_who_life_expectancy_extract.csv",
        min_year=min_year,
        max_year=max_year,
    )
    wdi = _ingest(
        wdi_validation_manifest(prepared_path=wdi_prepared, source_path=wdi_raw),
        wdi_prepared,
    )
    who = _ingest(
        who_life_expectancy_manifest(prepared_path=who_prepared, source_path=who_raw),
        who_prepared,
    )
    wgi = _ingest(wgi_manifest, wgi_trimmed)
    wdi_wgi = harmonize_datasets(request=_wdi_wgi_request(wdi_result=wdi, wgi_result=wgi))
    wdi_wgi_manifest = export_harmonized_dataset(
        harmonized=wdi_wgi,
        csv_path=output / "wdi_wgi_harmonized_sample.csv",
        manifest_path=output / "wdi_wgi_harmonized_manifest.json",
        summary_path=output / "wdi_wgi_harmonization_summary.json",
    )
    wdi_who_wgi = harmonize_datasets(
        request=_wdi_who_wgi_request(wdi_result=wdi, who_result=who, wgi_result=wgi)
    )
    wdi_who_wgi_manifest = export_harmonized_dataset(
        harmonized=wdi_who_wgi,
        csv_path=output / "wdi_who_wgi_harmonized_sample.csv",
        manifest_path=output / "wdi_who_wgi_harmonized_manifest.json",
        summary_path=output / "wdi_who_wgi_harmonization_summary.json",
    )
    project = run_research_project(
        _phase16_project_request(
            wdi=wdi,
            who=who,
            wgi=wgi,
            output_directory=output / "project_outputs",
        )
    )
    report_content = (
        project.research_report.rendered_content
        if project.research_report is not None
        else "Phase 16 report was not rendered."
    )
    (output / "phase16_report.md").write_text(report_content or "", encoding="utf-8")
    payload = {
        "panel_id": panel.panel_id,
        "panel_quality_summary": panel.quality_summary.model_dump(mode="json"),
        "schema_profile": panel.schema_profile.model_dump(mode="json"),
        "wgi_manifest_id": wgi_manifest.dataset_id,
        "wdi_wgi_harmonized_manifest_id": wdi_wgi_manifest.dataset_id,
        "wdi_who_wgi_harmonized_manifest_id": wdi_who_wgi_manifest.dataset_id,
        "wdi_wgi_quality_summary": wdi_wgi.quality_summary.model_dump(mode="json"),
        "wdi_who_wgi_quality_summary": wdi_who_wgi.quality_summary.model_dump(mode="json"),
        "project_id": project.project_id,
        "project_status": project.overall_status.value,
        "analysis_result_id": (
            project.analysis_result.result_id if project.analysis_result else None
        ),
        "selected_agents": [agent.value for agent in project.request.selected_agents],
        "domain_assessments": [
            assessment.agent_domain.value for assessment in project.domain_assessments
        ],
        "research_question": project.request.research_question.raw_text,
        "non_causal_language": True,
    }
    (output / "phase16_project_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if project.overall_status is not ProjectStatus.COMPLETED:
        raise RuntimeError("Phase 16 real-data project did not complete")
    return payload


def _trim_wgi_csv(
    *,
    source_path: Path,
    output_path: Path,
    min_year: int,
    max_year: int,
) -> Path:
    with source_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows = [
            row
            for row in reader
            if min_year <= int(row["year"]) <= max_year
            and row["country_code"] in {"AFG", "ALB", "CHN", "IND", "PAK", "USA", "GBR"}
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
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )


def _wdi_wgi_request(*, wdi_result, wgi_result) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi_result, wgi_result),
        dataset_configs=(
            _config(wdi_result, "wdi", "world_bank"),
            _config(wgi_result, "wgi", "world_bank"),
        ),
        variable_mappings=(
            _wdi_gdp_mapping(wdi_result),
            _wgi_mapping(wgi_result, "wgi_government_effectiveness", "Government Effectiveness"),
        ),
        join_type=JoinType.INNER,
        temporal_scope=TemporalScope(start=2015, end=2021),
    )


def _wdi_who_wgi_request(*, wdi_result, who_result, wgi_result) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi_result, who_result, wgi_result),
        dataset_configs=(
            _config(wdi_result, "wdi", "world_bank"),
            _config(who_result, "who", "who"),
            _config(wgi_result, "wgi", "world_bank"),
        ),
        variable_mappings=(
            _wdi_gdp_mapping(wdi_result),
            _who_life_mapping(who_result),
            _wgi_mapping(wgi_result, "wgi_government_effectiveness", "Government Effectiveness"),
            _wgi_mapping(wgi_result, "wgi_control_corruption", "Control of Corruption"),
        ),
        join_type=JoinType.INNER,
        temporal_scope=TemporalScope(start=2015, end=2021),
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


def _wgi_mapping(result, variable_id: str, label: str) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="world_bank_wgi",
        source_variable_id=variable_id,
        source_field_name=variable_id,
        canonical_variable_id=variable_id,
        canonical_label=f"WGI {label}",
        source_unit="standard normal governance estimate",
        canonical_unit="standard normal governance estimate",
        conceptual_definition=f"World Bank WGI {label} central governance estimate.",
        expected_data_type="float",
    )


def _phase16_project_request(
    *,
    wdi,
    who,
    wgi,
    output_directory: Path,
) -> ResearchProjectRequest:
    hrequest = _wdi_who_wgi_request(wdi_result=wdi, who_result=who, wgi_result=wgi)
    return ResearchProjectRequest(
        project_name="Phase 16 Government Effectiveness and Life Expectancy",
        research_question=ResearchQuestion(
            question_id="rq_phase16_government_effectiveness_life_expectancy",
            raw_text=(
                "How is government effectiveness associated with life expectancy across "
                "countries after accounting for GDP per capita?"
            ),
            category=QuestionCategory.CORRELATIONAL,
            outcome_variables=[
                VariableReference(variable_id="who_life_expectancy_at_birth_both_sexes")
            ],
            exposure_variables=[
                VariableReference(variable_id="wgi_government_effectiveness"),
                VariableReference(variable_id="wdi_gdp_per_capita_current_usd"),
            ],
            population="Country-year observations with WDI, WHO, and WGI coverage",
            geographic_scope=GeographicScope(codes=["GLOBAL"]),
            temporal_scope=TemporalScope(start=2015, end=2021),
            unit_of_analysis="country-year",
            requested_evidence_level=EvidenceStrength.LIMITED,
            requested_analytical_methods=["ordinary_least_squares"],
            assumptions=["Complete-case associational model; no causal identification claim."],
            exclusions=["No interpolation, imputation, smoothing, or composite governance index."],
            created_at="2026-08-11T00:00:00Z",
        ),
        dataset_inputs=(
            IngestionArtifactInput(ingestion_result=wdi),
            IngestionArtifactInput(ingestion_result=who),
            IngestionArtifactInput(ingestion_result=wgi),
        ),
        harmonization=ProjectHarmonizationConfig(
            dataset_configs=hrequest.dataset_configs,
            variable_mappings=hrequest.variable_mappings,
            join_type=hrequest.join_type,
        ),
        statistical_specification=StatisticalSpecification.model_validate(
            {
                "specification_id": "spec_phase16_government_effectiveness_life_expectancy",
                "investigation_id": "investigation_phase16_wgi",
                "analysis_type": StatisticalAnalysisType.CORRELATION,
                "model_family": StatisticalModelFamily.LINEAR,
                "procedure": StatisticalProcedure.ORDINARY_LEAST_SQUARES,
                "outcome_variable": {"variable_id": "who_life_expectancy_at_birth_both_sexes"},
                "exposure_variables": [
                    {"variable_id": "wgi_government_effectiveness"},
                    {"variable_id": "wdi_gdp_per_capita_current_usd"},
                ],
                "unit_of_analysis": "country-year",
                "missing_data_strategy": {
                    "strategy": "complete_case",
                    "rationale": "Conservative Phase 16 associational validation.",
                },
                "confidence_level": 0.95,
                "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
            }
        ),
        selected_agents=(
            AgentDomain.GOVERNANCE,
            AgentDomain.ECONOMICS,
            AgentDomain.PUBLIC_HEALTH,
        ),
        report=ProjectReportConfig(
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 16 WGI Governance Integration Validation",
            report_subtitle="Government effectiveness, income, and life expectancy",
            author="Polaris",
            organization="Polaris",
        ),
        execution_settings=ProjectExecutionSettings(write_outputs=True, raise_on_failure=True),
        output_directory=output_directory,
    )
