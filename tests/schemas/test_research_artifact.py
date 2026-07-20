from pathlib import Path

import pytest
from pydantic import ValidationError

from polaris.schemas.agents import AgentMessage
from polaris.schemas.artifact import ResearchArtifact
from polaris.schemas.common import DataValueCategory, EvidenceStrength, InvestigationStatus
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.provenance import ProvenanceRecord
from polaris.schemas.research_question import ResearchQuestion
from polaris.schemas.statistics import StatisticalSpecification


EXAMPLE_MODELS = {
    "research_question.json": ResearchQuestion,
    "dataset_manifest.json": DatasetManifest,
    "agent_message.json": AgentMessage,
    "provenance_record.json": ProvenanceRecord,
    "statistical_specification.json": StatisticalSpecification,
    "research_artifact.json": ResearchArtifact,
}


def test_valid_research_artifact_creation(example_data):
    artifact = ResearchArtifact.model_validate(example_data["research_artifact"])

    assert artifact.investigation_status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert artifact.evidence_quality_assessment.strength == EvidenceStrength.INSUFFICIENT


def test_research_artifact_json_round_trip(example_data):
    artifact = ResearchArtifact.model_validate(example_data["research_artifact"])

    assert ResearchArtifact.model_validate_json(artifact.model_dump_json()) == artifact


def test_research_artifact_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["research_artifact"])
    data["report_markdown"] = "deferred to later phase"

    with pytest.raises(ValidationError):
        ResearchArtifact.model_validate(data)


def test_artifact_status_represents_insufficient_evidence(example_data):
    artifact = ResearchArtifact.model_validate(example_data["research_artifact"])

    assert artifact.investigation_status == InvestigationStatus.INSUFFICIENT_EVIDENCE


def test_artifact_separates_observed_derived_analytical_and_narrative_sections(example_data):
    artifact = ResearchArtifact.model_validate(example_data["research_artifact"])

    assert artifact.observed_data_references[0].data_value_category == DataValueCategory.OBSERVED_VALUE
    assert artifact.derived_data_references[0].data_value_category == DataValueCategory.DERIVED_VARIABLE
    assert artifact.analytical_results.descriptive_values
    assert (
        artifact.analytical_results.narrative_interpretations[0].data_value_category
        == DataValueCategory.NARRATIVE_INTERPRETATION
    )


def test_research_artifact_rejects_inconsistent_insufficient_evidence_status(example_data, copy_data):
    data = copy_data(example_data["research_artifact"])
    data["evidence_quality_assessment"]["strength"] = "moderate"

    with pytest.raises(ValidationError):
        ResearchArtifact.model_validate(data)


def test_research_artifact_rejects_invalid_update_order(example_data, copy_data):
    data = copy_data(example_data["research_artifact"])
    data["updated_at"] = "2026-07-20T12:29:59Z"

    with pytest.raises(ValidationError):
        ResearchArtifact.model_validate(data)


def test_every_json_example_loads_successfully():
    examples_dir = Path(__file__).resolve().parents[2] / "examples" / "schemas"

    for file_name, model in EXAMPLE_MODELS.items():
        payload = (examples_dir / file_name).read_text()
        model.model_validate_json(payload)
