from pathlib import Path

import pytest

from polaris.ingestion import (
    DuplicateColumnError,
    IngestionConfiguration,
    SourceFileNotFoundError,
    SourceFileReadError,
    load_tabular_file,
)
from tests.ingestion.helpers import write_csv


def test_load_valid_csv_preserves_order_and_row_numbers(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "valid.csv", [["a", "b"], ["1", "2"], ["3", "4"]])

    loaded = load_tabular_file(path, IngestionConfiguration())

    assert loaded.source_columns == ("a", "b")
    assert [row.values for row in loaded.rows] == [("1", "2"), ("3", "4")]
    assert [row.row_number for row in loaded.rows] == [1, 2]
    assert [row.line_number for row in loaded.rows] == [2, 3]


def test_utf8_handling(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "utf8.csv", [["name"], ["Lahore"], ["São Paulo"]])

    loaded = load_tabular_file(path, IngestionConfiguration())

    assert loaded.rows[1].values == ("São Paulo",)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SourceFileNotFoundError):
        load_tabular_file(tmp_path / "missing.csv", IngestionConfiguration())


def test_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(SourceFileReadError):
        load_tabular_file(tmp_path, IngestionConfiguration())


def test_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    loaded = load_tabular_file(path, IngestionConfiguration())

    assert loaded.source_columns == ()
    assert loaded.rows == ()


def test_header_only_file(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "header.csv", [["a", "b"]])

    loaded = load_tabular_file(path, IngestionConfiguration())

    assert loaded.source_columns == ("a", "b")
    assert loaded.rows == ()


def test_duplicate_header_rejected(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "duplicate.csv", [["a", "a"], ["1", "2"]])

    with pytest.raises(DuplicateColumnError, match="duplicate"):
        load_tabular_file(path, IngestionConfiguration())


def test_malformed_row_lengths_are_retained(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "malformed.csv", [["a", "b"], ["1"], ["2", "3", "4"]])

    loaded = load_tabular_file(path, IngestionConfiguration())

    assert [row.row_number for row in loaded.malformed_rows] == [1, 2]
    assert loaded.rows == ()
