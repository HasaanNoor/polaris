import pytest
from pydantic import ValidationError

from polaris.harmonization import HarmonizationRequest, JoinType
from polaris.harmonization.provenance import deterministic_harmonized_dataset_id
from tests.harmonization.helpers import request_for, wdi_result, who_result


def test_request_is_frozen_and_rejects_unknown_fields(tmp_path) -> None:
    request = request_for(wdi_result(tmp_path), who_result(tmp_path))

    with pytest.raises(ValidationError):
        request.join_type = JoinType.INNER  # type: ignore[misc]
    with pytest.raises(ValidationError):
        HarmonizationRequest.model_validate({**request.model_dump(), "unknown": True})


def test_left_join_requires_anchor(tmp_path) -> None:
    request = request_for(wdi_result(tmp_path), who_result(tmp_path))
    payload = request.model_dump()
    payload["anchor_dataset_id"] = None

    with pytest.raises(ValidationError):
        HarmonizationRequest.model_validate(payload)


def test_deterministic_id_is_stable(tmp_path) -> None:
    request = request_for(wdi_result(tmp_path), who_result(tmp_path))

    assert deterministic_harmonized_dataset_id(request) == deterministic_harmonized_dataset_id(
        request
    )
