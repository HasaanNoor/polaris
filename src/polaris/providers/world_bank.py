"""World Bank World Development Indicators provider metadata."""

from polaris.providers._static import StaticFileProvider
from polaris.providers.base import ProviderDataset, ProviderMetadata, provider_variable
from polaris.schemas.common import DataType, GeographicScope, TemporalScope, VariableRole


def build_provider() -> StaticFileProvider:
    return StaticFileProvider(
        metadata=ProviderMetadata(
            provider_id="world_bank",
            name="World Bank",
            homepage_url="https://databank.worldbank.org/source/world-development-indicators",
            description="Official World Bank World Development Indicators public data provider.",
            license="World Bank Open Data Terms of Use",
            citation="World Bank, World Development Indicators.",
            supported_formats=(".csv",),
        ),
        datasets=(
            ProviderDataset(
                dataset_id="WDI",
                title="World Development Indicators",
                source_url="https://databank.worldbank.org/source/world-development-indicators",
                description=(
                    "Country-level World Development Indicators snapshot acquired from the "
                    "World Bank source selected by the caller."
                ),
                license="World Bank Open Data Terms of Use",
                citation="World Bank, World Development Indicators.",
                geographic_coverage=GeographicScope(
                    codes=["GLOBAL"],
                    description=(
                        "Global country and economy coverage as published by the World Bank."
                    ),
                ),
                temporal_coverage=TemporalScope(start=1960, end=None, label="Annual series"),
                variables=(
                    provider_variable(
                        "country_code",
                        "Country code",
                        DataType.STRING,
                        VariableRole.IDENTIFIER,
                        source_field_name="Country Code",
                    ),
                    provider_variable(
                        "year",
                        "Year",
                        DataType.INTEGER,
                        VariableRole.TIME,
                        source_field_name="Year",
                    ),
                    provider_variable(
                        "life_expectancy_at_birth",
                        "Life expectancy at birth",
                        DataType.FLOAT,
                        VariableRole.OUTCOME,
                        source_field_name="SP.DYN.LE00.IN",
                        unit="years",
                    ),
                    provider_variable(
                        "gdp_per_capita_current_usd",
                        "GDP per capita, current US dollars",
                        DataType.FLOAT,
                        VariableRole.PREDICTOR,
                        source_field_name="NY.GDP.PCAP.CD",
                        unit="current US dollars",
                    ),
                    provider_variable(
                        "secondary_school_enrollment",
                        "Secondary school enrollment",
                        DataType.FLOAT,
                        VariableRole.EXPOSURE,
                        source_field_name="SE.SEC.ENRR",
                        unit="percent",
                    ),
                ),
                units=("country-year",),
                frequency="annual",
                format=".csv",
                methodology_reference=(
                    "https://databank.worldbank.org/metadataglossary/world-development-indicators"
                ),
            ),
        ),
    )
