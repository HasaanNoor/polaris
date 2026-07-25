from pathlib import Path
from typing import Any

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    ClaimCandidate,
    ClaimType,
    Direction,
    EvidenceArtifact,
    EvidenceProvenance,
    LimitationCode,
    RegressionCoefficientEvidenceRecord,
    SampleQualityEvidenceRecord,
)
from polaris.evidence.service import extract_evidence
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.statistics import StatisticalSpecification


def make_provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        dataset_id="agent_dataset",
        source_checksum_sha256="abc123",
        source_analysis_result_id="analysis_agent",
        statistical_procedure="ordinary_least_squares",
        phase4_schema_version="1.0.0",
        phase5_schema_version=EVIDENCE_SCHEMA_VERSION,
        extraction_timestamp="2026-07-25T00:00:00Z",
        software_version="polaris-test",
    )


def make_cross_domain_artifact(*, include_governance: bool = False) -> EvidenceArtifact:
    provenance = make_provenance()
    evidence = [
        _coefficient_record(
            evidence_id="evidence_literacy",
            variable_id="female_literacy",
            predictor_variable_ids=("female_literacy", "gdp_per_capita"),
            provenance=provenance,
        ),
        _coefficient_record(
            evidence_id="evidence_gdp",
            variable_id="gdp_per_capita",
            predictor_variable_ids=("female_literacy", "gdp_per_capita"),
            provenance=provenance,
        ),
        SampleQualityEvidenceRecord(
            evidence_id="evidence_sample",
            source_analysis_result_id="analysis_agent",
            dataset_id="agent_dataset",
            source_checksum_sha256="abc123",
            statistical_procedure="ordinary_least_squares",
            sample_size=5,
            limitation_codes=(LimitationCode.MISSING_DATA_EXCLUSION,),
            provenance=provenance,
            required_variable_ids=("fertility_rate", "female_literacy", "gdp_per_capita"),
            original_accepted_record_count=6,
            final_analysis_sample_size=5,
            excluded_row_count=1,
            exclusion_reason_counts=(("missing", 1),),
            missing_value_exclusion_count=1,
        ),
    ]
    if include_governance:
        evidence.append(
            _coefficient_record(
                evidence_id="evidence_governance",
                variable_id="government_effectiveness",
                predictor_variable_ids=("government_effectiveness", "female_literacy"),
                provenance=provenance,
            )
        )
    claims = [
        ClaimCandidate(
            claim_id="claim_literacy_fertility",
            claim_type=ClaimType.CONDITIONAL_ASSOCIATION,
            subject_variable="female_literacy",
            outcome_variable="fertility_rate",
            related_variables=("female_literacy", "gdp_per_capita"),
            direction=Direction.NEGATIVE,
            statistical_procedure="ordinary_least_squares",
            supporting_evidence_ids=("evidence_literacy",),
            limitation_codes=(
                LimitationCode.LIMITED_MODEL_SCOPE,
                LimitationCode.MISSING_DATA_EXCLUSION,
                LimitationCode.OBSERVATIONAL_ASSOCIATION,
                LimitationCode.UNSUPPORTED_GENERALIZATION,
            ),
            source_analysis_result_id="analysis_agent",
            dataset_id="agent_dataset",
            provenance=provenance,
        ),
        ClaimCandidate(
            claim_id="claim_gdp_fertility",
            claim_type=ClaimType.CONDITIONAL_ASSOCIATION,
            subject_variable="gdp_per_capita",
            outcome_variable="fertility_rate",
            related_variables=("female_literacy", "gdp_per_capita"),
            direction=Direction.NEGATIVE,
            statistical_procedure="ordinary_least_squares",
            supporting_evidence_ids=("evidence_gdp",),
            limitation_codes=(LimitationCode.OBSERVATIONAL_ASSOCIATION,),
            source_analysis_result_id="analysis_agent",
            dataset_id="agent_dataset",
            provenance=provenance,
        ),
    ]
    return EvidenceArtifact(
        artifact_id="evidence_artifact_agent",
        source_analysis_result_id="analysis_agent",
        dataset_id="agent_dataset",
        source_checksum_sha256="abc123",
        evidence_records=tuple(evidence),
        claim_candidates=tuple(claims),
        provenance=provenance,
        extraction_timestamp="2026-07-25T00:00:00Z",
        software_version="polaris-test",
    )


