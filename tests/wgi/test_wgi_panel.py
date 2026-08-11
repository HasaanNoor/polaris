from __future__ import annotations

import csv
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from polaris.agents.models import AgentDomain
from polaris.harmonization import (
    DatasetHarmonizationConfig,
    HarmonizationRequest,
    JoinType,
    VariableMapping,
    harmonize_datasets,
)
from polaris.ingestion.loader import calculate_sha256
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.projects import (
    IngestionArtifactInput,
    ProjectHarmonizationConfig,
    run_research_project,
)
from polaris.projects.models import ProjectReportConfig, ProjectStatus, ResearchProjectRequest
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
from polaris.schemas.dataset import DatasetManifest, DatasetVariable
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification
from polaris.wgi import (
    build_wgi_governance_panel,
    export_wgi_governance_panel,
    wgi_mapping_registry,
)
from polaris.wgi.acquisition import wgi_dimension_download_url
from polaris.wgi.models import WGI_SOURCE_ID, WGISnapshotReference
from polaris.wgi.profiling import profile_wgi_schema


def test_official_dimension_download_url_uses_world_bank_source() -> None:
    url = wgi_dimension_download_url("GE")
    assert url.startswith("https://api.worldbank.org/v2/country/all/indicator/")
    assert f"source={WGI_SOURCE_ID}" in url
    assert "GOV_WGI_GE.EST" in url
    assert "downloadformat=csv" in url
    assert "dataformat=list" in url


def test_mappings_preserve_all_six_official_dimensions() -> None:
    mappings = wgi_mapping_registry()
    assert [mapping.canonical_variable_id for mapping in mappings] == [
        "wgi_voice_accountability",
        "wgi_political_stability",
        "wgi_government_effectiveness",
        "wgi_regulatory_quality",
        "wgi_rule_of_law",
        "wgi_control_corruption",
    ]
    assert {mapping.official_estimate_indicator_id for mapping in mappings} == {
        "GOV_WGI_VA.EST",
        "GOV_WGI_PV.EST",
        "GOV_WGI_GE.EST",
        "GOV_WGI_RQ.EST",
        "GOV_WGI_RL.EST",
        "GOV_WGI_CC.EST",
    }
    assert all(mapping.definition for mapping in mappings)
    assert len({mapping.ruleset_version for mapping in mappings}) == 1


def test_profile_detects_schema_fields_missingness_and_entities(tmp_path: Path) -> None:
    snapshots = _snapshots(tmp_path)
    profile = profile_wgi_schema(snapshots=snapshots)
    assert profile.country_identifier_field == "Country Code"
    assert profile.year_field == "Year"
    assert profile.indicator_identifier_field == "Indicator Code"
    assert profile.estimate_field == "Value"
    assert "GOV_WGI_GE.SE" in profile.standard_error_indicators
    assert "GOV_WGI_GE.SC_LB" in profile.confidence_bound_indicators
    assert "GOV_WGI_GE.SR" in profile.source_count_indicators
    assert profile.percentile_rank_indicators == ()
    assert profile.year_range == (2020, 2021)
    assert profile.territory_count > 0
    assert profile.missingness_by_indicator["GOV_WGI_GE.EST"] == 1


def test_panel_preserves_estimates_uncertainty_provenance_and_identity(tmp_path: Path) -> None:
    snapshots = _snapshots(tmp_path)
    panel = build_wgi_governance_panel(snapshots=snapshots)
    again = build_wgi_governance_panel(snapshots=snapshots)
    assert panel.panel_id == again.panel_id
    assert panel.quality_summary.analysis_ready is True
    assert panel.quality_summary.integrated_variable_count == 6
    assert panel.quality_summary.territory_exclusions > 0
    assert panel.quality_summary.aggregate_exclusions > 0
    assert panel.records[0].canonical_country_code == "AFG"
    ge_2020 = next(
        record
        for record in panel.records
        if record.canonical_country_code == "AFG" and record.year == 2020
    )
    assert ge_2020.values["wgi_government_effectiveness"] == -0.8
    assert ge_2020.uncertainty_metadata["wgi_government_effectiveness"]["standard_error"] == 0.2
    assert ge_2020.uncertainty_metadata["wgi_government_effectiveness"]["governance_score"] == 34.2
    assert ge_2020.uncertainty_metadata["wgi_government_effectiveness"]["percentile_rank"] is None
    provenance = ge_2020.value_provenance["wgi_government_effectiveness"]
    assert provenance.official_wgi_indicator_id == "GOV_WGI_GE.EST"
    assert provenance.normalized_estimate == -0.8
    assert provenance.standard_error == 0.2
    assert provenance.number_of_sources == 7


