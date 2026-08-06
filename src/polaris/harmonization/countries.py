"""Deterministic country identifier normalization for harmonization."""

from __future__ import annotations

from polaris.harmonization.models import GeographicEntityType, NormalizedCountry

ISO2_TO_ISO3 = {
    "PK": ("PAK", "Pakistan"),
    "US": ("USA", "United States"),
    "GB": ("GBR", "United Kingdom"),
    "AF": ("AFG", "Afghanistan"),
    "AL": ("ALB", "Albania"),
    "CN": ("CHN", "China"),
    "IN": ("IND", "India"),
}

CANONICAL_NAME_TO_ISO3 = {
    "pakistan": ("PAK", "Pakistan"),
    "united states": ("USA", "United States"),
    "united kingdom": ("GBR", "United Kingdom"),
    "afghanistan": ("AFG", "Afghanistan"),
    "albania": ("ALB", "Albania"),
    "china": ("CHN", "China"),
    "india": ("IND", "India"),
}

TERRITORY_CODES = {
    "ABW": "Aruba",
    "ASM": "American Samoa",
    "BMU": "Bermuda",
    "CYM": "Cayman Islands",
    "GIB": "Gibraltar",
    "GRL": "Greenland",
    "GUM": "Guam",
    "HKG": "Hong Kong SAR, China",
    "MAC": "Macao SAR, China",
    "PRI": "Puerto Rico",
    "VIR": "Virgin Islands (U.S.)",
}

REGION_CODES = {
    "AFE": "Africa Eastern and Southern",
    "AFW": "Africa Western and Central",
    "ARB": "Arab World",
    "CEB": "Central Europe and the Baltics",
    "CSS": "Caribbean small states",
    "EAP": "East Asia & Pacific",
    "EAR": "Early-demographic dividend",
    "EAS": "East Asia & Pacific",
    "ECA": "Europe & Central Asia",
    "ECS": "Europe & Central Asia",
    "EMU": "Euro area",
    "EUU": "European Union",
    "FCS": "Fragile and conflict affected situations",
    "HPC": "Heavily indebted poor countries (HIPC)",
    "IBD": "IBRD only",
    "IBT": "IDA & IBRD total",
    "IDA": "IDA total",
    "IDB": "IDA blend",
    "IDX": "IDA only",
    "LAC": "Latin America & Caribbean",
    "LCN": "Latin America & Caribbean",
    "LDC": "Least developed countries",
    "LTE": "Late-demographic dividend",
    "MEA": "Middle East & North Africa",
    "MIC": "Middle income",
    "MNA": "Middle East & North Africa",
    "NAC": "North America",
    "OED": "OECD members",
    "OSS": "Other small states",
    "PRE": "Pre-demographic dividend",
    "PSS": "Pacific island small states",
    "PST": "Post-demographic dividend",
    "SAS": "South Asia",
    "SSA": "Sub-Saharan Africa",
    "SSF": "Sub-Saharan Africa",
    "SST": "Small states",
    "TEA": "East Asia & Pacific",
    "TEC": "Europe & Central Asia",
    "TLA": "Latin America & Caribbean",
    "TMN": "Middle East & North Africa",
    "TSA": "South Asia",
    "TSS": "Sub-Saharan Africa",
}

INCOME_GROUP_CODES = {
    "HIC": "High income",
    "INX": "Not classified",
    "LIC": "Low income",
    "LMC": "Lower middle income",
    "LMY": "Low & middle income",
    "MIC": "Middle income",
    "UMC": "Upper middle income",
}

GLOBAL_CODES = {"WLD": "World", "GLOBAL": "Global"}


def normalize_country_identifier(
    value: object,
    *,
    provider: str | None = None,
    source_name: object | None = None,
) -> NormalizedCountry:
    """Normalize documented exact country identifiers without fuzzy matching."""

    raw = "" if value is None else str(value).strip()
    name = "" if source_name is None else str(source_name).strip()
    if not raw:
        return NormalizedCountry(
            source_value=raw,
            provider=provider,
            finding="empty geographic identifier",
        )
    upper = raw.upper()
    if upper in GLOBAL_CODES:
        return NormalizedCountry(
            source_value=raw,
            canonical_code=upper,
            canonical_name=GLOBAL_CODES[upper],
            entity_type=GeographicEntityType.GLOBAL_AGGREGATE,
            provider=provider,
        )
    if upper in INCOME_GROUP_CODES:
        return NormalizedCountry(
            source_value=raw,
            canonical_code=upper,
            canonical_name=INCOME_GROUP_CODES[upper],
            entity_type=GeographicEntityType.INCOME_GROUP,
            provider=provider,
        )
    if upper in REGION_CODES:
        return NormalizedCountry(
            source_value=raw,
            canonical_code=upper,
            canonical_name=REGION_CODES[upper],
            entity_type=GeographicEntityType.REGION,
            provider=provider,
        )
    if upper in TERRITORY_CODES:
        return NormalizedCountry(
            source_value=raw,
            canonical_code=upper,
            canonical_name=name or TERRITORY_CODES[upper],
            entity_type=GeographicEntityType.TERRITORY,
            provider=provider,
        )
    if upper in ISO2_TO_ISO3:
        code, canonical = ISO2_TO_ISO3[upper]
        return NormalizedCountry(
            source_value=raw,
            canonical_code=code,
            canonical_name=name or canonical,
            entity_type=GeographicEntityType.SOVEREIGN_COUNTRY,
            provider=provider,
        )
    if raw == upper and len(upper) == 3 and upper.isalpha():
        return NormalizedCountry(
            source_value=raw,
            canonical_code=upper,
            canonical_name=name or upper,
            entity_type=GeographicEntityType.SOVEREIGN_COUNTRY,
            provider=provider,
        )
    by_name = CANONICAL_NAME_TO_ISO3.get(raw.casefold())
    if by_name is not None:
        code, canonical = by_name
        return NormalizedCountry(
            source_value=raw,
            canonical_code=code,
            canonical_name=canonical,
            entity_type=GeographicEntityType.SOVEREIGN_COUNTRY,
            provider=provider,
        )
    return NormalizedCountry(
        source_value=raw,
        canonical_name=name or raw,
        entity_type=GeographicEntityType.UNKNOWN,
        provider=provider,
        finding="no reviewed exact mapping",
    )
