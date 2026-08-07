"""Run a Phase 13 WDI plus WHO research project from local provider files.

This example does not download data. It expects the existing Phase 11/12 local
files under data/raw and writes only derived project outputs.
"""

from pathlib import Path

from polaris.agents.models import AgentDomain
from polaris.ingestion.models import IngestionConfiguration, IngestionRequest, UnexpectedColumnMode
from polaris.ingestion.service import ingest_dataset
from polaris.projects import (
    IngestionArtifactInput,
    ProjectHarmonizationConfig,
    ProjectReportConfig,
    ResearchProjectRequest,
    run_research_project,
)
from polaris.realdata.harmonization import (
    _phase12_question,
    _phase12_request,
    _phase12_specification,
    prepare_who_life_expectancy_extract,
    who_life_expectancy_manifest,
)
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat


def build_project(*, raw_root: Path, output_root: Path) -> ResearchProjectRequest:
    wdi_raw = raw_root / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    who_raw = raw_root / "who" / "life_expectancy_at_birth_and_age_60.csv"
    prepared = output_root / "prepared"
    wdi_prepared = prepare_wdi_validation_extract(
        source_path=wdi_raw,
        output_path=prepared / "wdi_phase13_extract.csv",
        min_year=2015,
        max_year=2021,
    )
    who_prepared = prepare_who_life_expectancy_extract(
        source_path=who_raw,
        output_path=prepared / "who_life_expectancy_phase13_extract.csv",
        min_year=2015,
        max_year=2021,
    )
    wdi_manifest = wdi_validation_manifest(prepared_path=wdi_prepared, source_path=wdi_raw)
    who_manifest = who_life_expectancy_manifest(
        prepared_path=who_prepared,
        source_path=who_raw,
    )
    configuration = IngestionConfiguration(unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE)
    wdi = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=wdi_prepared,
            expected_checksum=wdi_manifest.checksum,
            configuration=configuration,
        ),
    )
    who = ingest_dataset(
        registry=DatasetRegistry((who_manifest,)),
        request=IngestionRequest(
            dataset_id=who_manifest.dataset_id,
            source_path=who_prepared,
            expected_checksum=who_manifest.checksum,
            configuration=configuration,
        ),
    )
    harmonization = _phase12_request(wdi_result=wdi, who_result=who)
    return ResearchProjectRequest(
        project_name="WDI GDP and WHO Life Expectancy",
        research_question=_phase12_question(),
        dataset_inputs=(
            IngestionArtifactInput(ingestion_result=wdi),
            IngestionArtifactInput(ingestion_result=who),
        ),
        harmonization=ProjectHarmonizationConfig(
            dataset_configs=harmonization.dataset_configs,
            variable_mappings=harmonization.variable_mappings,
            join_type=harmonization.join_type,
            anchor_dataset_id=harmonization.anchor_dataset_id,
        ),
        statistical_specification=_phase12_specification(),
        selected_agents=(AgentDomain.ECONOMICS, AgentDomain.PUBLIC_HEALTH),
        report=ProjectReportConfig(
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 13 WDI plus WHO Research Project",
            report_subtitle="Associational country-year analysis",
            author="Polaris",
            organization="Polaris",
        ),
        output_directory=output_root / "project_outputs",
    )


if __name__ == "__main__":
    project = build_project(raw_root=Path("data/raw"), output_root=Path("examples/projects"))
    result = run_research_project(project)
    print(result.reproducibility_summary.model_dump_json(indent=2))