def test_changed_source_checksum_changes_panel_identity(tmp_path: Path) -> None:
    snapshots = _snapshots(tmp_path)
    changed_path = _write_wgi_zip(tmp_path / "changed", "VA", changed=True)
    changed = (
        snapshots[0].model_copy(
            update={
                "snapshot_path": changed_path,
                "checksum_sha256": calculate_sha256(changed_path),
            }
        ),
        *snapshots[1:],
    )
    assert (
        build_wgi_governance_panel(snapshots=snapshots).panel_id
        != build_wgi_governance_panel(snapshots=changed).panel_id
    )


def test_export_reenters_phase3_and_orders_columns(tmp_path: Path) -> None:
    panel = build_wgi_governance_panel(snapshots=_snapshots(tmp_path))
    exported = export_wgi_governance_panel(panel=panel, output_dir=tmp_path, write_provenance=False)
    with exported.csv_path.open(newline="", encoding="utf-8") as file:
        header = next(csv.reader(file))
    assert header == [
        "country_code",
        "country_name",
        "year",
        "wgi_control_corruption",
        "wgi_government_effectiveness",
        "wgi_political_stability",
        "wgi_regulatory_quality",
        "wgi_rule_of_law",
        "wgi_voice_accountability",
    ]
    manifest = DatasetManifest.model_validate_json(exported.manifest_path.read_text())
    result = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=exported.csv_path,
            expected_checksum=manifest.checksum,
        ),
    )
    assert result.validation_report.analysis_ready is True


def test_phase12_accepts_wdi_wgi_and_wdi_who_wgi_generically(tmp_path: Path) -> None:
    wgi = _ingest_wgi(tmp_path)
    wdi = _ingest_small_dataset(tmp_path, "wdi")
    who = _ingest_small_dataset(tmp_path, "who")
    wdi_wgi = harmonize_datasets(request=_wdi_wgi_request(wdi, wgi))
    wdi_who_wgi = harmonize_datasets(request=_wdi_who_wgi_request(wdi, who, wgi))
    assert wdi_wgi.quality_summary.analysis_ready is True
    assert wdi_who_wgi.quality_summary.analysis_ready is True
    assert "wgi_government_effectiveness" in wdi_who_wgi.quality_summary.variables_represented


