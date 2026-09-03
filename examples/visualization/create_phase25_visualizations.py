"""Small deterministic Phase 25 visualization example."""

from pathlib import Path

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.statistics import StatisticalSpecification
from polaris.visualization import (
    OutputFormat,
    VisualizationSpecification,
    VisualizationType,
    create_visualization,
)


def main() -> None:
    data_path = Path("data/examples/world_bank_wdi_sample.csv")
    manifest = DatasetManifest.model_validate(
        {
            "dataset_id": "phase25_example_wdi",
            "title": "Phase 25 WDI Sample",
            "provider": "World Bank",
            "source_url": "https://example.test/phase25",
            "status": "candidate",
            "geographic_coverage": {"codes": ["USA", "CAN"]},
            "temporal_coverage": {"start": 2018, "end": 2021},
            "variables": [
                _variable("Country Code", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("Year", DataType.INTEGER, VariableRole.TIME),
                _variable("SP.DYN.LE00.IN", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("NY.GDP.PCAP.CD", DataType.FLOAT, VariableRole.PREDICTOR),
            ],
        }
    )
    ingestion = ingest_dataset(
        registry=DatasetRegistry((manifest,)),
        request=IngestionRequest(dataset_id=manifest.dataset_id, source_path=data_path),
    )
    analysis = run_analysis(
        request=AnalysisRequest(
            ingestion_result=ingestion,
            statistical_specification=StatisticalSpecification.model_validate(
                {
                    "specification_id": "phase25_example_scatter",
                    "investigation_id": "phase25_example",
                    "analysis_type": "regression",
                    "model_family": "linear",
                    "procedure": "ordinary_least_squares",
                    "outcome_variable": {"variable_id": "SP.DYN.LE00.IN"},
                    "exposure_variables": [{"variable_id": "NY.GDP.PCAP.CD"}],
                    "unit_of_analysis": "country-year",
                    "missing_data_strategy": {
                        "strategy": "complete_case",
                        "rationale": "example",
                    },
                    "confidence_level": 0.95,
                    "causal_identification_claim_level": "associational",
                }
            ),
        )
    )
    create_visualization(
        specification=VisualizationSpecification(
            visualization_type=VisualizationType.REGRESSION_RELATIONSHIP,
            source_artifact_id=analysis.result_id,
            x_variable="NY.GDP.PCAP.CD",
            y_variable="SP.DYN.LE00.IN",
            output_formats=(OutputFormat.PNG, OutputFormat.SVG, OutputFormat.CSV),
        ),
        source_artifact=analysis,
        data_artifact=ingestion,
        output_directory=Path("outputs/visualizations"),
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, str]:
    return {
        "variable_id": variable_id,
        "label": variable_id.replace("_", " ").title(),
        "data_type": data_type.value,
        "role": role.value,
    }


if __name__ == "__main__":
    main()
