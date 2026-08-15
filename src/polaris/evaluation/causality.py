"""Causal-restraint evaluation."""

from polaris.evaluation.models import (
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import CausalStatus, ReasoningCategory
from polaris.reasoning.validation import causal_language_violation


def evaluate_causal_restraint(reasoning: ReasoningArtifact) -> DimensionEvaluationResult:
    findings: list[EvaluationFinding] = []
    guarded_mechanisms = 0
    causal_disclaimers = 0
    for statement in reasoning.reasoning_statements:
        violation = causal_language_violation(statement)
        if violation is not None:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.CAUSAL_OVERCLAIM,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.CAUSAL_RESTRAINT,
                    message=violation,
                    statement_ids=(statement.statement_id,),
                )
            )
        if (
            statement.category is ReasoningCategory.PLAUSIBLE_MECHANISM
            and statement.causal_status is CausalStatus.NOT_ESTABLISHED
        ):
            guarded_mechanisms += 1
        text = statement.text.lower()
        if "causal" in text and ("not established" in text or "cannot be inferred" in text):
            causal_disclaimers += 1
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.CAUSAL_RESTRAINT,
        passed=not findings,
        findings=tuple(findings),
        metrics={
            "causal_violation_count": len(findings),
            "allowed_guarded_mechanism_count": guarded_mechanisms,
            "explicit_causal_disclaimer_count": causal_disclaimers,
        },
    )