def test_phase13_project_uses_governance_economics_public_health(tmp_path: Path) -> None:
    wgi = _ingest_wgi(tmp_path)
    wdi = _ingest_small_dataset(tmp_path, "wdi")
    who = _ingest_small_dataset(tmp_path, "who")
    hrequest = _wdi_who_wgi_request(wdi, who, wgi)
    result = run_research_project(
        ResearchProjectRequest(
            project_name="WGI project test",
            research_question=ResearchQuestion(
                question_id="rq_wgi_project",
                raw_text=(
                    "How is government effectiveness associated with life expectancy "
                    "after accounting for GDP per capita?"
                ),
                category=QuestionCategory.CORRELATIONAL,
                outcome_variables=[
                    VariableReference(variable_id="who_life_expectancy_at_birth_both_sexes")
                ],
                exposure_variables=[
                    VariableReference(variable_id="wgi_government_effectiveness"),
                    VariableReference(variable_id="wdi_gdp_per_capita_current_usd"),
                ],
                population="Synthetic country-year rows",
                geographic_scope=GeographicScope(codes=["TEST"]),
                temporal_scope=TemporalScope(start=2020, end=2021),
                unit_of_analysis="country-year",
                requested_evidence_level=EvidenceStrength.LIMITED,
                requested_analytical_methods=["ordinary_least_squares"],
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
            statistical_specification=_specification(),
            selected_agents=(
                AgentDomain.GOVERNANCE,
                AgentDomain.ECONOMICS,
                AgentDomain.PUBLIC_HEALTH,
            ),
            report=ProjectReportConfig(output_format=ReportFormat.MARKDOWN),
            output_directory=tmp_path / "outputs",
        )
    )
    assert result.overall_status is ProjectStatus.COMPLETED
    assert [assessment.agent_domain for assessment in result.domain_assessments] == [
        AgentDomain.GOVERNANCE,
        AgentDomain.ECONOMICS,
        AgentDomain.PUBLIC_HEALTH,
    ]
    governance = result.domain_assessments[0]
    assert governance.coverage_summary.relevant_evidence_count > 0


def _snapshots(tmp_path: Path) -> tuple[WGISnapshotReference, ...]:
    paths = [
        _write_wgi_zip(tmp_path, mapping.official_dimension_code)
        for mapping in wgi_mapping_registry()
    ]
    return tuple(
        WGISnapshotReference(
            snapshot_path=path,
            source_url=wgi_dimension_download_url(_dimension_from_path(path)),
            checksum_sha256=calculate_sha256(path),
            original_filename=path.name,
            downloaded_at=datetime(2026, 8, 11, tzinfo=UTC),
            dimension_code=_dimension_from_path(path),
        )
        for path in paths
    )


def _write_wgi_zip(tmp_path: Path, dimension: str, *, changed: bool = False) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / f"wgi_{dimension}.zip"
    label = next(
        m.canonical_label for m in wgi_mapping_registry() if m.official_dimension_code == dimension
    )
    rows = []
    values = {
        ("AFG", "Afghanistan", 2020): -0.81 if changed else -0.8,
        ("AFG", "Afghanistan", 2021): -0.7,
        ("ALB", "Albania", 2020): 0.1,
        ("ALB", "Albania", 2021): 0.2,
        ("CHN", "China", 2020): -0.1,
        ("CHN", "China", 2021): 0.0,
        ("IND", "India", 2020): -0.2,
        ("IND", "India", 2021): -0.1,
        ("PAK", "Pakistan", 2020): -0.6,
        ("PAK", "Pakistan", 2021): -0.5,
        ("USA", "United States", 2020): 1.2,
        ("USA", "United States", 2021): 1.1,
        ("ABW", "Aruba", 2020): 0.5,
        ("WLD", "World", 2020): 0.0,
    }
    for suffix in ("EST", "SE", "SR", "SC", "SC_LB", "SC_UB"):
        indicator = f"GOV_WGI_{dimension}.{suffix}"
        name = _indicator_name(label, suffix)
        for (code, country, year), estimate in values.items():
            value = _companion_value(suffix, estimate)
            if dimension == "GE" and suffix == "EST" and code == "ALB" and year == 2021:
                value = ""
            rows.append([country, code, name, indicator, str(year), str(value)])
    with zipfile.ZipFile(path, "w") as archive:
        data = [
            ["Data Source", "Worldwide Governance Indicators"],
            [],
            ["Last Updated Date", "2026-03-18"],
            [],
            ["Country Name", "Country Code", "Indicator Name", "Indicator Code", "Year", "Value"],
            *rows,
        ]
        archive.writestr("API_Download_DS3_EN_csv_v2_LIST.csv", _csv_text(data))
        archive.writestr(
            "Metadata_Indicator_API_Download_DS3_EN_csv_v2_LIST.csv",
            _csv_text([["INDICATOR_CODE", "INDICATOR_NAME", "SOURCE_NOTE", "SOURCE_ORGANIZATION"]]),
        )
    return path


def _csv_text(rows: list[list[str]]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def _indicator_name(label: str, suffix: str) -> str:
    names = {
        "EST": f"{label} - Governance estimate (approx. -2.5 to +2.5)",
        "SE": f"{label} - Standard error of the governance estimate",
        "SR": f"{label} - Number of sources",
        "SC": f"{label} - Governance score (0-100)",
        "SC_LB": f"{label} - Lower bound of the 90% confidence interval for the governance score",
        "SC_UB": f"{label} - Upper bound of the 90% confidence interval for the governance score",
    }
    return names[suffix]


def _companion_value(suffix: str, estimate: float) -> str | float:
    return {
        "EST": estimate,
        "SE": 0.2,
        "SR": 7,
        "SC": 35 + estimate,
        "SC_LB": 30 + estimate,
        "SC_UB": 40 + estimate,
    }[suffix]


def _dimension_from_path(path: Path) -> str:
    return path.stem.split("_", 1)[1]


def _ingest_wgi(tmp_path: Path):
    panel = build_wgi_governance_panel(snapshots=_snapshots(tmp_path))
    exported = export_wgi_governance_panel(
        panel=panel,
        output_dir=tmp_path / "wgi_export",
        write_provenance=False,
    )
    manifest = DatasetManifest.model_validate_json(exported.manifest_path.read_text())
    return ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=exported.csv_path,
            expected_checksum=manifest.checksum,
        ),
    )


