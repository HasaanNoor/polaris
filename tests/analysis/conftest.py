from pathlib import Path
from typing import Any

import pytest

from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest


@pytest.fixture
def analysis_manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "analysis_dataset",
            "title": "Analysis Dataset",
            "provider": "Test Provider",
            "source_url": "https://example.test/analysis",
            "status": "candidate",
            "geographic_coverage": {"codes": ["TEST"]},
            "temporal_coverage": {"start": 2020, "end": 2021},
            "variables": [
                _variable("row_id", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("y", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("x", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("z", DataType.FLOAT, VariableRole.COVARIATE),
                _variable("x_duplicate", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("constant", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("category", DataType.CATEGORICAL, VariableRole.GROUPING),
                _variable("flag", DataType.BOOLEAN, VariableRole.QUALITY_FLAG),
            ],
        }
    )


@pytest.fixture
def analysis_ingestion(tmp_path: Path, analysis_manifest: DatasetManifest):
    path = tmp_path / "analysis.csv"
    path.write_text(
        "\n".join(
            [
                "row_id,y,x,z,x_duplicate,constant,category,flag",
                "a,3,1,10,1,5,A,true",
                "b,5,2,20,2,5,A,false",
                "c,7,3,30,3,5,B,true",
                "d,9,4,40,4,5,B,false",
                "e,11,5,50,5,5,B,true",
                "f,,6,60,6,5,C,false",
                "g,15,7,,7,5,C,true",
                "h,17,8,80,8,5,C,false",
                "i,19,9,90,9,5,D,true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry = DatasetRegistry((analysis_manifest,))
    return ingest_dataset(
        registry=registry,
        request=IngestionRequest(dataset_id="analysis_dataset", source_path=path),
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "label": variable_id,
        "data_type": data_type,
        "role": role,
    }
