from __future__ import annotations

import json
from pathlib import Path

import pytest

from polaris.analysis.causal.models import CausalMethod
from polaris.causal_studies import (
    CausalStudyRegistry,
    CausalStudySearchQuery,
    assess_design_readiness,
    build_causal_specification,
    load_causal_study_registry,
)
from polaris.causal_studies.compatibility import (
    comparison_group_diagnostics,
    inspect_dataset_compatibility,
    pre_post_coverage,
    staggered_treatment_status,
)
from polaris.causal_studies.conversion import StudyConversionError
from polaris.causal_studies.errors import CausalStudyNotFoundError
from polaris.causal_studies.models import (
    AnnualTimingRule,
    CausalStudyDefinition,
    InterventionDefinition,
    ReviewStatus,
    StudyVariableReference,
    TreatmentAssignment,
    TreatmentSource,
)
from polaris.causal_studies.validation import validate_study
from polaris.evidence.service import extract_evidence
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.mcp.resources import MCPResourceStore
from polaris.mcp.tools import MCPToolService
from polaris.projects.models import IngestionArtifactInput
from polaris.projects.planning import plan_research_project
from polaris.registry import DatasetRegistry
from polaris.reporting.sections import causal_design_section
from polaris.schemas.common import DataType, VariableReference, VariableRole
from polaris.schemas.dataset import DatasetManifest
from tests.analysis.causal.conftest import causal_spec, statistical_spec, synthetic_causal_ingestion
from tests.projects.helpers import base_request


def test_models_validate_timing_sources_entities_and_review_status():
    study = _study()

    assert study.intervention.intervention_type == "health_policy"
    assert study.sources[0].quality_category == "primary_official"
    assert validate_study(study) == ()

    with pytest.raises(ValueError):
        TreatmentAssignment(
            entity_id="Brazil",
            treatment_status="treated",
            treatment_start=2020,
            assignment_source_ids=("src1",),
        )
    missing_source = study.model_copy(update={"source_ids": ("missing",)})
    assert any(item.code == "missing_source_reference" for item in validate_study(missing_source))


def test_registry_loading_search_duplicates_and_stable_order(tmp_path: Path):
    study = _study(study_id="study_b")
    other = _study(study_id="study_a", intervention_id="intervention_a", treated=("ARG",))
    _write_registry(tmp_path, [study, other])

    registry = load_causal_study_registry(tmp_path)
    assert [item.study_id for item in registry.list_studies()] == ["study_a", "study_b"]
    assert registry.get_study("study_b").title
    with pytest.raises(CausalStudyNotFoundError):
        registry.get_study("missing")
    result = registry.search(
        CausalStudySearchQuery(
            intervention_types=("health_policy",),
            treated_entities=("BRA",),
            treatment_years=(2020,),
            providers=("Test Provider",),
            review_statuses=(ReviewStatus.DESIGN_READY,),
        )
    )
    assert [item.study_id for item in result] == ["study_b"]

    duplicate = CausalStudyRegistry([study, study])
    assert any(item.code == "duplicate_study_id" for item in duplicate.registry_findings())


def test_sources_assignment_linkage_and_missing_references():
    study = _study()
    broken = study.model_copy(
        update={
            "treatment_assignments": (
                TreatmentAssignment(
                    entity_id="BRA",
                    treatment_status="treated",
                    treatment_start=2020,
                    assignment_source_ids=("missing",),
                    review_status=ReviewStatus.DESIGN_READY,
                ),
            )
        }
    )
    findings = validate_study(broken)
    assert any(item.code == "missing_source_reference" for item in findings)
    assert any(item.entity_id == "BRA" for item in findings)


def test_compatibility_coverage_controls_and_staggered(tmp_path: Path):
    ingestion = _ingestion(tmp_path)
    study = _study()
    registry = DatasetRegistry((ingestion.dataset_manifest,))

    compatibility = inspect_dataset_compatibility(
        study, registry=registry, ingestion_results=(ingestion,)
    )[0]
    assert compatibility.outcome_variables_available == ("y",)
    assert compatibility.covariates_available == ("x",)
    assert compatibility.missing_entities == ()

    missing_outcome = study.model_copy(
        update={
            "proposed_outcomes": (
                StudyVariableReference(
                    variable_id="missing",
                    dataset_id="study_panel",
                    role="outcome",
                    provider="Test Provider",
                ),
            )
        }
    )
    assert inspect_dataset_compatibility(missing_outcome, registry=registry)[0].findings[
        0
    ].code == ("outcome_not_available")

    coverage = pre_post_coverage(study, ingestion_results=(ingestion,), dataset_id="study_panel")
    assert coverage.treated_entities_with_sufficient_coverage == ("BRA",)
    assert coverage.control_entities_with_sufficient_coverage == ("ARG", "CHL")

    no_pre = _study(pre_periods=3)
    assert any(
        item.code == "insufficient_pre_periods"
        for item in pre_post_coverage(no_pre, ingestion_results=(ingestion,)).findings
    )
    controls = comparison_group_diagnostics(study, ingestion_results=(ingestion,))
    assert controls.explicit_control_entities == ("ARG", "CHL")
    assert "BRA" not in controls.candidate_never_treated_entities

    staggered = _study(treated=("BRA", "CHL"), starts={"BRA": 2020, "CHL": 2021})
    assert staggered_treatment_status(staggered) == "staggered_unsupported"


