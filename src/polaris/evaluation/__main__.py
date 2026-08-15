"""Optional local benchmark command for Phase 19."""

from pathlib import Path

from examples.evaluation.benchmarks.baseline import baseline_suite
from polaris.evaluation.benchmark import run_benchmark_suite
from polaris.evaluation.reporting import benchmark_result_to_json, benchmark_result_to_markdown


def main() -> None:
    suite = baseline_suite()
    result = run_benchmark_suite(suite=suite)
    output_dir = Path("examples/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "baseline_result.json").write_text(
        benchmark_result_to_json(result),
        encoding="utf-8",
    )
    (output_dir / "baseline_report.md").write_text(
        benchmark_result_to_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
