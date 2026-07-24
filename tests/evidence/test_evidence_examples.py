import json
from pathlib import Path


def test_example_artifacts_are_strict_json():
    for path in sorted(Path("examples/evidence").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1.0.0"
        assert payload["illustrative"] is True
        assert "narrative_conclusion" not in payload
