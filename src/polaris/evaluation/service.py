"""Public evaluation service for Phase 19."""

from polaris.evaluation.causality import evaluate_causal_restraint
from polaris.evaluation.contradictions import evaluate_contradiction_handling
from polaris.evaluation.epistemics import evaluate_epistemic_calibration
from polaris.evaluation.fidelity import evaluate_evidence_fidelity
from polaris.evaluation.grounding import evaluate_grounding
from polaris.evaluation.limitations import evaluate_limitation_propagation
from polaris.evaluation.literature import evaluate_literature_separation
from polaris.evaluation.models import (
    BenchmarkCase,
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
    ReasoningEvaluationMetrics,
    ReasoningEvaluationResult,
    deterministic_evaluation_id,
)
from polaris.evaluation.reproducibility import evaluate_reproducibility
from polaris.evaluation.structural import evaluate_structural_validity
from polaris.reasoning.models import ReasoningArtifact, ReasoningRequest
from polaris.reasoning.taxonomy import ReasoningCategory


def evaluate_reasoning(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
    check_reproducibility: bool = False,
) -> ReasoningEvaluationResult:
    request = ReasoningRequest(
        research_question=case.research_question,
        evidence_artifact=case.evidence_artifact,
        coordinated_assessment=case.coordinated_assessment,
        literature_context=case.literature_context,
        mode=reasoning.mode,
    )
    dimension_results = [
        evaluate_grounding(request=request, reasoning=reasoning),
        evaluate_evidence_fidelity(case=case, reasoning=reasoning),
        evaluate_causal_restraint(reasoning),
        evaluate_epistemic_calibration(reasoning),
        evaluate_contradiction_handling(case=case, reasoning=reasoning),
        evaluate_limitation_propagation(case=case, reasoning=reasoning),
        evaluate_literature_separation(case=case, reasoning=reasoning),
        evaluate_structural_validity(reasoning),
        _evaluate_expected_behavior(case=case, reasoning=reasoning),
    ]
    if check_reproducibility:
        dimension_results.append(evaluate_reproducibility(request=request, reasoning=reasoning))
    dimensions = tuple(dimension_results)
    findings = tuple(finding for result in dimensions for finding in result.findings)
    metrics = _metrics(dimensions)
    failed = tuple(
        result.dimension.value
        for result in dimensions
        if any(finding.severity is EvaluationSeverity.ERROR for finding in result.findings)
    )
    passed = tuple(
        result.dimension.value for result in dimensions if result.dimension.value not in failed
    )
    evaluation_id = deterministic_evaluation_id(
        benchmark_case_id=case.case_id,
        reasoning_artifact=reasoning,
        dimension_results=dimensions,
        metrics=metrics,
    )
    return ReasoningEvaluationResult(
        evaluation_id=evaluation_id,
        benchmark_case_id=case.case_id,
        reasoning_artifact_id=reasoning.reasoning_id,
        reasoning_mode=reasoning.mode,
        findings=findings,
        dimension_results=dimensions,
        metrics=metrics,
        pass_fail_criteria=(
            "no error-severity evaluation findings",
            "required benchmark expectations represented structurally",
            "grounding IDs valid against upstream artifacts",
        ),
        failed_expectations=failed,
        passed_expectations=passed,
    )


