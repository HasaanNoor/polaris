"""Reviewed WGI governance variable mappings."""

from __future__ import annotations

from polaris.wgi.models import WGIVariableMapping

_DEFINITIONS = {
    "VA": (
        "Captures perceptions of the extent to which citizens can participate in selecting "
        "their government, including electoral integrity, accountability mechanisms, access "
        "to information, oversight bodies, and traditional/digital media."
    ),
    "PV": (
        "Captures perceptions of the extent to which political power and governance are "
        "secure from destabilization, and the likelihood that authority will be challenged "
        "or altered through violent, coercive, or unconstitutional means."
    ),
    "GE": (
        "Captures perceptions of the quality of public services, the civil service, policy "
        "formulation and implementation, and the credibility of a government's decisions."
    ),
    "RQ": (
        "Captures perceptions of the government's ability to design and implement policies "
        "and regulations that promote private sector development."
    ),
    "RL": (
        "Captures perceptions of the extent to which agents respect and follow the rules of "
        "society, including contract enforcement, property rights, police, courts, and the "
        "likelihood of crime and violence."
    ),
    "CC": (
        "Captures perceptions of the extent to which public power is used for private gain, "
        "including petty and grand corruption, and capture of the state by elites and private "
        "interests."
    ),
}

_CANONICAL = (
    ("VA", "wgi_voice_accountability", "Voice and Accountability"),
    ("PV", "wgi_political_stability", "Political Stability and Absence of Violence/Terrorism"),
    ("GE", "wgi_government_effectiveness", "Government Effectiveness"),
    ("RQ", "wgi_regulatory_quality", "Regulatory Quality"),
    ("RL", "wgi_rule_of_law", "Rule of Law"),
    ("CC", "wgi_control_corruption", "Control of Corruption"),
)


def wgi_mapping_registry() -> tuple[WGIVariableMapping, ...]:
    """Return reviewed mappings for the six WGI governance dimensions."""

    mappings = []
    for code, variable_id, label in _CANONICAL:
        prefix = f"GOV_WGI_{code}"
        mappings.append(
            WGIVariableMapping(
                canonical_variable_id=variable_id,
                canonical_label=label,
                official_dimension_code=code,
                official_estimate_indicator_id=f"{prefix}.EST",
                official_title=f"{label} - Governance estimate (approx. -2.5 to +2.5)",
                definition=_DEFINITIONS[code],
                estimate_unit="standard normal governance estimate",
                estimate_scale=(
                    "approximately -2.5 to +2.5; higher values indicate better governance"
                ),
                standard_error_indicator_id=f"{prefix}.SE",
                source_count_indicator_id=f"{prefix}.SR",
                governance_score_indicator_id=f"{prefix}.SC",
                score_lower_bound_indicator_id=f"{prefix}.SC_LB",
                score_upper_bound_indicator_id=f"{prefix}.SC_UB",
            )
        )
    return tuple(mappings)


def mapping_by_indicator_id() -> dict[str, WGIVariableMapping]:
    """Map every WGI companion indicator ID to its canonical variable."""

    output: dict[str, WGIVariableMapping] = {}
    for mapping in wgi_mapping_registry():
        for indicator_id in (
            mapping.official_estimate_indicator_id,
            mapping.standard_error_indicator_id,
            mapping.source_count_indicator_id,
            mapping.governance_score_indicator_id,
            mapping.score_lower_bound_indicator_id,
            mapping.score_upper_bound_indicator_id,
        ):
            output[indicator_id] = mapping
    return output


def wgi_indicator_ids() -> tuple[str, ...]:
    """Return all WGI indicator IDs needed for estimates and uncertainty metadata."""

    ids = []
    for mapping in wgi_mapping_registry():
        ids.extend(
            [
                mapping.official_estimate_indicator_id,
                mapping.standard_error_indicator_id,
                mapping.source_count_indicator_id,
                mapping.governance_score_indicator_id,
                mapping.score_lower_bound_indicator_id,
                mapping.score_upper_bound_indicator_id,
            ]
        )
    return tuple(ids)
