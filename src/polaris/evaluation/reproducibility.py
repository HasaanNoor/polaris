"""Reproducibility checks for deterministic reasoning."""

from polaris.evaluation.models import (
    DimensionEvaluationResult,
    EvaluationDimension,
    EvaluationFinding,
    EvaluationFindingCode,
    EvaluationSeverity,
)
from polaris.reasoning.models import ReasoningArtifact, ReasoningRequest
from polaris.reasoning.service import build_reasoning_artifact
from polaris.reasoning.taxonomy import ReasoningMode


def evaluate_reproducibility(
    *,
    request: ReasoningRequest,
    reasoning: ReasoningArtifact,
    runs: int = 2,
) -> DimensionEvaluationResult:
    if request.mode is not ReasoningMode.DETERMINISTIC:
        return DimensionEvaluationResult(
            dimension=EvaluationDimension.REPRODUCIBILITY,
            passed=True,
            metrics={"reproducibility_checked": False},
        )
    generated = tuple(build_reasoning_artifact(request=request) for _ in range(runs))
    expected_identity = _stable_identity(reasoning)
    findings: list[EvaluationFinding] = []
    for artifact in generated:
        if _stable_identity(artifact) != expected_identity:
            findings.append(
                EvaluationFinding(
                    code=EvaluationFindingCode.NON_DETERMINISTIC_FALLBACK,
                    severity=EvaluationSeverity.ERROR,
                    dimension=EvaluationDimension.REPRODUCIBILITY,
                    message="Deterministic reasoning artifact changed across repeated runs.",
                )
            )
            break
    return DimensionEvaluationResult(
        dimension=EvaluationDimension.REPRODUCIBILITY,
        passed=not findings,
        findings=tuple(findings),
        metrics={"reproducibility_checked": True, "repeat_runs": runs},
    )


def _stable_identity(reasoning: ReasoningArtifact) -> dict[str, object]:
    return {
        "reasoning_id": reasoning.reasoning_id,
        "statements": [item.model_dump(mode="json") for item in reasoning.reasoning_statements],
        "contradictions": [item.model_dump(mode="json") for item in reasoning.contradictions],
        "candidate_confounders": [
            item.model_dump(mode="json") for item in reasoning.candidate_confounders
        ],
        "grounding_summary": reasoning.grounding_summary.model_dump(mode="json"),
    }