def test_readiness_statuses_and_deterministic_assessment(tmp_path: Path):
    ingestion = _ingestion(tmp_path)
    registry = DatasetRegistry((ingestion.dataset_manifest,))
    ready = assess_design_readiness(
        _study(), registry=registry, ingestion_results=(ingestion,), dataset_id="study_panel"
    )
    assert ready.readiness_status == "ready"
    assert ready == assess_design_readiness(
        _study(), registry=registry, ingestion_results=(ingestion,), dataset_id="study_panel"
    )

    warning = assess_design_readiness(
        _study(post_treatment_covariate=True),
        registry=registry,
        ingestion_results=(ingestion,),
        dataset_id="study_panel",
    )
    assert warning.readiness_status == "ready_with_warnings"
    needs_review = assess_design_readiness(
        _study(review_status=ReviewStatus.METADATA_VALIDATED),
        registry=registry,
        ingestion_results=(ingestion,),
    )
    assert needs_review.readiness_status == "needs_review"
    blocked = assess_design_readiness(
        _study(pre_periods=4), registry=registry, ingestion_results=(ingestion,)
    )
    assert blocked.readiness_status == "blocked"
    assert any(item.code == "insufficient_pre_periods" for item in blocked.blocking_findings)


def test_conversion_requires_explicit_methodological_choices_and_retains_provenance():
    study = _study()
    with pytest.raises(StudyConversionError):
        build_causal_specification(
            study=study,
            specification_id="spec",
            investigation_id="inv",
            outcome=VariableReference(variable_id="y"),
            controls=("ARG",),
            treatment_variable=VariableReference(variable_id="treated"),
            method=CausalMethod.DIFFERENCE_IN_DIFFERENCES,
            pre_treatment_window=(2018, 2019),
            post_treatment_window=(2020, 2021),
        )
    spec = build_causal_specification(
        study=study,
        specification_id="spec",
        investigation_id="inv",
        outcome=VariableReference(variable_id="y"),
        controls=("ARG", "CHL"),
        covariates=(VariableReference(variable_id="x"),),
        treatment_variable=VariableReference(variable_id="treated"),
        method=CausalMethod.DIFFERENCE_IN_DIFFERENCES,
        pre_treatment_window=(2018, 2019),
        post_treatment_window=(2020, 2021),
        treatment_timing_rule_confirmed=True,
    )
    assert spec.registry_provenance["study_id"] == study.study_id
    assert spec.treatment.treatment_source.startswith("causal_study_registry:")


def test_phase13_reference_does_not_execute_causal_analysis(tmp_path: Path):
    ingestion = synthetic_causal_ingestion(tmp_path)
    request = base_request(
        dataset_inputs=(IngestionArtifactInput(ingestion_result=ingestion),),
        statistical_specification=statistical_spec(),
    ).model_copy(
        update={
            "causal_study_id": "study_template_public_health_annual_country_v1",
            "causal_specification": None,
        }
    )
    plan = plan_research_project(request)
    assert plan.statistical_analysis_step == "ordinary_least_squares"
    assert request.causal_specification is None


def test_mcp_lists_inspects_and_assesses_without_invention():
    service = MCPToolService()
    listed = service.call_tool("list_causal_studies", {})
    assert any(
        item["study_id"] == "study_template_public_health_annual_country_v1"
        for item in listed["studies"]
    )
    inspected = service.call_tool(
        "inspect_causal_study", {"study_id": "study_template_public_health_annual_country_v1"}
    )
    assert inspected["study"]["study_id"] == "study_template_public_health_annual_country_v1"
    readiness = service.call_tool(
        "assess_causal_study_readiness",
        {"study_id": "study_template_public_health_annual_country_v1"},
    )
    assert readiness["artifact"]["artifact_type"] == "causal_study_readiness"
    assert "error" in service.call_tool("inspect_causal_study", {"study_id": "missing"})

    resources = MCPResourceStore()
    assert "polaris://causal-studies" in resources.list_resource_uris()
    assert resources.read_resource("polaris://causal-studies")["studies"]


def test_reporting_renders_registry_provenance(tmp_path: Path):
    ingestion = synthetic_causal_ingestion(tmp_path)
    spec = causal_spec().model_copy(
        update={"registry_provenance": {"study_id": "study_x", "intervention_id": "int_x"}}
    )
    from polaris.analysis.causal import CausalAnalysisRequest, run_causal_analysis

    result = run_causal_analysis(
        request=CausalAnalysisRequest(ingestion_result=ingestion, causal_specification=spec)
    )
    section = causal_design_section(extract_evidence(analysis_result=result))
    assert section.registry_provenance["study_id"] == "study_x"


