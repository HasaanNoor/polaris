"""Benchmark-suite execution for Phase 19 reasoning evaluation."""

from collections import Counter, defaultdict

from polaris.evaluation.models import (
    BenchmarkSuite,
    BenchmarkSuiteResult,
    EvaluationDimension,
    ModeComparison,
)
from polaris.evaluation.service import evaluate_reasoning
from polaris.reasoning.models import ReasoningRequest
from polaris.reasoning.provider import ReasoningProvider
from polaris.reasoning.service import build_reasoning_artifact
from polaris.reasoning.taxonomy import ReasoningMode


def run_benchmark_suite(
    *,
    suite: BenchmarkSuite,
    reasoning_modes: tuple[ReasoningMode, ...] | None = None,
    provider: ReasoningProvider | dict[str, ReasoningProvider] | None = None,
    check_reproducibility: bool = True,
) -> BenchmarkSuiteResult:
    requested_modes = reasoning_modes or tuple(
        sorted(
            {mode for case in suite.benchmark_cases for mode in case.reasoning_modes},
            key=lambda item: item.value,
        )
    )
    results = []
    for case in suite.benchmark_cases:
        for mode in requested_modes:
            if mode not in case.reasoning_modes:
                continue
            request = ReasoningRequest(
                research_question=case.research_question,
                evidence_artifact=case.evidence_artifact,
                coordinated_assessment=case.coordinated_assessment,
                literature_context=case.literature_context,
                mode=mode,
            )
            reasoning_provider = _provider_for(case.case_id, provider)
            artifact = build_reasoning_artifact(request=request, provider=reasoning_provider)
            results.append(
                evaluate_reasoning(
                    case=case,
                    reasoning=artifact,
                    check_reproducibility=check_reproducibility
                    and mode is ReasoningMode.DETERMINISTIC,
                )
            )
    dimension_summaries: dict[str, dict[str, int]] = {}
    for dimension in EvaluationDimension:
        passed = sum(
            1
            for result in results
            for item in result.dimension_results
            if item.dimension is dimension and item.passed
        )
        failed = sum(
            1
            for result in results
            for item in result.dimension_results
            if item.dimension is dimension and not item.passed
        )
        if passed or failed:
            dimension_summaries[dimension.value] = {"passed": passed, "failed": failed}
    failure_counts = Counter(
        finding.code.value for result in results for finding in result.findings
    )
    reproducibility_findings = tuple(
        finding
        for result in results
        for finding in result.findings
        if finding.dimension is EvaluationDimension.REPRODUCIBILITY
    )
    return BenchmarkSuiteResult(
        suite_id=suite.suite_id,
        executed_cases=tuple(sorted({result.benchmark_case_id for result in results})),
        reasoning_modes=tuple(
            sorted({result.reasoning_mode for result in results}, key=lambda item: item.value)
        ),
        case_results=tuple(results),
        aggregate_dimension_summaries=dimension_summaries,
        failure_counts_by_code=dict(sorted(failure_counts.items())),
        mode_comparisons=_mode_comparisons(tuple(results)),
        reproducibility_findings=reproducibility_findings,
        run_metadata={
            "suite_title": suite.title,
            "suite_version": suite.version,
            "single_score": "not provided; inspect dimension metrics",
        },
    )


def _provider_for(
    case_id: str,
    provider: ReasoningProvider | dict[str, ReasoningProvider] | None,
) -> ReasoningProvider | None:
    if isinstance(provider, dict):
        return provider.get(case_id)
    return provider


def _mode_comparisons(results) -> tuple[ModeComparison, ...]:
    by_mode: dict[ReasoningMode, list] = defaultdict(list)
    for result in results:
        by_mode[result.reasoning_mode].append(result)
    comparisons = []
    for mode, mode_results in sorted(by_mode.items(), key=lambda item: item[0].value):
        dimension_counts: Counter[str] = Counter()
        failures: Counter[str] = Counter()
        for result in mode_results:
            for dimension in result.dimension_results:
                if dimension.passed:
                    dimension_counts[dimension.dimension.value] += 1
            for finding in result.findings:
                failures[finding.code.value] += 1
        comparisons.append(
            ModeComparison(
                reasoning_mode=mode,
                executed_cases=len(mode_results),
                dimension_pass_counts=dict(sorted(dimension_counts.items())),
                failure_counts_by_code=dict(sorted(failures.items())),
                metric_means=_metric_means(tuple(mode_results)),
            )
        )
    return tuple(comparisons)


def _metric_means(results) -> dict[str, float]:
    keys = (
        "grounding_coverage",
        "evidence_fidelity_pass_rate",
        "required_category_coverage",
        "contradiction_detection_rate",
        "material_limitation_coverage",
    )
    means = {}
    for key in keys:
        values = [float(getattr(result.metrics, key)) for result in results]
        means[key] = sum(values) / len(values) if values else 0.0
    return means
