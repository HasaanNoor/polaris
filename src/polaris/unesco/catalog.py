"""Local UNESCO UIS catalog loading."""

from __future__ import annotations

import csv
from pathlib import Path

from polaris.ingestion.loader import calculate_sha256

UNESCO_DATASETS = ("DEM", "SDG", "SCN-SDG", "SDG11")


def dataset_paths(*, raw_root: str | Path = "data/raw/unesco") -> dict[str, dict[str, Path]]:
    root = Path(raw_root)
    return {
        dataset: {
            "data": root / dataset / f"{dataset}_DATA_NATIONAL.csv",
            "labels": root / dataset / f"{dataset}_LABEL.csv",
            "countries": root / dataset / f"{dataset}_COUNTRY.csv",
            "metadata": root / dataset / f"{dataset}_METADATA.csv",
            "readme": root / dataset / f"{dataset}_README_RELEASE_2026_February.md",
        }
        for dataset in UNESCO_DATASETS
    }


def load_indicator_labels(*, raw_root: str | Path = "data/raw/unesco") -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    for dataset, paths in dataset_paths(raw_root=raw_root).items():
        path = paths["labels"]
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as file:
            labels[dataset] = {
                row["INDICATOR_ID"]: row["INDICATOR_LABEL_EN"]
                for row in csv.DictReader(file)
                if row.get("INDICATOR_ID")
            }
    return labels


def load_country_names(*, raw_root: str | Path = "data/raw/unesco") -> dict[str, dict[str, str]]:
    countries: dict[str, dict[str, str]] = {}
    for dataset, paths in dataset_paths(raw_root=raw_root).items():
        path = paths["countries"]
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as file:
            countries[dataset] = {
                row["COUNTRY_ID"]: row["COUNTRY_NAME_EN"]
                for row in csv.DictReader(file)
                if row.get("COUNTRY_ID")
            }
    return countries


def source_checksums(*, raw_root: str | Path = "data/raw/unesco") -> dict[str, str]:
    checksums: dict[str, str] = {}
    for dataset, paths in dataset_paths(raw_root=raw_root).items():
        for kind, path in paths.items():
            if path.exists():
                checksums[f"{dataset}:{kind}"] = calculate_sha256(path)
    return checksums
