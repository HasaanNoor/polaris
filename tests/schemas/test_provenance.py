import pytest
from pydantic import ValidationError

from polaris.schemas.common import DataValueCategory
from polaris.schemas.provenance import ProvenanceRecord


def test_valid_provenance_record_creation(example_data):
    record = ProvenanceRecord.model_validate(example_data["provenance_record"])

    assert record.data_value_category == DataValueCategory.RETRIEVED_SOURCE_DATA


def test_provenance_record_json_round_trip(example_data):
    record = ProvenanceRecord.model_validate(example_data["provenance_record"])

    assert ProvenanceRecord.model_validate_json(record.model_dump_json()) == record


def test_provenance_record_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["provenance_record"])
    data["mutable_note"] = "not part of contract"

    with pytest.raises(ValidationError):
        ProvenanceRecord.model_validate(data)


def test_provenance_record_is_immutable(example_data):
    record = ProvenanceRecord.model_validate(example_data["provenance_record"])

    with pytest.raises(ValidationError):
        record.actor_id = "other_agent"


def test_provenance_record_requires_identifier(example_data, copy_data):
    data = copy_data(example_data["provenance_record"])
    del data["provenance_record_id"]

    with pytest.raises(ValidationError):
        ProvenanceRecord.model_validate(data)
