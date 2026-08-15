"""Epistemic-calibration evaluation."""

from polaris.evaluation.models import (
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact
from polaris.reasoning.taxonomy import EpistemicStatus, ReasoningCategory, SupportLevel


def evaluate_epistemic_calibration(reasoning: ReasoningArtifact) -> DimensionEvaluationResult:
    findings: list[EvaluationFinding] = []
    checked = 0
    for statement in reasoning.reasoning_statements:
        checked += 1
        if statement.category is ReasoningCategory.PLAUSIBLE_MECHANISM:
            if statement.epistemic_status not in {
                EpistemicStatus.PLAUSIBLE_BUT_UNPROVEN,
                EpistemicStatus.SPECULATIVE,
            }:
                findings.append(
                    _mismatch(statement.statement_id, "Mechanism was not labeled unproven.")
                )
            if statement.support_level is SupportLevel.STRONG:
                findings.append(
                    _mismatch(statement.statement_id, "Mechanism received strong support.")
                )
        if (
            statement.category
            in {
                ReasoningCategory.FOLLOW_UP_HYPOTHESIS,
                ReasoningCategory.FOLLOW_UP_RESEARCH_QUESTION,
            }
            and statement.epistemic_status is EpistemicStatus.DIRECTLY_SUPPORTED
        ):
            findings.append(
                _mismatch(
                    statement.statement_id, "Speculative follow-up was labeled directly supported."
                )
            )
        if (
            statement.epistemic_status is EpistemicStatus.CONTRADICTED
            and statement.support_level is SupportLevel.STRONG
        ):
            findings.append(
                _mismatch(statement.statement_id, "Contradicted statement received strong support.")
            )
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.EPISTEMIC_CALIBRATION,
        passed=not findings,
        findings=tuple(findings),
        metrics={"checked_statement_count": checked, "epistemic_mismatch_count": len(findings)},
    )


def _mismatch(statement_id: str, message: str) -> EvaluationFinding:
    return EvaluationFinding(
        code=EvaluationFindingCode.EPISTEMIC_STATUS_MISMATCH,
        severity=EvaluationSeverity.ERROR,
        dimension=EvaluationDimension.EPISTEMIC_CALIBRATION,
        message=message,
        statement_ids=(statement_id,),
    )
