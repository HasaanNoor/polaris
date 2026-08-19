"""Phase 22 causal-reasoning benchmark fixtures."""

from examples.evaluation.benchmarks.baseline import _SOFTWARE, _TIMESTAMP, _coordination
from polaris.evaluation.models import (
    BenchmarkCase,
    BenchmarkSuite,
    BenchmarkTag,
    ExpectedReasoningBehavior,
    deterministic_suite_id,
)
from polaris.evidence.models import (
    CausalAssumptionEvidenceRecord,
    CausalTreatmentEffectEvidenceRecord,
    ClaimCandidate,
    ClaimType,
    Direction,
    EvidenceArtifact,
    EvidenceProvenance,
    LimitationCode,
)
from polaris.reasoning.taxonomy import CausalStatus, ReasoningCategory, ReasoningMode
from polaris.schemas.common import StatisticalProcedure


def causal_suite() -> BenchmarkSuite:
    cases = (
        _case("causal_a_valid_simple_did", "Valid simple DiD", Direction.POSITIVE),
        _case(
            "causal_b_parallel_trend_concern",
            "Parallel-trend concern",
            Direction.POSITIVE,
            limitations=(LimitationCode.PRE_TREND_CONCERN,),
        ),
        _case(
            "causal_c_insufficient_pre_periods",
            "Insufficient pre-periods",
            Direction.POSITIVE,
            limitations=(LimitationCode.INSUFFICIENT_PRE_TREATMENT_DATA,),
        ),
        _case(
            "causal_d_no_valid_control_group",
            "No valid control group",
            Direction.UNDEFINED,
            limitations=(LimitationCode.IDENTIFICATION_ASSUMPTION_LIMITATION,),
        ),
        _case(
            "causal_e_timing_inconsistency",
            "Treatment-timing inconsistency",
            Direction.UNDEFINED,
            limitations=(LimitationCode.IDENTIFICATION_ASSUMPTION_LIMITATION,),
        ),
        _case(
            "causal_f_ols_causal_overclaim",
            "Causal claim from ordinary OLS",
            Direction.POSITIVE,
            procedure=StatisticalProcedure.ORDINARY_LEAST_SQUARES,
            causal=False,
        ),
        _case(
            "causal_g_fe_causal_overclaim",
            "Causal claim from fixed effects alone",
            Direction.POSITIVE,
            procedure=StatisticalProcedure.PANEL_TWO_WAY_FE,
            causal=False,
        ),
        _case("causal_h_stronger_than_assumptions", "Overstrong DiD claim", Direction.POSITIVE),
        _case(
            "causal_i_mechanism_from_effect", "Mechanism claimed from effect", Direction.POSITIVE
        ),
        _case(
            "causal_j_staggered_unsupported",
            "Unsupported staggered adoption",
            Direction.UNDEFINED,
            limitations=(LimitationCode.IDENTIFICATION_ASSUMPTION_LIMITATION,),
        ),
        _case(
            "causal_k_post_treatment_control",
            "Post-treatment-control warning",
            Direction.POSITIVE,
            limitations=(LimitationCode.BAD_CONTROL_CAUTION,),
        ),
        _case(
            "causal_l_event_reference_period", "Event-study reference period", Direction.POSITIVE
        ),
    )
    return BenchmarkSuite(
        suite_id=deterministic_suite_id(
            title="Phase 22 Causal Reasoning Benchmarks",
            version="phase22_causal_reasoning_v1",
            case_ids=tuple(case.case_id for case in cases),
        ),
        title="Phase 22 Causal Reasoning Benchmarks",
        description="Adversarial fixtures for causal-design reasoning and overclaim detection.",
        benchmark_cases=cases,
        version="phase22_causal_reasoning_v1",
        tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.CAUSAL_TRAP, BenchmarkTag.SYNTHETIC),
    )


def _case(
    case_id: str,
    title: str,
    direction: Direction,
    *,
    limitations: tuple[LimitationCode, ...] = (),
    procedure: StatisticalProcedure = StatisticalProcedure.DIFFERENCE_IN_DIFFERENCES,
    causal: bool = True,
) -> BenchmarkCase:
    all_limitations = tuple(
        sorted(
            {
                LimitationCode.CONDITIONAL_CAUSAL_DESIGN,
                LimitationCode.IDENTIFICATION_ASSUMPTION_LIMITATION,
                *limitations,
            },
            key=lambda item: item.value,
        )
    )
    evidence, coordination = _artifacts(
        case_id,
        direction=direction,
        limitations=all_limitations,
        procedure=procedure,
        causal=causal,
    )
    return BenchmarkCase(
        case_id=case_id,
        title=title,
        description="Phase 22 causal-reasoning adversarial fixture.",
        research_question="What is the estimated treatment effect under the supplied design?",
        evidence_artifact=evidence,
        coordinated_assessment=coordination,
        expected_behavior=ExpectedReasoningBehavior(
            required_statement_categories=(ReasoningCategory.EMPIRICAL_INTERPRETATION,),
            expected_causal_status=(
                CausalStatus.CONDITIONAL_CAUSAL_DESIGN if causal else CausalStatus.NON_CAUSAL
            ),
            expected_direction=direction,
            expected_limitations=tuple(item.value for item in all_limitations),
        ),
        benchmark_tags=(BenchmarkTag.ADVERSARIAL, BenchmarkTag.CAUSAL_TRAP, BenchmarkTag.SYNTHETIC),
        reasoning_modes=(ReasoningMode.DETERMINISTIC, ReasoningMode.PROVIDER_BACKED),
    )


