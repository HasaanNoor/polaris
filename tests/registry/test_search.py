from polaris.registry import DatasetSearchQuery, TemporalRequirement, TextMatchMode
from polaris.schemas.common import DatasetStatus


def test_empty_query_returns_all_datasets(registry) -> None:
    results = registry.search(DatasetSearchQuery())

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
        "unesco_uis_illustrative",
    ]
    assert all(result.match_reasons == ("no filters requested",) for result in results)


def test_case_insensitive_keyword_search(registry) -> None:
    results = registry.search(DatasetSearchQuery(keywords=("HEALTH",)))

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
    ]


def test_provider_filter(registry) -> None:
    results = registry.search(DatasetSearchQuery(providers=("World Bank",)))

    assert [result.dataset_id for result in results] == ["world_bank_wdi_illustrative"]
    assert 'provider matched "World Bank"' in results[0].match_reasons


def test_status_filter(registry) -> None:
    results = registry.search(DatasetSearchQuery(statuses=(DatasetStatus.CANDIDATE,)))

    assert len(results) == 3
    assert all('status matched "candidate"' in result.match_reasons for result in results)


def test_variable_identifier_filter(registry) -> None:
    results = registry.search(DatasetSearchQuery(variable_ids=("maternal_mortality_ratio",)))

    assert [result.dataset_id for result in results] == ["who_gho_illustrative"]
    assert results[0].matched_variable_ids == ("maternal_mortality_ratio",)


def test_variable_label_search(registry) -> None:
    results = registry.search(DatasetSearchQuery(variable_keywords=("life expectancy",)))

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
    ]
    assert [result.matched_variable_ids for result in results] == [
        ("life_expectancy_at_birth",),
        ("life_expectancy_at_birth",),
    ]


def test_multiple_filters_use_and_semantics(registry) -> None:
    results = registry.search(
        DatasetSearchQuery(
            providers=("World Bank",),
            variable_keywords=("life expectancy",),
            temporal=TemporalRequirement(start=2000, end=2020),
        )
    )

    assert [result.dataset_id for result in results] == ["world_bank_wdi_illustrative"]
    assert results[0].temporal_overlap is not None
    assert results[0].temporal_overlap.match_type.value == "full"


def test_multiple_values_within_filter_use_any_semantics(registry) -> None:
    results = registry.search(
        DatasetSearchQuery(providers=("World Bank", "World Health Organization"))
    )

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
    ]


def test_all_match_mode_for_keywords(registry) -> None:
    results = registry.search(
        DatasetSearchQuery(keywords=("health", "education"), match_mode=TextMatchMode.ALL)
    )

    assert [result.dataset_id for result in results] == ["world_bank_wdi_illustrative"]


def test_no_match_behavior(registry) -> None:
    assert registry.search(DatasetSearchQuery(providers=("Missing provider",))) == ()


def test_search_ordering_is_deterministic(registry) -> None:
    first = registry.search(DatasetSearchQuery(variable_keywords=("enrollment",)))
    second = registry.search(DatasetSearchQuery(variable_keywords=("enrollment",)))

    assert [result.dataset_id for result in first] == [result.dataset_id for result in second]


def test_match_reasons_are_populated(registry) -> None:
    results = registry.search(DatasetSearchQuery(variable_keywords=("enrollment",)))

    assert all(result.match_reasons for result in results)


def test_warnings_are_preserved(registry) -> None:
    results = registry.search(DatasetSearchQuery(providers=("UNESCO Institute for Statistics",)))

    assert any("comparability warning" in warning for warning in results[0].warnings)
    assert any("access restriction" in warning for warning in results[0].warnings)


def test_unrestricted_access_filter(registry) -> None:
    results = registry.search(DatasetSearchQuery(require_unrestricted_access=True))

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
    ]


def test_methodology_reference_requirement(registry) -> None:
    results = registry.search(DatasetSearchQuery(require_methodology_reference=True))

    assert [result.dataset_id for result in results] == [
        "world_bank_wdi_illustrative",
        "who_gho_illustrative",
    ]


def test_exclude_warning_bearing_datasets(registry) -> None:
    results = registry.search(DatasetSearchQuery(include_datasets_with_warnings=False))

    assert results == ()


def test_license_filter(registry) -> None:
    results = registry.search(
        DatasetSearchQuery(
            licenses=("Illustrative candidate record; redistribution terms require review.",)
        )
    )

    assert [result.dataset_id for result in results] == ["unesco_uis_illustrative"]
