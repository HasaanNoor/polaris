from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "schemas"


def load_example(name: str) -> dict[str, Any]:
    with (EXAMPLES_DIR / name).open() as file:
        return json.load(file)


@pytest.fixture
def example_data() -> dict[str, dict[str, Any]]:
    return {
        "research_question": load_example("research_question.json"),
        "dataset_manifest": load_example("dataset_manifest.json"),
        "agent_message": load_example("agent_message.json"),
        "provenance_record": load_example("provenance_record.json"),
        "statistical_specification": load_example("statistical_specification.json"),
        "research_artifact": load_example("research_artifact.json"),
    }


@pytest.fixture
def copy_data():
    def _copy(data: dict[str, Any]) -> dict[str, Any]:
        return deepcopy(data)

    return _copy