def _artifacts(
    case_id: str,
    *,
    direction: Direction,
    limitations: tuple[LimitationCode, ...],
    procedure: StatisticalProcedure,
    causal: bool,
) -> tuple[EvidenceArtifact, object]:
    provenance = EvidenceProvenance(
        dataset_id=f"{case_id}_dataset",
        source_checksum_sha256=f"{case_id}_checksum",
        source_analysis_result_id=f"{case_id}_causal_analysis",
        statistical_procedure=procedure,
        phase4_schema_version="1.0.0",
        extraction_timestamp=_TIMESTAMP,
        software_version=_SOFTWARE,
    )
    estimate = (
        1.5
        if direction is Direction.POSITIVE
        else (-1.5 if direction is Direction.NEGATIVE else None)
    )
    effect_id = f"{case_id}_effect"
    assumption_id = f"{case_id}_parallel_trends"
    records = (
        CausalAssumptionEvidenceRecord(
            evidence_id=assumption_id,
            source_analysis_result_id=f"{case_id}_causal_analysis",
            dataset_id=f"{case_id}_dataset",
            source_checksum_sha256=f"{case_id}_checksum",
            statistical_procedure=procedure,
            sample_size=60,
            limitation_codes=limitations,
            provenance=provenance,
            assumption_code="parallel_trends",
            status="not_violated_by_available_diagnostic"
            if LimitationCode.PRE_TREND_CONCERN not in limitations
            else "concern",
            description="Parallel trends is represented as an identifying assumption.",
            diagnostic_evidence="synthetic benchmark diagnostic",
            limitation="Non-rejection is not proof of parallel trends.",
            empirically_testable=True,
        ),
        CausalTreatmentEffectEvidenceRecord(
            evidence_id=effect_id,
            source_analysis_result_id=f"{case_id}_causal_analysis",
            dataset_id=f"{case_id}_dataset",
            source_checksum_sha256=f"{case_id}_checksum",
            statistical_procedure=procedure,
            sample_size=60,
            limitation_codes=limitations,
            provenance=provenance,
            causal_method=procedure.value,
            estimator="twfe_did",
            estimand="att",
            outcome_variable_id="outcome",
            treatment_variable_id="treatment",
            estimate=estimate,
            standard_error=0.25 if estimate is not None else None,
            p_value=0.01 if estimate is not None else None,
            confidence_interval_low=1.0 if estimate is not None else None,
            confidence_interval_high=2.0 if estimate is not None else None,
            cluster_count=30,
            treated_entity_count=10,
            control_entity_count=20,
            assumption_ids=(assumption_id,),
        ),
    )
    claim = ClaimCandidate(
        claim_id=f"{case_id}_claim",
        claim_type=ClaimType.CAUSAL_DESIGN_ESTIMATE if causal else ClaimType.ASSOCIATION,
        subject_variable="treatment",
        outcome_variable="outcome",
        related_variables=("treatment",),
        direction=direction,
        statistical_procedure=procedure,
        supporting_evidence_ids=(effect_id, assumption_id),
        limitation_codes=limitations,
        causal=causal,
        source_analysis_result_id=f"{case_id}_causal_analysis",
        dataset_id=f"{case_id}_dataset",
        provenance=provenance,
        p_value_below_threshold=estimate is not None,
        confidence_interval_crosses_zero=False if estimate is not None else None,
    )
    artifact = EvidenceArtifact(
        artifact_id=f"{case_id}_evidence_artifact",
        source_analysis_result_id=f"{case_id}_causal_analysis",
        dataset_id=f"{case_id}_dataset",
        source_checksum_sha256=f"{case_id}_checksum",
        evidence_records=records,
        claim_candidates=(claim,),
        provenance=provenance,
        extraction_timestamp=_TIMESTAMP,
        software_version=_SOFTWARE,
    )
    return artifact, _coordination(case_id=case_id, artifact=artifact, limitations=limitations)
