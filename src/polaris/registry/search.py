"""Pure deterministic matching utilities for dataset manifests."""

from collections.abc import Iterable

from polaris.registry.models import (
    DatasetSearchQuery,
    GeographicCoverageMatch,
    GeographicMatchType,
    TemporalCoverageMatch,
    TemporalMatchType,
    TemporalRequirement,
    TextMatchMode,
)
from polaris.schemas.common import TemporalScope, ValidationWarning
from polaris.schemas.dataset import DatasetManifest, DatasetVariable


def normalize_text(value: str) -> str:
    """Normalize text for deterministic case-insensitive matching."""

    return " ".join(value.casefold().strip().split())


def normalize_identifier(value: str) -> str:
    """Normalize identifiers without introducing fuzzy matching."""

    return value.casefold().strip()


def temporal_coverage_match(
    dataset_coverage: TemporalScope,
    requirement: TemporalRequirement | None,
) -> TemporalCoverageMatch:
    """Compare year ranges using interval logic, with None treated as open-ended."""

    if requirement is None:
        return TemporalCoverageMatch(
            match_type=TemporalMatchType.NOT_REQUESTED,
            dataset_start=dataset_coverage.start,
            dataset_end=dataset_coverage.end,
        )

    dataset_start = float("-inf") if dataset_coverage.start is None else dataset_coverage.start
    dataset_end = float("inf") if dataset_coverage.end is None else dataset_coverage.end
    requested_start = float("-inf") if requirement.start is None else requirement.start
    requested_end = float("inf") if requirement.end is None else requirement.end

    if dataset_start <= requested_start and dataset_end >= requested_end:
        match_type = TemporalMatchType.FULL
    elif dataset_start <= requested_end and dataset_end >= requested_start:
        match_type = TemporalMatchType.PARTIAL
    else:
        match_type = TemporalMatchType.NONE

    return TemporalCoverageMatch(
        match_type=match_type,
        dataset_start=dataset_coverage.start,
        dataset_end=dataset_coverage.end,
        requested_start=requirement.start,
        requested_end=requirement.end,
    )


def geographic_coverage_match(
    manifest: DatasetManifest,
    requested: Iterable[str],
) -> GeographicCoverageMatch:
    """Match explicit coverage codes or represented names in description text."""

    requested_values = tuple(requested)
    if not requested_values:
        return GeographicCoverageMatch(match_type=GeographicMatchType.NOT_REQUESTED)

    requested_norm = {normalize_identifier(value): value for value in requested_values}
    code_norm = {normalize_identifier(code): code for code in manifest.geographic_coverage.codes}
    exact_matches = tuple(code_norm[value] for value in requested_norm if value in code_norm)
    if exact_matches:
        return GeographicCoverageMatch(
            match_type=GeographicMatchType.EXACT,
            requested=requested_values,
            matched=exact_matches,
        )

    description = manifest.geographic_coverage.description
    if description is not None:
        description_norm = normalize_text(description)
        description_matches = tuple(
            original
            for value, original in requested_norm.items()
            if value and value in description_norm
        )
        if description_matches:
            return GeographicCoverageMatch(
                match_type=GeographicMatchType.DESCRIPTION,
                requested=requested_values,
                matched=description_matches,
            )

    return GeographicCoverageMatch(
        match_type=GeographicMatchType.NONE,
        requested=requested_values,
    )


def warning_messages(manifest: DatasetManifest) -> tuple[str, ...]:
    """Collect warning and access-restriction metadata without reinterpreting it."""

    messages: list[str] = []
    messages.extend(
        _format_validation_warning("comparability", warning)
        for warning in manifest.comparability_warnings
    )
    messages.extend(
        _format_validation_warning("licensing", warning) for warning in manifest.licensing_warnings
    )
    messages.extend(
        f"access restriction: {restriction}" for restriction in manifest.access_restrictions
    )
    return tuple(messages)


def manifest_has_warnings(manifest: DatasetManifest) -> bool:
    return bool(
        manifest.comparability_warnings
        or manifest.licensing_warnings
        or manifest.access_restrictions
    )


def variable_matches_keyword(variable: DatasetVariable, keyword: str) -> bool:
    keyword_norm = normalize_text(keyword)
    searchable = [
        variable.variable_id,
        variable.label,
        variable.description,
        variable.source_field_name,
    ]
    return any(value is not None and keyword_norm in normalize_text(value) for value in searchable)


def variable_matches_identifier(variable: DatasetVariable, variable_ids: Iterable[str]) -> bool:
    requested = {normalize_identifier(variable_id) for variable_id in variable_ids}
    return normalize_identifier(variable.variable_id) in requested


