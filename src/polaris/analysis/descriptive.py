"""Descriptive statistics for Phase 4 analysis."""

from collections import Counter

import numpy as np

from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    CategoricalSummary,
    DescriptiveAnalysisResult,
    DescriptiveVariableSummary,
    FindingSeverity,
    NumericSummary,
)
from polaris.analysis.utils import safe_float
from polaris.ingestion.models import DatasetIngestionResult
from polaris.schemas.common import DataType


def describe_variables(
    ingestion_result: DatasetIngestionResult,
    variable_ids: tuple[str, ...],
) -> DescriptiveAnalysisResult:
    variables = {
        variable.variable_id: variable for variable in ingestion_result.dataset_manifest.variables
    }
    summaries: list[DescriptiveVariableSummary] = []
    for variable_id in variable_ids:
        variable = variables[variable_id]
        values = tuple(
            record.values.get(variable_id) for record in ingestion_result.normalized_records
        )
        if variable.data_type in {DataType.INTEGER, DataType.FLOAT}:
            summaries.append(_numeric_summary(variable_id, variable.data_type.value, values))
        else:
            summaries.append(_categorical_summary(variable_id, variable.data_type.value, values))
    return DescriptiveAnalysisResult(variables=tuple(summaries))


def _numeric_summary(
    variable_id: str,
    variable_type: str,
    values: tuple[object, ...],
) -> DescriptiveVariableSummary:
    non_null = np.asarray([float(value) for value in values if value is not None], dtype=float)
    missing_count = len(values) - int(non_null.size)
    findings: list[AnalysisFinding] = []
    if non_null.size == 0:
        findings.append(
            AnalysisFinding(
                severity=FindingSeverity.WARNING,
                code=AnalysisFindingCode.ALL_NULL_VARIABLE,
                message=f'variable "{variable_id}" has no non-missing values',
                variable_ids=(variable_id,),
            )
        )
        return DescriptiveVariableSummary(
            variable_id=variable_id,
            variable_type=variable_type,
            numeric=NumericSummary(count=0, missing_count=missing_count),
            findings=tuple(findings),
        )
    if len(set(non_null.tolist())) == 1:
        findings.append(
            AnalysisFinding(
                severity=FindingSeverity.INFO,
                code=AnalysisFindingCode.CONSTANT_VARIABLE,
                message=f'variable "{variable_id}" is constant',
                variable_ids=(variable_id,),
            )
        )
    return DescriptiveVariableSummary(
        variable_id=variable_id,
        variable_type=variable_type,
        numeric=NumericSummary(
            count=int(non_null.size),
            missing_count=missing_count,
            mean=safe_float(np.mean(non_null)),
            standard_deviation=safe_float(np.std(non_null, ddof=1)) if non_null.size > 1 else None,
            minimum=safe_float(np.min(non_null)),
            percentile_25=safe_float(np.percentile(non_null, 25, method="linear")),
            median=safe_float(np.percentile(non_null, 50, method="linear")),
            percentile_75=safe_float(np.percentile(non_null, 75, method="linear")),
            maximum=safe_float(np.max(non_null)),
        ),
        findings=tuple(findings),
    )


def _categorical_summary(
    variable_id: str,
    variable_type: str,
    values: tuple[object, ...],
) -> DescriptiveVariableSummary:
    non_null = tuple(value for value in values if value is not None)
    counts = Counter(non_null)
    most_frequent = None
    most_frequent_count = 0
    if counts:
        most_frequent, most_frequent_count = sorted(
            counts.items(),
            key=lambda item: (-item[1], str(item[0])),
        )[0]
    return DescriptiveVariableSummary(
        variable_id=variable_id,
        variable_type=variable_type,
        categorical=CategoricalSummary(
            count=len(non_null),
            missing_count=len(values) - len(non_null),
            unique_count=len(counts),
            most_frequent_value=most_frequent,  # type: ignore[arg-type]
            most_frequent_value_count=most_frequent_count,
        ),
    )
