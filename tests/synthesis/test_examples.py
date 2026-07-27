import json
from pathlib import Path

from polaris.synthesis.models import SynthesisArtifact


def test_illustrative_synthesis_example_validates():
    path = Path("examples/synthesis/interdisciplinary_synthesis.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    artifact = SynthesisArtifact.model_validate(payload)

    assert artifact.synthesis_id.startswith("synthesis_")
    assert artifact.schema_version == "1.0.0"
