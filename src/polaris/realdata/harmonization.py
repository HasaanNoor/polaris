"""Phase 12 real-data harmonization example using local provider files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from polaris.agents.service import run_all_domain_agents
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.coordination.service import coordinate_assessments
from polaris.evidence.service import extract_evidence
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
from polaris.realdata.wdi import prepare_wdi_validation_extract, wdi_validation_manifest
from polaris.registry import DatasetRegistry
from polaris.reporting.models import ReportFormat, ReportRequest
from polaris.reporting.service import generate_report
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
from polaris.synthesis.models import SynthesisMode, SynthesisRequest
from polaris.synthesis.service import synthesize_assessment


def run_phase12_real_harmonization_example(
    *,
    raw_root: str | Path = "data/raw",
    output_root: str | Path = "examples/harmonization",
) -> dict[str, Any]:
    """Create and validate a small WDI+WHO country-year harmonization artifact."""

    raw = Path(raw_root)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    wdi_raw = raw / "world_bank" / "WDI_CSV" / "WDICSV.csv"
    who_raw = raw / "who" / "life_expectancy_at_birth_and_age_60.csv"
    wdi_prepared = prepare_wdi_validation_extract(
        source_path=wdi_raw,
        output_path=output / "phase12_wdi_extract.csv",
        min_year=2015,
        max_year=2021,
    )
    who_prepared = prepare_who_life_expectancy_extract(
        source_path=who_raw,
        output_path=output / "phase12_who_life_expectancy_extract.csv",
        min_year=2015,
        max_year=2021,
    )
    wdi_manifest = wdi_validation_manifest(prepared_path=wdi_prepared, source_path=wdi_raw)
    who_manifest = who_life_expectancy_manifest(prepared_path=who_prepared, source_path=who_raw)
    wdi_result = ingest_dataset(
        registry=DatasetRegistry((wdi_manifest,)),
        request=IngestionRequest(
            dataset_id=wdi_manifest.dataset_id,
            source_path=wdi_prepared,
            expected_checksum=wdi_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    who_result = ingest_dataset(
        registry=DatasetRegistry((who_manifest,)),
        request=IngestionRequest(
            dataset_id=who_manifest.dataset_id,
            source_path=who_prepared,
            expected_checksum=who_manifest.checksum,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )
    harmonized = harmonize_datasets(
        request=_phase12_request(wdi_result=wdi_result, who_result=who_result)
    )
    manifest = export_harmonized_dataset(
        harmonized=harmonized,
        csv_path=output / "harmonized_country_year_sample.csv",
        manifest_path=output / "harmonized_country_year_manifest.json",
        summary_path=output / "harmonization_summary.json",
    )
    harmonized_ingestion = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(
            dataset_id=manifest.dataset_id,
            source_path=output / "harmonized_country_year_sample.csv",
            expected_checksum=manifest.checksum,
        ),
    )
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=harmonized_ingestion,
            statistical_specification=_phase12_specification(),
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
            ingestion_result=harmonized_ingestion,
            research_question=_phase12_question(),
            dataset_manifest=manifest,
            output_format=ReportFormat.MARKDOWN,
            report_title="Phase 12 Harmonized Country-Year Validation Report",
            report_subtitle="Derived WDI plus WHO official local extracts",
            author="Polaris",
            organization="Polaris",
        )
    )
    if report.rendered_content is not None:
        (output / "harmonized_phase12_report.md").write_text(
            report.rendered_content,
            encoding="utf-8",
        )
    payload = {
        "harmonized_dataset_id": harmonized.harmonized_dataset_id,
        "wdi_dataset_id": wdi_result.dataset_manifest.dataset_id,
        "who_dataset_id": who_result.dataset_manifest.dataset_id,
        "harmonized_manifest_id": manifest.dataset_id,
        "harmonized_checksum": manifest.checksum,
        "value_provenance_count": len(harmonized.value_level_provenance),
        "quality_summary": harmonized.quality_summary.model_dump(mode="json"),
        "analysis_result_id": analysis.result_id,
        "evidence_artifact_id": evidence.artifact_id,
        "coordinated_assessment_id": coordinated.coordinated_assessment_id,
        "synthesis_artifact_id": synthesis.synthesis_id,
        "report_id": report.report.report_id,
        "integrated_variables": tuple(
            entry.canonical_variable_id for entry in harmonized.canonical_variable_catalog
        ),
        "deferred_provider_files": _deferred_files(),
    }
    (output / "phase12_pipeline_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return payload


def prepare_who_life_expectancy_extract(
    *,
    source_path: str | Path,
    output_path: str | Path,
    min_year: int,
    max_year: int,
) -> Path:
    """Filter WHO GHO life expectancy to annual country both-sex birth records."""

    source = Path(source_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("country_code", "country_name", "year", "who_life_expectancy_at_birth")
    rows: list[dict[str, str]] = []
    with source.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("IndicatorCode") != "WHOSIS_000001":
                continue
            if row.get("Dim1ValueCode") != "SEX_BTSX":
                continue
            if row.get("Location type") != "Country" or row.get("Period type") != "Year":
                continue
            year_text = (row.get("Period") or "").strip()
            if not year_text.isdigit():
                continue
            year = int(year_text)
            if year < min_year or year > max_year:
                continue
            rows.append(
                {
                    "country_code": (row.get("SpatialDimValueCode") or "").strip(),
                    "country_name": (row.get("Location") or "").strip(),
                    "year": year_text,
                    "who_life_expectancy_at_birth": (row.get("FactValueNumeric") or "").strip(),
                }
            )
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda item: (item["country_code"], item["year"])))
    return destination


def who_life_expectancy_manifest(
    *,
    prepared_path: str | Path,
    source_path: str | Path,
) -> DatasetManifest:
    checksum = calculate_sha256(prepared_path)
    return DatasetManifest(
        dataset_id=f"who_life_expectancy_phase12_{checksum[:12]}",
        title="WHO Life Expectancy Phase 12 Extract",
        provider="World Health Organization",
        source_url="https://www.who.int/data/gho",
        access_url=str(prepared_path),
        description=(
            "Phase 12 reviewed extract from the locally downloaded WHO GHO life expectancy "
            f"file. Original source file: {Path(source_path)}. Filtered to WHOSIS_000001, "
            "both sexes, location type Country, annual Period records."
        ),
        license="WHO data terms and conditions",
        status=DatasetStatus.REVIEWED_CANDIDATE,
        geographic_coverage=GeographicScope(codes=["GLOBAL_HEALTH"]),
        temporal_coverage=TemporalScope(start=2015, end=2021, label="Annual country records"),
        revision_metadata=RevisionMetadata(update_frequency="provider snapshot"),
        variables=[
            DatasetVariable(
                variable_id="country_code",
                label="WHO spatial dimension value code",
                data_type=DataType.STRING,
                role=VariableRole.IDENTIFIER,
                source_field_name="country_code",
            ),
            DatasetVariable(
                variable_id="country_name",
                label="Country name",
                data_type=DataType.STRING,
                role=VariableRole.IDENTIFIER,
                source_field_name="country_name",
            ),
            DatasetVariable(
                variable_id="year",
                label="Year",
                data_type=DataType.INTEGER,
                role=VariableRole.TIME,
                source_field_name="year",
            ),
            DatasetVariable(
                variable_id="who_life_expectancy_at_birth",
                label="WHO life expectancy at birth, both sexes",
                description="WHO GHO WHOSIS_000001, both sexes, annual country records.",
                unit="years",
                data_type=DataType.FLOAT,
                role=VariableRole.OUTCOME,
                source_field_name="who_life_expectancy_at_birth",
            ),
        ],
        units=["country-year"],
        frequency="annual",
        methodology_reference="https://www.who.int/data/gho/indicator-metadata-registry",
        checksum=checksum,
    )


def _phase12_request(
    *,
    wdi_result,
    who_result,
) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi_result, who_result),
        dataset_configs=(
            DatasetHarmonizationConfig(
                dataset_id=wdi_result.dataset_manifest.dataset_id,
                alias="wdi",
                provider="world_bank",
                country_field="country_code",
                country_name_field="country_name",
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
                source_variable_id="gdp_per_capita_current_usd",
                source_field_name="gdp_per_capita_current_usd",
                canonical_variable_id="wdi_gdp_per_capita_current_usd",
                canonical_label="GDP per capita, current US dollars",
                source_unit="current US dollars",
                canonical_unit="current US dollars",
                conceptual_definition="WDI GDP per capita in current US dollars.",
                expected_data_type="float",
            ),
            VariableMapping(
                source_dataset_id=who_result.dataset_manifest.dataset_id,
                source_provider="who",
                source_variable_id="who_life_expectancy_at_birth",
                source_field_name="who_life_expectancy_at_birth",
                canonical_variable_id="who_life_expectancy_at_birth_both_sexes",
                canonical_label="WHO life expectancy at birth, both sexes",
                source_unit="years",
                canonical_unit="years",
                conceptual_definition=(
                    "WHO GHO WHOSIS_000001 life expectancy at birth, both sexes, in years."
                ),
                expected_data_type="float",
            ),
        ),
        join_type=JoinType.LEFT,
        anchor_dataset_id=wdi_result.dataset_manifest.dataset_id,
        temporal_scope=TemporalScope(start=2015, end=2021),
    )


def _phase12_specification() -> StatisticalSpecification:
    return StatisticalSpecification.model_validate(
        {
            "specification_id": "spec_phase12_harmonized_real_validation",
            "investigation_id": "investigation_phase12_harmonized_real_validation",
            "analysis_type": StatisticalAnalysisType.CORRELATION,
            "model_family": StatisticalModelFamily.NONE,
            "procedure": StatisticalProcedure.PEARSON_CORRELATION,
            "outcome_variable": {"variable_id": "who_life_expectancy_at_birth_both_sexes"},
            "exposure_variables": [{"variable_id": "wdi_gdp_per_capita_current_usd"}],
            "unit_of_analysis": "country-year",
            "missing_data_strategy": {
                "strategy": "complete_case",
                "rationale": "Phase 12 validates derived harmonized country-year export.",
            },
            "confidence_level": 0.95,
            "causal_identification_claim_level": CausalIdentificationLevel.ASSOCIATIONAL,
        }
    )


def _phase12_question() -> ResearchQuestion:
    return ResearchQuestion(
        question_id="rq_phase12_harmonized_real_validation",
        raw_text=(
            "How is WDI GDP per capita associated with WHO life expectancy at birth in "
            "the Phase 12 harmonized country-year extract?"
        ),
        category=QuestionCategory.CORRELATIONAL,
        outcome_variables=[
            VariableReference(variable_id="who_life_expectancy_at_birth_both_sexes")
        ],
        exposure_variables=[VariableReference(variable_id="wdi_gdp_per_capita_current_usd")],
        population="Country-year observations in the derived WDI plus WHO harmonized extract",
        geographic_scope=GeographicScope(codes=["GLOBAL"], description="Country-level records"),
        temporal_scope=TemporalScope(start=2015, end=2021, label="Annual observations"),
        unit_of_analysis="country-year",
        requested_evidence_level=EvidenceStrength.LIMITED,
        requested_analytical_methods=["pearson_correlation"],
        assumptions=["Associational validation only"],
        exclusions=["No imputation, fuzzy matching, unit conversion, or causal inference"],
        created_at="2026-08-06T00:00:00Z",
    )


def _deferred_files() -> tuple[dict[str, str], ...]:
    return (
        {
            "path": "data/raw/who/HALE_at_birth_and_age_60.csv",
            "reason": "Compatible row shape, deferred to keep Phase 12 initial subset small.",
        },
        {
            "path": "data/raw/who/mortality_rates_global.csv",
            "reason": "Global aggregate export, not country observations.",
        },
        {
            "path": "data/raw/who/mortality_rates_*country_or_region*.csv",
            "reason": "Country-specific or regional exports, not global country-year panel.",
        },
        {
            "path": "data/raw/unesco/DEM",
            "reason": "National rows are structured but indicator subset units need review.",
        },
        {
            "path": "data/raw/unesco/SDG",
            "reason": "Large multi-indicator archive; only schema-profiled in Phase 12.",
        },
        {
            "path": "data/raw/unesco/SCN-SDG",
            "reason": "Science indicator definitions and metadata require explicit mapping review.",
        },
        {
            "path": "data/raw/unesco/SDG11",
            "reason": "Culture expenditure units are clear for some variables but out of scope.",
        },
    )
