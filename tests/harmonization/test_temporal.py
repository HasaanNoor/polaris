from polaris.harmonization.temporal import normalize_year


def test_normalize_year_accepts_integer_and_numeric_string() -> None:
    assert normalize_year(2020) == 2020
    assert normalize_year("2020") == 2020


def test_normalize_year_rejects_ranges_and_non_annual_periods() -> None:
    assert normalize_year("2019-2020") is None
    assert normalize_year("FY2020") is None
    assert normalize_year("2020Q1") is None
    assert normalize_year(1700) is None