def _study(
    *,
    study_id: str = "study_ready",
    intervention_id: str = "intervention_ready",
    treated: tuple[str, ...] = ("BRA",),
    starts: dict[str, int] | None = None,
    pre_periods: int = 2,
    review_status: ReviewStatus = ReviewStatus.DESIGN_READY,
    post_treatment_covariate: bool = False,
) -> CausalStudyDefinition:
    starts = starts or {entity: 2020 for entity in treated}
    assignments = [
        TreatmentAssignment(
            entity_id=entity,
            treatment_status="treated",
            treatment_start=starts[entity],
            assignment_source_ids=("src1",),
            review_status=review_status,
        )
        for entity in treated
    ]
    assignments.extend(
        [
            TreatmentAssignment(
                entity_id="ARG",
                treatment_status="never_treated",
                assignment_source_ids=("src1",),
                review_status=review_status,
            ),
            TreatmentAssignment(
                entity_id="CHL",
                treatment_status="never_treated",
                assignment_source_ids=("src1",),
                review_status=review_status,
            ),
        ]
    )
    return CausalStudyDefinition(
        study_id=study_id,
        title="Reviewed synthetic metadata study",
        research_question="Does a reviewed treatment definition support a causal design?",
        intervention=InterventionDefinition(
            intervention_id=intervention_id,
            name="Reviewed synthetic intervention",
            description="Synthetic intervention metadata used only for tests.",
            intervention_type="health_policy",
            jurisdiction_level="country",
            treatment_definition="Explicit synthetic treatment definition.",
            effective_date="2020-01-01",
            treated_entities=treated,
            potentially_unaffected_entities=("ARG", "CHL"),
            treatment_persistence="absorbing",
            treatment_reversibility="not_reversed_in_scope",
            source_ids=("src1",),
            review_status=review_status,
        ),
        treatment_assignments=tuple(assignments),
        treatment_timing_rule=AnnualTimingRule(
            date_role="effective_date",
            analysis_treatment_year=2020,
            rule="First annual treatment period is 2020.",
            source_ids=("src1",),
        ),
        sources=(
            TreatmentSource(
                source_id="src1",
                title="Synthetic official treatment source",
                publisher="Test authority",
                source_type="official_document",
                quality_category="primary_official",
                citation_text="Synthetic official source for tests.",
            ),
        ),
        proposed_outcomes=(
            StudyVariableReference(
                variable_id="y",
                dataset_id="study_panel",
                role="outcome",
                provider="Test Provider",
                unit="points",
            ),
        ),
        proposed_covariates=(
            StudyVariableReference(
                variable_id="x",
                dataset_id="study_panel",
                role="covariate",
                provider="Test Provider",
                unit="points",
                post_treatment_concern=post_treatment_covariate,
            ),
        ),
        candidate_dataset_ids=("study_panel",),
        entity_variable=VariableReference(variable_id="country_code"),
        time_variable=VariableReference(variable_id="year"),
        pre_period_requirements=pre_periods,
        post_period_requirements=2,
        comparison_group_policy="explicit_only",
        explicit_comparison_entities=("ARG", "CHL"),
        identifying_assumptions=("Parallel trends requires human review.",),
        source_ids=("src1",),
        review_status=review_status,
    )


def _ingestion(tmp_path: Path):
    rows = [["country_code", "year", "y", "x", "treated"]]
    for entity in ("ARG", "BRA", "CHL"):
        for year in range(2018, 2022):
            rows.append([entity, year, float(year), 1.0, int(entity == "BRA")])
    path = tmp_path / "study_panel.csv"
    path.write_text("\n".join(",".join(map(str, row)) for row in rows) + "\n", encoding="utf-8")
    manifest = DatasetManifest.model_validate(
        {
            "dataset_id": "study_panel",
            "title": "Study Panel",
            "provider": "Test Provider",
            "source_url": "https://example.test/study-panel",
            "status": "approved",
            "geographic_coverage": {"codes": ["ARG", "BRA", "CHL"]},
            "temporal_coverage": {"start": 2018, "end": 2021},
            "variables": [
                _variable("country_code", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("year", DataType.INTEGER, VariableRole.TIME),
                _variable("y", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("x", DataType.FLOAT, VariableRole.COVARIATE),
                _variable("treated", DataType.INTEGER, VariableRole.EXPOSURE),
            ],
        }
    )
    return ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(dataset_id="study_panel", source_path=path),
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole):
    return {"variable_id": variable_id, "label": variable_id, "data_type": data_type, "role": role}


def _write_registry(path: Path, studies: list[CausalStudyDefinition]) -> None:
    (path / "studies.json").write_text(
        json.dumps([study.model_dump(mode="json") for study in studies], sort_keys=True),
        encoding="utf-8",
    )
