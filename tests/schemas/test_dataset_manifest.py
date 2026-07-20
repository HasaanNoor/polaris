import pytest
from pydantic import ValidationError

from polaris.schemas.common import DatasetStatus
from polaris.schemas.dataset import DatasetManifest


def test_valid_dataset_manifest_creation(example_data):
    manifest = DatasetManifest.model_validate(example_data["dataset_manifest"])

    assert manifest.dataset_id == "ds_synthetic_oecd_indicators"
    assert manifest.status == DatasetStatus.CANDIDATE


def test_dataset_manifest_json_round_trip(example_data):
    manifest = DatasetManifest.model_validate(example_data["dataset_manifest"])

    assert DatasetManifest.model_validate_json(manifest.model_dump_json()) == manifest


def test_dataset_manifest_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["dataset_manifest"])
    data["integration_status"] = "approved"

    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(data)


def test_dataset_manifest_rejects_empty_variables(example_data, copy_data):
    data = copy_data(example_data["dataset_manifest"])
    data["variables"] = []

    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(data)


def test_dataset_manifest_rejects_missing_identifier(example_data, copy_data):
    data = copy_data(example_data["dataset_manifest"])
    del data["dataset_id"]

    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(data)