def _evaluate_expected_behavior(
    *,
    case: BenchmarkCase,
    reasoning: ReasoningArtifact,
) -> DimensionEvaluationResult:
    expected = case.expected_behavior
    findings: list[EvaluationFinding] = []
    categories = {statement.category for statement in reasoning.reasoning_statements}
    grounded_ids = {
        source_id
        for statement in reasoning.reasoning_statements
        for source_id in (
            statement.evidence_ids
            + statement.claim_ids
            + statement.agent_assessment_ids
            + statement.literature_evidence_ids
        )
    }
    for category in expected.required_statement_categories:
        if category not in categories:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.EXPECTED_CATEGORY_MISSING,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message=f"Required reasoning category is missing: {category.value}",
                )
            )
    for category in expected.prohibited_statement_categories:
        if category in categories:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.PROHIBITED_CATEGORY_PRESENT,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message=f"Prohibited reasoning category is present: {category.value}",
                )
            )
    for source_id in expected.required_grounding_ids:
        if source_id not in grounded_ids:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.INVALID_GROUNDING,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message=f"Required grounding ID was not used: {source_id}",
                    source_ids=(source_id,),
                )
            )
    for source_id in expected.prohibited_grounding_ids:
        if source_id in grounded_ids:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.INVALID_GROUNDING,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message=f"Prohibited grounding ID was used: {source_id}",
                    source_ids=(source_id,),
                )
            )
    if expected.expected_epistemic_statuses:
        allowed_statuses = set(expected.expected_epistemic_statuses)
        mismatched_statuses = tuple(
            statement.statement_id
            for statement in reasoning.reasoning_statements
            if statement.category in expected.required_statement_categories
            and statement.epistemic_status not in allowed_statuses
        )
        if mismatched_statuses:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.EPISTEMIC_STATUS_MISMATCH,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message="Reasoning used epistemic statuses outside benchmark expectations.",
                    statement_ids=mismatched_statuses,
                )
            )
    if expected.expected_candidate_confounders:
        represented_confounders = " ".join(
            (
                *(item.variable_or_concept.lower() for item in reasoning.candidate_confounders),
                *(item.text.lower() for item in reasoning.reasoning_statements),
            )
        )
        for confounder in expected.expected_candidate_confounders:
            if confounder.lower() not in represented_confounders:
                findings.append(
                    EvaluationFinding(
                        code=EvaluationFindingCode.EXPECTED_CATEGORY_MISSING,
                        severity=EvaluationSeverity.ERROR,
                        dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                        message=f"Expected candidate confounder was absent: {confounder}",
                    )
                )
    if expected.expected_causal_status is not None:
        categories_with_expected_causal_status = {
            ReasoningCategory.EMPIRICAL_INTERPRETATION,
            ReasoningCategory.CROSS_DOMAIN_SYNTHESIS,
            ReasoningCategory.CONTRADICTION,
            ReasoningCategory.LIMITATION,
            ReasoningCategory.UNCERTAINTY,
            ReasoningCategory.LITERATURE_ALIGNMENT,
            ReasoningCategory.LITERATURE_CONTRAST,
        }
        mismatched = [
            statement.statement_id
            for statement in reasoning.reasoning_statements
            if statement.causal_status != expected.expected_causal_status
            and statement.category in categories_with_expected_causal_status
        ]
        if mismatched:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.CAUSAL_OVERCLAIM,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                    message="Reasoning used an unexpected causal status.",
                    statement_ids=tuple(mismatched),
                )
            )
    covered_categories = len(set(expected.required_statement_categories) & categories)
    category_coverage = (
        covered_categories / len(expected.required_statement_categories)
        if expected.required_statement_categories
        else 1.0
    )
    grounded_count = sum(
        1
        for statement in reasoning.reasoning_statements
        if statement.evidence_ids
        or statement.claim_ids
        or statement.agent_assessment_ids
        or statement.literature_evidence_ids
    )
    if grounded_count < expected.minimum_grounded_statements:
        findings.append(
            EvaluationFinding(
                code=EvaluationFindingCode.ORPHAN_STATEMENT,
                severity=EvaluationSeverity.ERROR,
                dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                message="Reasoning had fewer grounded statements than expected.",
            )
        )
    unsupported_count = sum(
        1
        for statement in reasoning.reasoning_statements
        if not (
            statement.evidence_ids
            or statement.claim_ids
            or statement.agent_assessment_ids
            or statement.literature_evidence_ids
        )
    )
    if unsupported_count > expected.maximum_unsupported_statements:
        findings.append(
            EvaluationFinding(
                code=EvaluationFindingCode.ORPHAN_STATEMENT,
                severity=EvaluationSeverity.ERROR,
                dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
                message="Reasoning had more unsupported statements than expected.",
            )
        )
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.EXPECTED_BEHAVIOR,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "required_category_coverage": category_coverage,
            "grounded_statement_count": grounded_count,
            "unsupported_statement_count": unsupported_count,
        },
    )


def _metrics(dimensions: tuple[DimensionEvaluationResult, ...]) -> ReasoningEvaluationMetrics:
    by_name = {result.dimension: result for result in dimensions}
    grounding = by_name[EvaluationDimension.GROUNDING].metrics
    fidelity = by_name[EvaluationDimension.EVIDENCE_FIDELITY].metrics
    expected = by_name[EvaluationDimension.EXPECTED_BEHAVIOR].metrics
    contradictions = by_name[EvaluationDimension.CONTRADICTION_HANDLING].metrics
    limitations = by_name[EvaluationDimension.LIMITATION_PROPAGATION].metrics
    reproducibility = by_name.get(EvaluationDimension.REPRODUCIBILITY)
    return ReasoningEvaluationMetrics(
        grounding_coverage=float(grounding.get("grounding_coverage_ratio", 0.0)),
        evidence_fidelity_pass_rate=float(fidelity.get("pass_rate", 1.0)),
        causal_restraint_pass=by_name[EvaluationDimension.CAUSAL_RESTRAINT].passed,
        required_category_coverage=float(expected.get("required_category_coverage", 1.0)),
        contradiction_detection_rate=float(contradictions.get("contradiction_detection_rate", 1.0)),
        material_limitation_coverage=float(limitations.get("material_limitation_coverage", 1.0)),
        structural_validity_pass=by_name[EvaluationDimension.STRUCTURAL_VALIDITY].passed,
        deterministic_reproducibility_pass=(
            reproducibility.passed if reproducibility is not None else None
        ),
    )
