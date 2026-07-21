from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polaris.schemas.dataset import DatasetManifest

CATALOG_DIR = Path(__file__).resolve().parents[2] / "catalog" / "datasets"


def catalog_manifest(name: str) -> DatasetManifest:
    with (CATALOG_DIR / name).open(encoding="utf-8") as file:
        return DatasetManifest.model_validate(json.load(file))


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
