"""JSON and Markdown benchmark reporting."""

import json

from polaris.evaluation.models import BenchmarkSuiteResult, EvaluationSeverity


def benchmark_result_to_json(result: BenchmarkSuiteResult) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


def benchmark_result_to_markdown(result: BenchmarkSuiteResult) -> str:
    lines = [
        "# Benchmark Summary",
        "",
        "## Suite",
        f"- Suite ID: `{result.suite_id}`",
        f"- Executed cases: {len(result.executed_cases)}",
        "",
        "## Reasoning Modes",
        *[f"- `{mode.value}`" for mode in result.reasoning_modes],
        "",
        "## Dimension Results",
    ]
    for dimension, counts in result.aggregate_dimension_summaries.items():
        lines.append(
            f"- {dimension}: {counts.get('passed', 0)} passed, {counts.get('failed', 0)} failed"
        )
    lines.extend(
        [
            "",
            "## Grounding",
            _dimension_table(result, "grounding"),
            "## Evidence Fidelity",
            _dimension_table(result, "evidence_fidelity"),
            "## Causal Restraint",
            _dimension_table(result, "causal_restraint"),
            "## Epistemic Calibration",
            _dimension_table(result, "epistemic_calibration"),
            "## Contradiction Handling",
            _dimension_table(result, "contradiction_handling"),
            "## Limitation Propagation",
            _dimension_table(result, "limitation_propagation"),
            "## Literature Separation",
            _dimension_table(result, "literature_separation"),
            "## Reproducibility",
            _dimension_table(result, "reproducibility"),
            "## Case Failures",
        ]
    )
    failures = [
        finding
        for case_result in result.case_results
        for finding in case_result.findings
        if finding.severity is EvaluationSeverity.ERROR
    ]
    if failures:
        for finding in failures:
            lines.append(f"- `{finding.code.value}` ({finding.dimension.value}): {finding.message}")
    else:
        lines.append("- No error-severity findings.")
    lines.extend(["", "## Mode Comparison"])
    for comparison in result.mode_comparisons:
        lines.append(f"- `{comparison.reasoning_mode.value}`: {comparison.executed_cases} cases")
        lines.append(f"  - metric means: `{comparison.metric_means}`")
        lines.append(f"  - failures by code: `{comparison.failure_counts_by_code}`")
    lines.extend(
        [
            "",
            "## Known Evaluation Limitations",
            "- Rule-based checks do not measure scientific creativity or explanatory usefulness.",
            "- Plausible mechanisms are checked for grounding and labels, not substantive truth.",
            "- Confounder discovery is expectation-based and not comprehensive.",
            "- Domain-expert judgment remains outside the automated benchmark.",
            "",
        ]
    )
    return "\n".join(lines)


def _dimension_table(result: BenchmarkSuiteResult, dimension_name: str) -> str:
    rows = []
    for case_result in result.case_results:
        dimension = next(
            (
                item
                for item in case_result.dimension_results
                if item.dimension.value == dimension_name
            ),
            None,
        )
        if dimension is not None:
            rows.append(
                f"- `{case_result.benchmark_case_id}` / `{case_result.reasoning_mode.value}`: "
                f"{'pass' if dimension.passed else 'fail'}; metrics `{dimension.metrics}`"
            )
    return "\n".join(rows) if rows else "- Not evaluated."