def _ingest_small_dataset(tmp_path: Path, name: str):
    path = tmp_path / f"{name}.csv"
    variables = {
        "wdi": ("gdp_per_capita_current_usd", "GDP per capita", "current US dollars"),
        "who": ("who_life_expectancy_at_birth", "Life expectancy", "years"),
    }
    variable_id, label, unit = variables[name]
    values = {
        ("AFG", "Afghanistan", 2020): 500.0 if name == "wdi" else 62.0,
        ("AFG", "Afghanistan", 2021): 520.0 if name == "wdi" else 63.0,
        ("ALB", "Albania", 2020): 5300.0 if name == "wdi" else 78.0,
        ("CHN", "China", 2020): 10500.0 if name == "wdi" else 77.0,
        ("CHN", "China", 2021): 12600.0 if name == "wdi" else 78.0,
        ("IND", "India", 2020): 1900.0 if name == "wdi" else 70.0,
        ("IND", "India", 2021): 2200.0 if name == "wdi" else 71.0,
        ("PAK", "Pakistan", 2020): 1400.0 if name == "wdi" else 66.0,
        ("PAK", "Pakistan", 2021): 1500.0 if name == "wdi" else 67.0,
        ("USA", "United States", 2020): 63000.0 if name == "wdi" else 77.0,
        ("USA", "United States", 2021): 65000.0 if name == "wdi" else 78.0,
    }
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["country_code", "country_name", "year", variable_id],
        )
        writer.writeheader()
        for (code, country, year), value in sorted(values.items()):
            writer.writerow(
                {"country_code": code, "country_name": country, "year": year, variable_id: value}
            )
    checksum = calculate_sha256(path)
    manifest = DatasetManifest(
        dataset_id=f"{name}_{checksum[:12]}",
        title=f"{name} fixture",
        provider=name,
        source_url="https://example.invalid/local-fixture",
        access_url=str(path),
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(codes=["TEST"]),
        temporal_coverage=TemporalScope(start=2020, end=2021),
        variables=[
            DatasetVariable(
                variable_id="country_code",
                label="Country",
                data_type=DataType.STRING,
                role=VariableRole.IDENTIFIER,
            ),
            DatasetVariable(
                variable_id="country_name",
                label="Country name",
                data_type=DataType.STRING,
                role=VariableRole.IDENTIFIER,
            ),
            DatasetVariable(
                variable_id="year",
                label="Year",
                data_type=DataType.INTEGER,
                role=VariableRole.TIME,
            ),
            DatasetVariable(
                variable_id=variable_id,
                label=label,
                data_type=DataType.FLOAT,
                role=VariableRole.OUTCOME,
                unit=unit,
            ),
        ],
        checksum=checksum,
    )
    return ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=path,
            expected_checksum=checksum,
        ),
    )


def _wdi_wgi_request(wdi, wgi) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi, wgi),
        dataset_configs=(_config(wdi, "wdi", "world_bank"), _config(wgi, "wgi", "world_bank")),
        variable_mappings=(_wdi_mapping(wdi), _wgi_mapping(wgi)),
        join_type=JoinType.INNER,
    )


def _wdi_who_wgi_request(wdi, who, wgi) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi, who, wgi),
        dataset_configs=(
            _config(wdi, "wdi", "world_bank"),
            _config(who, "who", "who"),
            _config(wgi, "wgi", "world_bank"),
        ),
        variable_mappings=(_wdi_mapping(wdi), _who_mapping(who), _wgi_mapping(wgi)),
        join_type=JoinType.INNER,
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


def _wdi_mapping(result) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="world_bank",
        source_variable_id="gdp_per_capita_current_usd",
        source_field_name="gdp_per_capita_current_usd",
        canonical_variable_id="wdi_gdp_per_capita_current_usd",
        canonical_label="GDP per capita",
        source_unit="current US dollars",
        canonical_unit="current US dollars",
        conceptual_definition="GDP per capita.",
        expected_data_type="float",
    )


def _who_mapping(result) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="who",
        source_variable_id="who_life_expectancy_at_birth",
        source_field_name="who_life_expectancy_at_birth",
        canonical_variable_id="who_life_expectancy_at_birth_both_sexes",
        canonical_label="Life expectancy",
        source_unit="years",
        canonical_unit="years",
        conceptual_definition="Life expectancy.",
        expected_data_type="float",
    )


def _wgi_mapping(result) -> VariableMapping:
    return VariableMapping(
        source_dataset_id=result.dataset_manifest.dataset_id,
        source_provider="world_bank_wgi",
        source_variable_id="wgi_government_effectiveness",
        source_field_name="wgi_government_effectiveness",
        canonical_variable_id="wgi_government_effectiveness",
        canonical_label="WGI government effectiveness",
        source_unit="standard normal governance estimate",
        canonical_unit="standard normal governance estimate",
        conceptual_definition="WGI government effectiveness central estimate.",
        expected_data_type="float",
    )


def _specification() -> StatisticalSpecification:
    return StatisticalSpecification.model_validate(
        {
            "specification_id": "spec_wgi_project",
            "investigation_id": "investigation_wgi_project",
            "analysis_type": StatisticalAnalysisType.CORRELATION,
            "model_family": StatisticalModelFamily.LINEAR,
            "procedure": StatisticalProcedure.ORDINARY_LEAST_SQUARES,
            "outcome_variable": {"variable_id": "who_life_expectancy_at_birth_both_sexes"},
            "exposure_variables": [
                {"variable_id": "wgi_government_effectiveness"},
                {"variable_id": "wdi_gdp_per_capita_current_usd"},
            ],
            "unit_of_analysis": "country-year",
            "missing_data_strategy": {"strategy": "complete_case", "rationale": "test"},
            "confidence_level": 0.95,
            "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
        }
    )
