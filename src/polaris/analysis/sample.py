"""Analysis-ready complete-case sample construction."""

from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    AnalysisSample,
    RowExclusion,
)
from polaris.ingestion.models import DatasetIngestionResult


def build_analysis_sample(
    ingestion_result: DatasetIngestionResult,
    variable_ids: tuple[str, ...],
) -> tuple[AnalysisSample, tuple[AnalysisFinding, ...]]:
    rows: list[dict[str, int | float | str | bool]] = []
    included_rows: list[int] = []
    included_lines: list[int] = []
    exclusions: list[RowExclusion] = []

    for record in ingestion_result.normalized_records:
        missing = tuple(
            variable_id for variable_id in variable_ids if record.values.get(variable_id) is None
        )
        if missing:
            exclusions.append(
                RowExclusion(
                    row_number=record.row_number,
                    source_line_number=record.source_line_number,
                    reason="complete-case analysis excluded row with missing required values",
                    variable_ids=missing,
                )
            )
            continue
        rows.append({variable_id: record.values[variable_id] for variable_id in variable_ids})  # type: ignore[dict-item]
        included_rows.append(record.row_number)
        included_lines.append(record.source_line_number)

    findings: list[AnalysisFinding] = []
    if exclusions:
        findings.append(
            AnalysisFinding(
                severity="info",
                code=AnalysisFindingCode.EXCLUDED_MISSING_ROWS,
                message="complete-case analysis excluded rows with missing required values",
                variable_ids=variable_ids,
                source_row_numbers=tuple(exclusion.row_number for exclusion in exclusions),
            )
        )

    return (
        AnalysisSample(
            variable_ids=variable_ids,
            rows=tuple(rows),
            included_row_numbers=tuple(included_rows),
            included_source_line_numbers=tuple(included_lines),
            exclusions=tuple(exclusions),
        ),
        tuple(findings),
    )
