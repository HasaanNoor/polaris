"""WHO Global Health Observatory provider metadata."""

from polaris.providers._static import StaticFileProvider
from polaris.providers.base import ProviderDataset, ProviderMetadata, provider_variable
from polaris.schemas.common import DataType, GeographicScope, TemporalScope, VariableRole


def build_provider() -> StaticFileProvider:
    return StaticFileProvider(
        metadata=ProviderMetadata(
            provider_id="who",
            name="World Health Organization",
            homepage_url="https://www.who.int/data/gho",
            description="Official WHO Global Health Observatory public data provider.",
            license="WHO data terms and conditions",
            citation="World Health Organization, Global Health Observatory.",
            supported_formats=(".csv",),
        ),
        datasets=(
            ProviderDataset(
                dataset_id="GHO",
                title="Global Health Observatory",
                source_url="https://www.who.int/data/gho",
                description=(
                    "WHO Global Health Observatory snapshot acquired from the selected "
                    "provider download."
                ),
                license="WHO data terms and conditions",
                citation="World Health Organization, Global Health Observatory.",
                geographic_coverage=GeographicScope(
                    codes=["GLOBAL_HEALTH"],
                    description="Global health indicator coverage as published by WHO.",
                ),
                temporal_coverage=TemporalScope(start=2000, end=None, label="Annual series"),
                variables=(
                    provider_variable(
                        "location",
                        "Location",
                        DataType.STRING,
                        VariableRole.IDENTIFIER,
                        source_field_name="Location",
                    ),
                    provider_variable(
                        "period",
                        "Period",
                        DataType.INTEGER,
                        VariableRole.TIME,
                        source_field_name="Period",
                    ),
                    provider_variable(
                        "maternal_mortality_ratio",
                        "Maternal mortality ratio",
                        DataType.FLOAT,
                        VariableRole.OUTCOME,
                        source_field_name="MDG_0000000026",
                        unit="deaths per 100,000 live births",
                        missing=("null", "NA", "N/A", "not_available"),
                    ),
                    provider_variable(
                        "life_expectancy_at_birth",
                        "Life expectancy at birth",
                        DataType.FLOAT,
                        VariableRole.OUTCOME,
                        source_field_name="WHOSIS_000001",
                        unit="years",
                    ),
                ),
                units=("country-year",),
                frequency="annual",
                format=".csv",
                methodology_reference="https://www.who.int/data/gho/indicator-metadata-registry",
            ),
        ),
    )
