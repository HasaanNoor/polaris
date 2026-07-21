from polaris.registry import (
    GeographicMatchType,
    TemporalMatchType,
    TemporalRequirement,
    geographic_coverage_match,
    temporal_coverage_match,
)
from polaris.schemas.common import TemporalScope


def test_full_temporal_coverage() -> None:
    result = temporal_coverage_match(
        TemporalScope(start=1990, end=2023),
        TemporalRequirement(start=2000, end=2020),
    )

    assert result.match_type is TemporalMatchType.FULL


def test_partial_temporal_overlap() -> None:
    result = temporal_coverage_match(
        TemporalScope(start=2015, end=2023),
        TemporalRequirement(start=2000, end=2020),
    )

    assert result.match_type is TemporalMatchType.PARTIAL


def test_no_temporal_overlap() -> None:
    result = temporal_coverage_match(
        TemporalScope(start=1990, end=2000),
        TemporalRequirement(start=2010, end=2020),
    )

    assert result.match_type is TemporalMatchType.NONE


def test_open_ended_temporal_coverage() -> None:
    result = temporal_coverage_match(
        TemporalScope(start=1990, end=None),
        TemporalRequirement(start=2020, end=2030),
    )

    assert result.match_type is TemporalMatchType.FULL


def test_exact_geographic_match(world_bank_manifest) -> None:
    result = geographic_coverage_match(world_bank_manifest, ["GLOBAL"])

    assert result.match_type is GeographicMatchType.EXACT
    assert result.matched == ("GLOBAL",)


def test_absent_geographic_match(world_bank_manifest) -> None:
    result = geographic_coverage_match(world_bank_manifest, ["PAK"])

    assert result.match_type is GeographicMatchType.NONE


def test_regional_or_global_description_match(who_manifest) -> None:
    result = geographic_coverage_match(who_manifest, ["global health"])

    assert result.match_type is GeographicMatchType.DESCRIPTION
