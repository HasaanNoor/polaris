"""UNESCO Institute for Statistics provider metadata."""

from polaris.providers._static import StaticFileProvider
from polaris.providers.base import ProviderDataset, ProviderMetadata, provider_variable
from polaris.schemas.common import DataType, GeographicScope, TemporalScope, VariableRole


def build_provider() -> StaticFileProvider:
    return StaticFileProvider(
        metadata=ProviderMetadata(
            provider_id="unesco",
            name="UNESCO Institute for Statistics",
            homepage_url="https://uis.unesco.org/",
            description="Official UNESCO Institute for Statistics public data provider.",
            license="UNESCO UIS data terms",
            citation="UNESCO Institute for Statistics.",
            supported_formats=(".csv",),
        ),
        datasets=(
            ProviderDataset(
                dataset_id="UIS",
                title="UNESCO Institute for Statistics",
                source_url="https://uis.unesco.org/",
                description=(
                    "Education indicator snapshot acquired from a UNESCO Institute for "
                    "Statistics provider download."
                ),
                license="UNESCO UIS data terms",
                citation="UNESCO Institute for Statistics.",
                geographic_coverage=GeographicScope(
                    codes=["EDUCATION_GLOBAL"],
                    description="Global education coverage as published by UNESCO UIS.",
                ),
                temporal_coverage=TemporalScope(start=1970, end=None, label="Annual series"),
                variables=(
                    provider_variable(
                        "reference_area",
                        "Reference area",
                        DataType.STRING,
                        VariableRole.IDENTIFIER,
                        source_field_name="REF_AREA",
                    ),
                    provider_variable(
                        "time_period",
                        "Time period",
                        DataType.INTEGER,
                        VariableRole.TIME,
                        source_field_name="TIME_PERIOD",
                    ),
                    provider_variable(
                        "secondary_school_enrollment",
                        "Secondary school enrollment",
                        DataType.FLOAT,
                        VariableRole.OUTCOME,
                        source_field_name="EDULIT_DS",
                        unit="percent",
                        missing=("null", "NA", "N/A", ".."),
                    ),
                    provider_variable(
                        "education_expenditure_percent_gdp",
                        "Education expenditure as percent of GDP",
                        DataType.FLOAT,
                        VariableRole.PREDICTOR,
                        source_field_name="FINANCE_GDP",
                        unit="percent",
                        missing=("null", "NA", "N/A", ".."),
                    ),
                ),
                units=("country-year",),
                frequency="annual",
                format=".csv",
            ),
        ),
    )
