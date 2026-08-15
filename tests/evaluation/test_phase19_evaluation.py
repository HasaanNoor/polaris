from __future__ import annotations

from examples.evaluation.benchmarks.baseline import baseline_suite
from polaris.evaluation import (
    benchmark_result_to_json,
    benchmark_result_to_markdown,
    evaluate_reasoning,
    run_benchmark_suite,
)
from polaris.evaluation.models import EvaluationFindingCode
from polaris.reasoning import (
    CausalStatus,
    EpistemicStatus,
    ReasoningCategory,
    ReasoningMode,
    ReasoningRequest,
    ReasoningStatement,
    SupportLevel,
    build_reasoning_artifact,
)
from polaris.reasoning.models import StructuredReasoningResponse


class ValidProvider:
    provider_name = "valid-fake-provider"

    def reason(self, *, request, system_prompt, grounding_payload):
        claim = request.evidence_artifact.claim_candidates[0]
        return StructuredReasoningResponse(
            reasoning_statements=(
                ReasoningStatement(
                    statement_id="provider_valid_empirical",
                    category=ReasoningCategory.EMPIRICAL_INTERPRETATION,
                    text=(
                        f"{claim.subject_variable} is associated with {claim.outcome_variable} "
                        f"in the {claim.direction.value} direction in non-causal evidence."
                    ),
                    evidence_ids=claim.supporting_evidence_ids,
                    claim_ids=(claim.claim_id,),
                    agent_assessment_ids=request.coordinated_assessment.source_assessment_ids,
                    domains=request.coordinated_assessment.participating_domains,
                    support_level=SupportLevel.MODERATE,
                    epistemic_status=EpistemicStatus.SUPPORTED_INTERPRETATION,
                    causal_status=CausalStatus.NON_CAUSAL,
                ),
            )
        )


def request_for(case, mode=ReasoningMode.DETERMINISTIC):
    return ReasoningRequest(
        research_question=case.research_question,
        evidence_artifact=case.evidence_artifact,
        coordinated_assessment=case.coordinated_assessment,
        literature_context=case.literature_context,
        mode=mode,
    )


def artifact_for(case):
    return build_reasoning_artifact(request=request_for(case))


def replace_first_statement(artifact, statement):
    statements = (statement, *artifact.reasoning_statements[1:])
    return artifact.model_copy(update={"reasoning_statements": statements})


def finding_codes(result):
    return {finding.code for finding in result.findings}


def test_baseline_suite_is_deterministic_and_structurally_clean():
    suite = baseline_suite()
    result_a = run_benchmark_suite(
        suite=suite,
        reasoning_modes=(ReasoningMode.DETERMINISTIC,),
    )
    result_b = run_benchmark_suite(
        suite=suite,
        reasoning_modes=(ReasoningMode.DETERMINISTIC,),
    )

    assert len(suite.benchmark_cases) == 11
    assert result_a.failure_counts_by_code == {}
    assert [item.evaluation_id for item in result_a.case_results] == [
        item.evaluation_id for item in result_b.case_results
    ]
    assert all(item.metrics.deterministic_reproducibility_pass for item in result_a.case_results)


def test_fabricated_grounding_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_h")
    )
    artifact = artifact_for(case)
    original = artifact.reasoning_statements[0]
    flawed = original.model_copy(update={"evidence_ids": ("missing_evidence_id",)})

    result = evaluate_reasoning(case=case, reasoning=replace_first_statement(artifact, flawed))

    assert EvaluationFindingCode.INVALID_GROUNDING in finding_codes(result)
    assert result.metrics.grounding_coverage < 1.0


def test_fabricated_citation_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_i")
    )
    artifact = artifact_for(case)
    literature_statement = next(
        item
        for item in artifact.reasoning_statements
        if item.category is ReasoningCategory.LITERATURE_CONTRAST
    )
    flawed = literature_statement.model_copy(update={"literature_evidence_ids": ("missing_lit",)})

    result = evaluate_reasoning(case=case, reasoning=replace_first_statement(artifact, flawed))

    assert EvaluationFindingCode.FABRICATED_CITATION in finding_codes(result)


def test_causal_overclaim_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_c")
    )
    artifact = artifact_for(case)
    original = artifact.reasoning_statements[0]
    flawed = original.model_copy(update={"text": "education_spending causes life_expectancy."})

    result = evaluate_reasoning(case=case, reasoning=replace_first_statement(artifact, flawed))

    assert EvaluationFindingCode.CAUSAL_OVERCLAIM in finding_codes(result)


def test_evidence_direction_mismatch_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_a")
    )
    artifact = artifact_for(case)
    original = next(
        item
        for item in artifact.reasoning_statements
        if item.category is ReasoningCategory.EMPIRICAL_INTERPRETATION
    )
    flawed = original.model_copy(
        update={"text": "x is associated with y in the negative direction."}
    )

    result = evaluate_reasoning(case=case, reasoning=replace_first_statement(artifact, flawed))

    assert EvaluationFindingCode.EVIDENCE_DIRECTION_MISMATCH in finding_codes(result)


def test_contradiction_omission_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_d")
    )
    artifact = artifact_for(case).model_copy(update={"contradictions": ()})

    result = evaluate_reasoning(case=case, reasoning=artifact)

    assert EvaluationFindingCode.CONTRADICTION_IGNORED in finding_codes(result)
    assert result.metrics.contradiction_detection_rate == 0.0


def test_material_limitation_loss_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_f")
    )
    artifact = artifact_for(case)
    stripped = artifact.model_copy(
        update={
            "reasoning_statements": tuple(
                statement.model_copy(
                    update={
                        "limitations": (),
                        "text": statement.text.replace("SMALL_SAMPLE", "sample constraint"),
                    }
                )
                for statement in artifact.reasoning_statements
            )
        }
    )

    result = evaluate_reasoning(case=case, reasoning=stripped)

    assert EvaluationFindingCode.MATERIAL_LIMITATION_DROPPED in finding_codes(result)


def test_literature_as_empirical_evidence_is_detected():
    case = next(
        item for item in baseline_suite().benchmark_cases if item.case_id.startswith("case_e")
    )
    artifact = artifact_for(case)
    literature_id = case.literature_context.literature_evidence[0].literature_evidence_id
    original = artifact.reasoning_statements[0]
    flawed = original.model_copy(update={"literature_evidence_ids": (literature_id,)})

    result = evaluate_reasoning(case=case, reasoning=replace_first_statement(artifact, flawed))

    assert EvaluationFindingCode.LITERATURE_AS_EMPIRICAL_EVIDENCE in finding_codes(result)


def test_provider_comparison_uses_same_dimensions_without_leaderboard():
    suite = baseline_suite()
    result = run_benchmark_suite(
        suite=suite,
        reasoning_modes=(ReasoningMode.DETERMINISTIC, ReasoningMode.PROVIDER_BACKED),
        provider=ValidProvider(),
    )

    assert {mode.value for mode in result.reasoning_modes} == {"deterministic", "provider_backed"}
    assert len(result.mode_comparisons) == 2
    assert result.run_metadata["single_score"] == "not provided; inspect dimension metrics"


def test_benchmark_reports_include_required_sections():
    result = run_benchmark_suite(
        suite=baseline_suite(),
        reasoning_modes=(ReasoningMode.DETERMINISTIC,),
    )
    markdown = benchmark_result_to_markdown(result)
    payload = benchmark_result_to_json(result)

    assert "Benchmark Summary" in markdown
    assert "Mode Comparison" in markdown
    assert "Known Evaluation Limitations" in markdown
    assert '"suite_id"' in payload
