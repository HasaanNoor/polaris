"""Reviewed WHO dimension filtering rules."""

from __future__ import annotations

from typing import Any

from polaris.who.models import WHODimensionRule, WHOMissingnessReasonCode, WHOVariableMapping

COUNTRY_SPATIAL_TYPES = {"COUNTRY"}
AGGREGATE_SPATIAL_TYPES = {
    "GLOBAL",
    "REGION",
    "UNREGION",
    "UNSDGREGION",
    "WORLDBANKREGION",
    "WORLDBANKINCOMEGROUP",
    "GBDREGION",
}
PROJECTED_YEAR_START_BY_INDICATOR = {"M_Est_tob_curr_std": 2025}


def both_sexes_rule(field: str = "Dim1") -> WHODimensionRule:
    return WHODimensionRule(
        field=field,
        allowed_values=("SEX_BTSX",),
        reason="Provider supplies an explicit both-sexes headline category.",
    )


def exact_dimension_rule(field: str, value: str | None, reason: str) -> WHODimensionRule:
    return WHODimensionRule(field=field, allowed_values=(value,), reason=reason)


def total_residence_rule(field: str = "Dim1") -> WHODimensionRule:
    return WHODimensionRule(
        field=field,
        allowed_values=("RESIDENCEAREATYPE_TOTL",),
        reason="Provider supplies total residence category; urban/rural rows are not averaged.",
    )


def row_matches_mapping(row: dict[str, Any], mapping: WHOVariableMapping) -> bool:
    """Return whether a raw WHO row satisfies reviewed mapping filters."""

    if row.get("SpatialDimType") not in COUNTRY_SPATIAL_TYPES:
        return False
    year = row.get(mapping.year_field)
    if not isinstance(year, int):
        return False
    if mapping.supported_year_range is not None:
        start, end = mapping.supported_year_range
        if year < start or year > end:
            return False
    if not mapping.projections_accepted and is_projected_row(row, mapping.who_indicator_id):
        return False
    for rule in mapping.required_dimension_filters:
        if row.get(rule.field) not in rule.allowed_values:
            return False
    return True


def is_aggregate_row(row: dict[str, Any]) -> bool:
    return row.get("SpatialDimType") in AGGREGATE_SPATIAL_TYPES


def is_projected_row(row: dict[str, Any], indicator_id: str) -> bool:
    """Identify reviewed projection rows without inferring undocumented statuses."""

    threshold = PROJECTED_YEAR_START_BY_INDICATOR.get(indicator_id)
    return (
        isinstance(row.get("TimeDim"), int)
        and threshold is not None
        and row["TimeDim"] >= threshold
    )


def exclusion_reason(row: dict[str, Any], mapping: WHOVariableMapping) -> WHOMissingnessReasonCode:
    """Return the stable exclusion reason for a row not selected by a mapping."""

    if is_aggregate_row(row):
        return WHOMissingnessReasonCode.AGGREGATE_ROW_EXCLUDED
    if is_projected_row(row, mapping.who_indicator_id):
        return WHOMissingnessReasonCode.PROJECTED_ROW_EXCLUDED
    return WHOMissingnessReasonCode.ROW_EXCLUDED_BY_DIMENSION_RULE
