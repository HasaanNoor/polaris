import json
from pathlib import Path

from polaris.coordination import CoordinatedAssessment


def test_coordination_example_is_valid():
    path = Path("examples/coordination/coordinated_assessment.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    coordinated = CoordinatedAssessment.model_validate(payload)

    assert coordinated.evidence_domain_map
    assert coordinated.claim_domain_map
    assert coordinated.agreements
    assert coordinated.domain_gaps