def make_unrelated_artifact() -> EvidenceArtifact:
    provenance = make_provenance()
    evidence = (
        _coefficient_record(
            evidence_id="evidence_weather",
            variable_id="rainfall",
            dependent_variable_id="temperature",
            predictor_variable_ids=("rainfall",),
            provenance=provenance,
        ),
    )
    return EvidenceArtifact(
        artifact_id="evidence_artifact_unrelated",
        source_analysis_result_id="analysis_agent",
        dataset_id="agent_dataset",
        source_checksum_sha256="abc123",
        evidence_records=evidence,
        claim_candidates=(),
        provenance=provenance,
        extraction_timestamp="2026-07-25T00:00:00Z",
        software_version="polaris-test",
    )


def run_integration_artifact(tmp_path: Path) -> EvidenceArtifact:
    path = tmp_path / "agents.csv"
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
    ingestion = ingest_dataset(
        registry=DatasetRegistry((_integration_manifest(),)),
        request=IngestionRequest(dataset_id="agent_integration_dataset", source_path=path),
    )
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=ingestion,
            statistical_specification=_integration_spec(),
            significance_threshold=0.05,
        )
    )
    return extract_evidence(analysis_result=result)


def _coefficient_record(
    *,
    evidence_id: str,
    variable_id: str,
    provenance: EvidenceProvenance,
    dependent_variable_id: str = "fertility_rate",
    predictor_variable_ids: tuple[str, ...] = ("female_literacy",),
) -> RegressionCoefficientEvidenceRecord:
    return RegressionCoefficientEvidenceRecord(
        evidence_id=evidence_id,
        source_analysis_result_id="analysis_agent",
        dataset_id="agent_dataset",
        source_checksum_sha256="abc123",
        statistical_procedure="ordinary_least_squares",
        sample_size=5,
        limitation_codes=(LimitationCode.LIMITED_MODEL_SCOPE,),
        provenance=provenance,
        dependent_variable_id=dependent_variable_id,
        term=variable_id,
        variable_id=variable_id,
        estimate=-0.1,
        standard_error=0.01,
        test_statistic=-10.0,
        p_value=0.001,
        confidence_interval_low=-0.2,
        confidence_interval_high=-0.01,
        below_significance_threshold=True,
        direction=Direction.NEGATIVE,
        is_intercept=False,
        model_result_id="analysis_agent",
        predictor_variable_ids=predictor_variable_ids,
    )


def _integration_manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "agent_integration_dataset",
            "title": "Agent Integration Dataset",
            "provider": "Test Provider",
            "source_url": "https://example.test/agents",
            "status": "candidate",
            "geographic_coverage": {"codes": ["TEST"]},
            "temporal_coverage": {"start": 2020, "end": 2020},
            "variables": [
                _variable("country", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("fertility_rate", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("female_literacy", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("gdp_per_capita", DataType.FLOAT, VariableRole.COVARIATE),
            ],
        }
    )


def _integration_spec() -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": "spec_agent_integration",
        "investigation_id": "investigation_agents",
        "analysis_type": "regression",
        "model_family": "linear",
        "procedure": "ordinary_least_squares",
        "outcome_variable": {"variable_id": "fertility_rate"},
        "exposure_variables": [{"variable_id": "female_literacy"}],
        "covariates": [{"variable_id": "gdp_per_capita"}],
        "unit_of_analysis": "country",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "Phase 6 integration fixture",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": "associational",
    }
    return StatisticalSpecification.model_validate(payload)


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "label": variable_id,
        "data_type": data_type,
        "role": role,
    }