def text_values_match(
    haystack_values: Iterable[str | None],
    needles: Iterable[str],
    mode: TextMatchMode,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether text values satisfy the query terms and which terms matched."""

    needle_values = tuple(needles)
    if not needle_values:
        return True, ()

    haystack = " ".join(normalize_text(value) for value in haystack_values if value is not None)
    matched = tuple(needle for needle in needle_values if normalize_text(needle) in haystack)
    if mode is TextMatchMode.ALL:
        return len(matched) == len(needle_values), matched
    return bool(matched), matched


def exact_values_match(
    haystack_value: str | None,
    needles: Iterable[str],
) -> tuple[bool, str | None]:
    """Case-insensitive exact matching for fields such as provider or frequency."""

    needle_values = tuple(needles)
    if not needle_values:
        return True, None
    if haystack_value is None:
        return False, None
    normalized = normalize_identifier(haystack_value)
    for needle in needle_values:
        if normalized == normalize_identifier(needle):
            return True, needle
    return False, None


def _format_validation_warning(category: str, warning: ValidationWarning) -> str:
    field = f" {warning.field}" if warning.field is not None else ""
    return f"{category} warning {warning.code}{field}: {warning.message}"


def manifest_matches_query(
    manifest: DatasetManifest,
    query: DatasetSearchQuery,
) -> tuple[
    bool,
    tuple[str, ...],
    tuple[str, ...],
    TemporalCoverageMatch | None,
    GeographicCoverageMatch | None,
]:
    """Evaluate one manifest against a structured query and return explanations."""

    reasons: list[str] = []

    if query.dataset_ids:
        requested = {normalize_identifier(dataset_id) for dataset_id in query.dataset_ids}
        if normalize_identifier(manifest.dataset_id) not in requested:
            return False, (), (), None, None
        reasons.append(f'dataset_id matched "{manifest.dataset_id}"')

    if query.providers:
        matched, provider = exact_values_match(manifest.provider, query.providers)
        if not matched:
            return False, (), (), None, None
        reasons.append(f'provider matched "{provider}"')

    if query.statuses:
        if manifest.status not in query.statuses:
            return False, (), (), None, None
        reasons.append(f'status matched "{manifest.status.value}"')

    if query.frequencies:
        matched, frequency = exact_values_match(manifest.frequency, query.frequencies)
        if not matched:
            return False, (), (), None, None
        reasons.append(f'frequency matched "{frequency}"')

    if query.licenses:
        matched, license_value = exact_values_match(manifest.license, query.licenses)
        if not matched:
            return False, (), (), None, None
        reasons.append(f'license matched "{license_value}"')

    if query.require_unrestricted_access:
        if manifest.access_restrictions:
            return False, (), (), None, None
        reasons.append("access has no recorded restrictions")

    if query.require_methodology_reference:
        if manifest.methodology_reference is None:
            return False, (), (), None, None
        reasons.append("methodology reference is present")

    if not query.include_datasets_with_warnings and manifest_has_warnings(manifest):
        return False, (), (), None, None

    keyword_matched, matched_keywords = text_values_match(
        [
            manifest.dataset_id,
            manifest.title,
            manifest.provider,
            manifest.description,
            manifest.license,
            manifest.frequency,
        ],
        query.keywords,
        query.match_mode,
    )
    if not keyword_matched:
        return False, (), (), None, None
    reasons.extend(f'keyword matched "{keyword}"' for keyword in matched_keywords)

    identifier_variable_ids = _identifier_matched_variables(manifest, query.variable_ids)
    keyword_variable_ids = _keyword_matched_variables(manifest, query)
    if query.variable_ids and not identifier_variable_ids:
        return False, (), (), None, None
    if query.variable_keywords and not keyword_variable_ids:
        return False, (), (), None, None
    matched_variable_ids = tuple(dict.fromkeys(identifier_variable_ids + keyword_variable_ids))
    if query.variable_ids:
        reasons.append(
            "variable identifier matched "
            + ", ".join(f'"{variable_id}"' for variable_id in identifier_variable_ids)
        )
    if query.variable_keywords:
        reasons.append(
            "variable metadata matched "
            + ", ".join(f'"{variable_id}"' for variable_id in keyword_variable_ids)
        )

    temporal_match: TemporalCoverageMatch | None = None
    if query.temporal is not None:
        temporal_match = temporal_coverage_match(manifest.temporal_coverage, query.temporal)
        if temporal_match.match_type is TemporalMatchType.NONE:
            return False, (), (), None, None
        reasons.append(
            "dataset coverage "
            f"{temporal_match.match_type.value} overlapped "
            f"{query.temporal.start}-{query.temporal.end}"
        )

    geographic_match: GeographicCoverageMatch | None = None
    if query.geographic:
        geographic_match = geographic_coverage_match(manifest, query.geographic)
        if geographic_match.match_type is GeographicMatchType.NONE:
            return False, (), (), None, None
        reasons.append(
            "geographic coverage matched "
            + ", ".join(f'"{value}"' for value in geographic_match.matched)
        )

    if not reasons:
        reasons.append("no filters requested")

    return (
        True,
        tuple(dict.fromkeys(matched_variable_ids)),
        tuple(reasons),
        temporal_match,
        geographic_match,
    )


def _identifier_matched_variables(
    manifest: DatasetManifest,
    variable_ids: Iterable[str],
) -> tuple[str, ...]:
    requested_variable_ids = tuple(variable_ids)
    if not requested_variable_ids:
        return ()
    return tuple(
        variable.variable_id
        for variable in manifest.variables
        if variable_matches_identifier(variable, requested_variable_ids)
    )


def _keyword_matched_variables(
    manifest: DatasetManifest,
    query: DatasetSearchQuery,
) -> tuple[str, ...]:
    if not query.variable_keywords:
        return ()
    return tuple(
        variable.variable_id
        for variable in manifest.variables
        if _variable_keyword_match(variable, query.variable_keywords, query.match_mode)
    )


def _variable_keyword_match(
    variable: DatasetVariable,
    keywords: Iterable[str],
    mode: TextMatchMode,
) -> bool:
    keyword_values = tuple(keywords)
    if mode is TextMatchMode.ALL:
        return all(variable_matches_keyword(variable, keyword) for keyword in keyword_values)
    return any(variable_matches_keyword(variable, keyword) for keyword in keyword_values)
