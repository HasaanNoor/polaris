"""Deterministic local CSV loading and checksum utilities."""

import csv
import hashlib
from pathlib import Path

from polaris.ingestion.errors import (
    DuplicateColumnError,
    MalformedTabularDataError,
    SourceFileNotFoundError,
    SourceFileReadError,
)
from polaris.ingestion.models import IngestionConfiguration, LoadedTabularFile, RawTabularRow


def calculate_sha256(path: str | Path) -> str:
    """Return the SHA-256 checksum for a local file without using metadata."""

    source_path = Path(path)
    digest = hashlib.sha256()
    try:
        with source_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SourceFileReadError(
            f"{source_path}: unable to read source file for checksum: {exc}",
            source_path=source_path,
        ) from exc
    return digest.hexdigest()


def file_size(path: str | Path) -> int:
    """Return local file size in bytes."""

    source_path = Path(path)
    try:
        return source_path.stat().st_size
    except OSError as exc:
        raise SourceFileReadError(
            f"{source_path}: unable to inspect source file: {exc}",
            source_path=source_path,
        ) from exc


def load_tabular_file(
    path: str | Path,
    configuration: IngestionConfiguration,
) -> LoadedTabularFile:
    """Load a local CSV file while preserving deterministic source ordering."""

    source_path = Path(path)
    if not source_path.exists():
        raise SourceFileNotFoundError(
            f"{source_path}: source file does not exist",
            source_path=source_path,
        )
    if not source_path.is_file():
        raise SourceFileReadError(
            f"{source_path}: source path is not a regular file",
            source_path=source_path,
        )

    try:
        with source_path.open(newline="", encoding=configuration.encoding) as file:
            reader = csv.reader(file, delimiter=configuration.delimiter, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                return LoadedTabularFile(
                    source_path=str(source_path),
                    source_columns=(),
                    rows=(),
                    malformed_rows=(),
                    parse_succeeded=True,
                )

            source_columns = tuple(column.strip() for column in header)
            duplicate = _first_duplicate(source_columns)
            if duplicate is not None:
                raise DuplicateColumnError(
                    f'{source_path}: duplicate source column "{duplicate}"',
                    source_path=source_path,
                    column_name=duplicate,
                )

            rows: list[RawTabularRow] = []
            malformed_rows: list[RawTabularRow] = []
            expected_width = len(source_columns)
            for row_number, values in enumerate(reader, start=1):
                line_number = reader.line_num
                parsed_row = RawTabularRow(
                    row_number=row_number,
                    line_number=line_number,
                    values=tuple(values),
                )
                if len(values) != expected_width:
                    malformed_rows.append(parsed_row)
                else:
                    rows.append(parsed_row)
    except UnicodeError as exc:
        raise SourceFileReadError(
            f"{source_path}: unable to decode source file with {configuration.encoding}",
            source_path=source_path,
        ) from exc
    except csv.Error as exc:
        raise MalformedTabularDataError(
            f"{source_path}: malformed CSV near line {getattr(reader, 'line_num', '?')}: {exc}",
            source_path=source_path,
            row_number=getattr(reader, "line_num", None),
        ) from exc
    except OSError as exc:
        raise SourceFileReadError(
            f"{source_path}: unable to read source file: {exc}",
            source_path=source_path,
        ) from exc

    return LoadedTabularFile(
        source_path=str(source_path),
        source_columns=source_columns,
        rows=tuple(rows),
        malformed_rows=tuple(malformed_rows),
        parse_succeeded=True,
    )


def _first_duplicate(values: tuple[str, ...]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
