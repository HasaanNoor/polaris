"""Derived Phase 15 WDI plus WHO example artifacts."""

from __future__ import annotations

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
from polaris.ingestion.loader import calculate_sha256
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
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat
from polaris.schemas.common import (
    CausalIdentificationLevel,
    DatasetStatus,
    DataType,
    EvidenceStrength,
    GeographicScope,
    QuestionCategory,
    StatisticalAnalysisType,
    StatisticalModelFamily,
    StatisticalProcedure,
    TemporalScope,
    VariableReference,
    VariableRole,
)
from polaris.schemas.dataset import DatasetManifest, DatasetVariable, RevisionMetadata
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from polaris.who import build_who_health_panel, export_who_health_panel

WHO_EXAMPLE_VARIABLES = (
    "who_life_expectancy_birth_years",
    "who_hale_birth_years",
    "who_health_expenditure_pct_gdp",
    "who_medical_doctors_per_10000",
    "who_dtp3_immunization_pct",
)


def run_phase15_wdi_who_example(
    *,
    catalog_path: str | Path = "data/raw/who/gho/acquisition_catalog.json",
    wdi_sample_path: str | Path = "data/examples/world_bank_wdi_sample.csv",
    output_dir: str | Path = "examples/who",
) -> dict[str, Any]:
    """Build small derived artifacts proving WDI + WHO Phase 12/13 compatibility."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    panel = build_who_health_panel(catalog_path=catalog_path)
    panel_export = export_who_health_panel(
        panel=panel,
        output_dir=output,
        write_provenance=False,
    )
    who_result = ingest_dataset(
        registry=DatasetRegistry((panel_export_manifest(panel_export.manifest_path),)),
        request=IngestionRequest(
            dataset_id=panel.panel_id,
            source_path=panel_export.csv_path,
            expected_checksum=panel_export.checksum_sha256,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    wdi_manifest = _wdi_example_manifest(wdi_sample_path)
    wdi_result = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=Path(wdi_sample_path),
            expected_checksum=wdi_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    hrequest = _harmonization_request(wdi_result=wdi_result, who_result=who_result)
    harmonized = harmonize_datasets(request=hrequest)
    harmonized_manifest = export_harmonized_dataset(
        harmonized=harmonized,
        csv_path=output / "wdi_who_phase15_harmonized.csv",
        manifest_path=output / "wdi_who_phase15_harmonized_manifest.json",
        summary_path=output / "wdi_who_phase15_harmonization_summary.json",
    )
    project = run_research_project(
        _project_request(
            wdi_result=wdi_result,
            who_result=who_result,
            hrequest=hrequest,
            output_dir=Path("/private/tmp/polaris_phase15_wdi_who_project"),
        )
    )
    report_text = ""
    if project.research_report is not None and project.research_report.rendered_content:
        report_text = project.research_report.rendered_content
    (output / "wdi_who_phase15_report.md").write_text(report_text, encoding="utf-8")
    summary = {
        "panel_id": panel.panel_id,
        "who_panel_rows": len(panel.records),
        "who_integrated_indicator_count": panel.quality_summary.integrated_indicator_count,
        "who_deferred_indicator_count": panel.quality_summary.deferred_indicator_count,
        "wdi_dataset_id": wdi_result.dataset_manifest.dataset_id,
        "who_dataset_id": who_result.dataset_manifest.dataset_id,
        "harmonized_dataset_id": harmonized.harmonized_dataset_id,
        "harmonized_manifest_id": harmonized_manifest.dataset_id,
        "harmonized_rows": len(harmonized.records),
        "harmonized_variables": [
            entry.canonical_variable_id for entry in harmonized.canonical_variable_catalog
        ],
        "project_id": project.project_id,
        "project_status": project.overall_status.value,
        "analysis_result_id": (
            project.analysis_result.result_id if project.analysis_result else None
        ),
        "agent_domains": [
            assessment.agent_domain.value for assessment in project.domain_assessments
        ],
        "report_path": "examples/who/wdi_who_phase15_report.md",
        "note": (
            "Derived from official local WHO GHO snapshots and the committed local WDI sample; "
            "no network access or raw-provider mutation is required."
        ),
    }
    (output / "wdi_who_phase15_project_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def panel_export_manifest(path: str | Path) -> DatasetManifest:
    with Path(path).open(encoding="utf-8") as file:
        return DatasetManifest.model_validate(json.load(file))


def _wdi_example_manifest(wdi_sample_path: str | Path) -> DatasetManifest:
    checksum = calculate_sha256(wdi_sample_path)
    return DatasetManifest(
        dataset_id=f"world_bank_wdi_phase15_sample_{checksum[:12]}",
        title="World Bank WDI Phase 15 Local Sample",
        provider="World Bank",
        source_url="https://databank.worldbank.org/source/world-development-indicators",
        access_url=str(wdi_sample_path),
        description="Committed local WDI sample used for Phase 15 cross-provider validation.",
        license="World Bank data terms; sample already present in repository.",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(codes=["PAK", "NPL"]),
        temporal_coverage=TemporalScope(start=2020, end=2021),
        revision_metadata=RevisionMetadata(update_frequency="sample"),
        variables=[
            DatasetVariable(
                variable_id="country_code",
                label="Country code",
                data_type=DataType.STRING,
                role=VariableRole.IDENTIFIER,
                source_field_name="Country Code",
            ),
            DatasetVariable(
                variable_id="year",
                label="Year",
                data_type=DataType.INTEGER,
                role=VariableRole.TIME,
                source_field_name="Year",
            ),
            DatasetVariable(
                variable_id="wdi_gdp_per_capita_current_usd",
                label="GDP per capita, current US dollars",
                unit="current US dollars",
                data_type=DataType.FLOAT,
                role=VariableRole.PREDICTOR,
                source_field_name="NY.GDP.PCAP.CD",
                missing_value_representation=["null"],
            ),
        ],
        units=["country-year", "current US dollars"],
        frequency="annual",
        methodology_reference="https://databank.worldbank.org/metadataglossary/world-development-indicators",
        checksum=checksum,
    )


def _harmonization_request(wdi_result, who_result) -> HarmonizationRequest:
    who_mappings = tuple(
        VariableMapping(
            source_dataset_id=who_result.dataset_manifest.dataset_id,
            source_provider="who",
            source_variable_id=variable_id,
            source_field_name=variable_id,
            canonical_variable_id=variable_id,
            canonical_label=variable_id.replace("_", " "),
            source_unit=_unit_for(who_result.dataset_manifest, variable_id),
            canonical_unit=_unit_for(who_result.dataset_manifest, variable_id),
            conceptual_definition=f"WHO Phase 15 canonical variable {variable_id}.",
            expected_data_type="float",
        )
        for variable_id in WHO_EXAMPLE_VARIABLES
    )
    return HarmonizationRequest(
        ingestion_results=(wdi_result, who_result),
        dataset_configs=(
            DatasetHarmonizationConfig(
                dataset_id=wdi_result.dataset_manifest.dataset_id,
                alias="wdi",
                provider="world_bank",
                country_field="country_code",
                year_field="year",
            ),
            DatasetHarmonizationConfig(
                dataset_id=who_result.dataset_manifest.dataset_id,
                alias="who",
                provider="who",
                country_field="country_code",
                country_name_field="country_name",
                year_field="year",
            ),
        ),
        variable_mappings=(
            VariableMapping(
                source_dataset_id=wdi_result.dataset_manifest.dataset_id,
                source_provider="world_bank",
                source_variable_id="wdi_gdp_per_capita_current_usd",
                source_field_name="wdi_gdp_per_capita_current_usd",
                canonical_variable_id="wdi_gdp_per_capita_current_usd",
                canonical_label="GDP per capita, current US dollars",
                source_unit="current US dollars",
                canonical_unit="current US dollars",
                conceptual_definition="World Bank WDI GDP per capita in current US dollars.",
                expected_data_type="float",
            ),
            *who_mappings,
        ),
        join_type=JoinType.LEFT,
        anchor_dataset_id=wdi_result.dataset_manifest.dataset_id,
        temporal_scope=TemporalScope(start=2020, end=2021),
    )


def _unit_for(manifest: DatasetManifest, variable_id: str) -> str | None:
    for variable in manifest.variables:
        if variable.variable_id == variable_id:
            return variable.unit
    return None


def _project_request(
    *,
    wdi_result,
    who_result,
    hrequest: HarmonizationRequest,
    output_dir: Path,
) -> ResearchProjectRequest:
    return ResearchProjectRequest(
        project_name="Phase 15 WDI WHO Health Capacity Example",
        research_question=ResearchQuestion(
            question_id="rq_phase15_wdi_who_health_capacity",
            raw_text=(
                "How are national income and healthcare-system capacity associated with "
                "life expectancy across countries?"
            ),
            category=QuestionCategory.CORRELATIONAL,
            outcome_variables=[VariableReference(variable_id="who_life_expectancy_birth_years")],
            exposure_variables=[
                VariableReference(variable_id="wdi_gdp_per_capita_current_usd"),
                VariableReference(variable_id="who_health_expenditure_pct_gdp"),
            ],
            population="Country-year observations in the Phase 15 WDI plus WHO derived sample",
            geographic_scope=GeographicScope(codes=["PAK", "NPL"]),
            temporal_scope=TemporalScope(start=2020, end=2021),
            unit_of_analysis="country-year",
            requested_evidence_level=EvidenceStrength.LIMITED,
            requested_analytical_methods=["pearson_correlation"],
            assumptions=["Associational validation only; no causal interpretation."],
            exclusions=["No imputation, sex averaging, age averaging, or projection mixing."],
            created_at="2026-08-10T00:00:00Z",
        ),
        dataset_inputs=(
            IngestionArtifactInput(ingestion_result=wdi_result),
            IngestionArtifactInput(ingestion_result=who_result),
        ),
        harmonization=ProjectHarmonizationConfig(
            dataset_configs=hrequest.dataset_configs,
            variable_mappings=hrequest.variable_mappings,
            join_type=hrequest.join_type,
            anchor_dataset_id=hrequest.anchor_dataset_id,
        ),
        statistical_specification=StatisticalSpecification.model_validate(
            {
                "specification_id": "spec_phase15_wdi_who_life_expectancy",
                "investigation_id": "investigation_phase15_wdi_who",
                "analysis_type": StatisticalAnalysisType.CORRELATION,
                "model_family": StatisticalModelFamily.NONE,
                "procedure": StatisticalProcedure.PEARSON_CORRELATION,
                "outcome_variable": {"variable_id": "who_life_expectancy_birth_years"},
                "exposure_variables": [
                    {"variable_id": "wdi_gdp_per_capita_current_usd"},
                ],
                "unit_of_analysis": "country-year",
                "missing_data_strategy": {
                    "strategy": "complete_case",
                    "rationale": "Phase 15 example uses complete observed country-year rows.",
                },
                "confidence_level": 0.95,
                "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
            }
        ),
        selected_agents=(AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH),
        report=ProjectReportConfig(
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 15 WDI plus WHO Health Panel Example",
            report_subtitle="Associational validation using local derived data",
            author="Polaris",
            organization="Polaris",
        ),
        execution_settings=ProjectExecutionSettings(write_outputs=False),
        output_directory=output_dir,
    )
