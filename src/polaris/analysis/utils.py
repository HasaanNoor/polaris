"""Small numerical helpers for JSON-safe deterministic analysis."""

import math
from collections.abc import Iterable

import numpy as np


def safe_float(value: object) -> float | None:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def safe_bool(value: object) -> bool | None:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return None


def finite_array(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(tuple(float(value) for value in values), dtype=float)
    return array[np.isfinite(array)]


def summarize(
    values: Iterable[float],
) -> tuple[int, float | None, float | None, float | None, float | None]:
    array = finite_array(values)
    if array.size == 0:
        return 0, None, None, None, None
    std = safe_float(np.std(array, ddof=1)) if array.size > 1 else None
    return (
        int(array.size),
        safe_float(np.mean(array)),
        std,
        safe_float(np.min(array)),
        safe_float(np.max(array)),
    )
