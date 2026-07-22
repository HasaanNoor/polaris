"""Pearson and Spearman correlation calculations."""

import numpy as np
from scipy import stats

from polaris.analysis.models import (
    AnalysisFinding,
    AnalysisFindingCode,
    CorrelationAnalysisResult,
    CorrelationPairResult,
    FindingSeverity,
)
from polaris.analysis.utils import safe_float
from polaris.ingestion.models import DatasetIngestionResult


def correlate_variables(
    ingestion_result: DatasetIngestionResult,
    variable_ids: tuple[str, ...],
    *,
    method: str,
) -> CorrelationAnalysisResult:
    pairs: list[CorrelationPairResult] = []
    for left_index, left_id in enumerate(variable_ids):
        for right_id in variable_ids[left_index + 1 :]:
            pairs.append(_correlate_pair(ingestion_result, left_id, right_id, method=method))
    return CorrelationAnalysisResult(method=method, pairs=tuple(pairs))  # type: ignore[arg-type]


def _correlate_pair(
    ingestion_result: DatasetIngestionResult,
    left_id: str,
    right_id: str,
    *,
    method: str,
) -> CorrelationPairResult:
    left: list[float] = []
    right: list[float] = []
    excluded: list[int] = []
    for record in ingestion_result.normalized_records:
        left_value = record.values.get(left_id)
        right_value = record.values.get(right_id)
        if left_value is None or right_value is None:
            excluded.append(record.row_number)
            continue
        left.append(float(left_value))
        right.append(float(right_value))

    warnings: list[AnalysisFinding] = []
    if len(left) < 2:
        warnings.append(
            _undefined("correlation requires at least two paired observations", left_id, right_id)
        )
        return CorrelationPairResult(
            variable_id_1=left_id,
            variable_id_2=right_id,
            method=method,  # type: ignore[arg-type]
            observation_count=len(left),
            defined=False,
            warnings=tuple(warnings),
            excluded_row_numbers=tuple(excluded),
        )
    if len(set(left)) == 1 or len(set(right)) == 1:
        warnings.append(
            _undefined("correlation is undefined for constant variables", left_id, right_id)
        )
        return CorrelationPairResult(
            variable_id_1=left_id,
            variable_id_2=right_id,
            method=method,  # type: ignore[arg-type]
            observation_count=len(left),
            defined=False,
            warnings=tuple(warnings),
            excluded_row_numbers=tuple(excluded),
        )
    if method == "pearson":
        statistic = stats.pearsonr(np.asarray(left), np.asarray(right))
    else:
        statistic = stats.spearmanr(np.asarray(left), np.asarray(right))
    coefficient = safe_float(statistic.statistic)
    p_value = safe_float(statistic.pvalue)
    if coefficient is not None and np.isclose(abs(coefficient), 1.0):
        warnings.append(
            AnalysisFinding(
                severity=FindingSeverity.INFO,
                code=AnalysisFindingCode.PERFECT_CORRELATION,
                message="correlation coefficient is exactly -1 or 1",
                variable_ids=(left_id, right_id),
                method=method,
                statistic=coefficient,
            )
        )
    return CorrelationPairResult(
        variable_id_1=left_id,
        variable_id_2=right_id,
        method=method,  # type: ignore[arg-type]
        observation_count=len(left),
        correlation_coefficient=coefficient,
        p_value=p_value,
        defined=coefficient is not None,
        warnings=tuple(warnings),
        excluded_row_numbers=tuple(excluded),
    )


def _undefined(message: str, left_id: str, right_id: str) -> AnalysisFinding:
    return AnalysisFinding(
        severity=FindingSeverity.WARNING,
        code=AnalysisFindingCode.UNDEFINED_STATISTIC,
        message=message,
        variable_ids=(left_id, right_id),
    )
