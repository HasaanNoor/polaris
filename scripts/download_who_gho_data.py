#!/usr/bin/env python3
"""Acquire a curated WHO GHO OData snapshot collection.

This script is intentionally standalone. It downloads raw WHO provider JSON
responses and writes a metadata catalog for later Polaris integration review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://ghoapi.azureedge.net/api"
RAW_ROOT = Path("data/raw/who/gho")
CATALOG_PATH = RAW_ROOT / "acquisition_catalog.json"
USER_AGENT = "Polaris WHO GHO acquisition/1.0"


TARGETS: list[dict[str, Any]] = [
    {
        "number": 1,
        "key": "life_expectancy_at_birth",
        "category": "longevity_mortality",
        "concept": "Life expectancy at birth",
        "indicator_id": "WHOSIS_000001",
        "rationale": "Broad overall population-health status.",
        "reason_selected": "Direct WHO GHO headline life expectancy-at-birth series.",
        "alternatives": ["WHOSIS_000015: Life expectancy at age 60 (not birth)."],
    },
    {
        "number": 2,
        "key": "healthy_life_expectancy_at_birth",
        "category": "longevity_mortality",
        "concept": "Healthy life expectancy (HALE) at birth",
        "indicator_id": "WHOSIS_000002",
        "rationale": "Separates total longevity from years lived in good health.",
        "reason_selected": "Direct HALE-at-birth series.",
        "alternatives": ["WHOSIS_000007: HALE at age 60 (not birth)."],
    },
    {
        "number": 3,
        "key": "adult_mortality",
        "category": "longevity_mortality",
        "concept": "Adult mortality",
        "indicator_id": "WHOSIS_000004",
        "rationale": "Captures mortality outside childhood.",
        "reason_selected": "Only exact adult mortality match in the official index.",
        "alternatives": [],
    },
    {
        "number": 4,
        "key": "under_five_mortality",
        "category": "longevity_mortality",
        "concept": "Under-five mortality",
        "indicator_id": "MDG_0000000007",
        "rationale": "Child survival and broader development conditions.",
        "reason_selected": "WHO GHO under-five mortality probability series with country-year observations; the current concise u5mr label returned no observations from the data endpoint.",
        "alternatives": [
            "u5mr: exact current concise title but OData data endpoint returned no observations."
        ],
        "data_filter": "SpatialDimType eq 'COUNTRY' and Dim1 eq 'SEX_BTSX' and Dim2 eq 'AGEGROUP_YEARSUNDER5' and Dim3 eq 'WEALTHQUINTILE_TOTL'",
    },
    {
        "number": 5,
        "key": "neonatal_mortality",
        "category": "longevity_mortality",
        "concept": "Neonatal mortality",
        "indicator_id": "WHOSIS_000003",
        "rationale": "Isolates first 28 days and maternal/newborn health-system performance.",
        "reason_selected": "WHO GHO neonatal mortality series with country-year observations; the current concise nmr label returned no observations from the data endpoint.",
        "alternatives": ["nmr: exact current concise title but OData data endpoint returned no observations."],
        "data_filter": "SpatialDimType eq 'COUNTRY' and Dim1 eq 'SEX_BTSX' and Dim2 eq 'AGEGROUP_DAYS0-27'",
    },
    {
        "number": 6,
        "key": "maternal_mortality_ratio",
        "category": "longevity_mortality",
        "concept": "Maternal mortality ratio",
        "indicator_id": "MDG_0000000026",
        "rationale": "Reproductive and maternal-care outcome.",
        "reason_selected": "Modeled/global-comparable MMR series rather than country-reported-only estimates.",
        "alternatives": [
            "MDG_0000000032: country reported estimates; less comparable."
        ],
    },
    {
        "number": 7,
        "key": "suicide_mortality_rate",
        "category": "longevity_mortality",
        "concept": "Suicide mortality rate",
        "indicator_id": "MH_12",
        "rationale": "Globally comparable mental-health outcome.",
        "reason_selected": "Age-standardized suicide-rate series.",
        "alternatives": ["SDGSUICIDE: crude suicide rates."],
    },
    {
        "number": 8,
        "key": "current_health_expenditure_gdp",
        "category": "health_systems",
        "concept": "Current health expenditure as % of GDP",
        "indicator_id": "GHED_CHEGDP_SHA2011",
        "rationale": "National commitment relative to economic output.",
        "reason_selected": "Direct GHED CHE share-of-GDP indicator.",
        "alternatives": [],
    },
    {
        "number": 9,
        "key": "current_health_expenditure_per_capita",
        "category": "health_systems",
        "concept": "Current health expenditure per capita",
        "indicator_id": "GHED_CHE_pc_US_SHA2011",
        "rationale": "Health spending available per person.",
        "reason_selected": "Direct current-health-expenditure per-capita series with country-year observations; the PPP variant returned no observations from the data endpoint.",
        "alternatives": ["GHED_CHE_pc_PPP_SHA2011: PPP int$ per capita but OData data endpoint returned no observations."],
        "warnings": ["US-dollar values may require later price/exchange-rate handling."],
        "data_filter": "SpatialDimType eq 'COUNTRY'",
    },
    {
        "number": 10,
        "key": "medical_doctor_density",
        "category": "health_systems",
        "concept": "Physician / medical doctor density",
        "indicator_id": "HWF_0001",
        "rationale": "Medical workforce capacity.",
        "reason_selected": "Direct medical-doctor density per 10,000 population.",
        "alternatives": ["HWF_0002: medical doctors number."],
    },
    {
        "number": 11,
        "key": "nurse_midwife_density",
        "category": "health_systems",
        "concept": "Nurse and midwife density",
        "indicator_id": "HWF_0006",
        "rationale": "Nursing and midwifery workforce capacity.",
        "reason_selected": "Current nursing and midwifery personnel density per 10,000 population.",
        "alternatives": ["WHS6_148: older equivalent density label."],
    },
    {
        "number": 12,
        "key": "hospital_bed_density",
        "category": "health_systems",
        "concept": "Hospital bed density",
        "indicator_id": "WHS6_102",
        "rationale": "Infrastructure capacity.",
        "reason_selected": "Direct hospital beds per 10,000 population series.",
        "alternatives": [],
    },
    {
        "number": 13,
        "key": "uhc_service_coverage_index",
        "category": "health_systems",
        "concept": "Universal Health Coverage service coverage index",
        "indicator_id": "UHC_INDEX_REPORTED",
        "rationale": "Service coverage.",
        "reason_selected": "WHO's reported SDG 3.8.1 UHC Service Coverage Index.",
        "alternatives": ["UHC_INDEX_ACTUAL: actual index values; reported SDG series preferred."],
    },
    {
        "number": 14,
        "key": "catastrophic_health_expenditure",
        "category": "health_systems",
        "concept": "Catastrophic health expenditure / financial hardship from healthcare",
        "indicator_id": "FINPROTECTION_CATA_TOT_10_LEVEL_SH",
        "rationale": "Healthcare affordability and financial protection.",
        "reason_selected": "Estimated SDG 3.8.2 population share above 10% household-budget threshold.",
        "alternatives": [
            "FINPROTECTION_CATA_TOT_10_POP: reported data.",
            "FINPROTECTION_CATA_TOT_25_LEVEL_SH: stricter 25% threshold.",
        ],
    },
    {
        "number": 15,
        "key": "dtp3_immunization",
        "category": "immunization",
        "concept": "DTP3 immunization coverage",
        "indicator_id": "WHS4_100",
        "rationale": "Routine immunization-system performance.",
        "reason_selected": "WHO/UNICEF WUENIC DTP3 coverage among one-year-olds.",
        "alternatives": ["dptv: concise DTP3 coverage label."],
    },
    {
        "number": 16,
        "key": "measles_immunization",
        "category": "immunization",
        "concept": "Measles immunization coverage",
        "indicator_id": "WHS8_110",
        "rationale": "Second core vaccination-coverage indicator.",
        "reason_selected": "WHO/UNICEF WUENIC first-dose measles-containing vaccine coverage.",
        "alternatives": ["mslv: concise measles coverage label.", "MCV2: second-dose coverage."],
    },
    {
        "number": 17,
        "key": "child_stunting_prevalence",
        "category": "nutrition",
        "concept": "Child stunting prevalence",
        "indicator_id": "NUTSTUNTINGPREV",
        "rationale": "Chronic or recurrent undernutrition.",
        "reason_selected": "Model-based under-5 stunting prevalence for broad comparability.",
        "alternatives": ["NUTRITION_ANT_HAZ_NE2: survey-based estimates."],
    },
    {
        "number": 18,
        "key": "child_wasting_prevalence",
        "category": "nutrition",
        "concept": "Child wasting prevalence",
        "indicator_id": "NUTWASTINGPREV",
        "rationale": "Acute or recent undernutrition.",
        "reason_selected": "Model-based under-5 wasting prevalence for broad comparability.",
        "alternatives": ["NUTRITION_WH_2: survey-based estimates."],
    },
    {
        "number": 19,
        "key": "child_overweight_prevalence",
        "category": "nutrition",
        "concept": "Child overweight prevalence",
        "indicator_id": "NUTOVERWEIGHTPREV",
        "rationale": "Child nutrition burden beyond undernutrition.",
        "reason_selected": "Model-based under-5 overweight prevalence.",
        "alternatives": ["NUTRITION_ANT_WHZ_NE2: survey-based estimates."],
    },
    {
        "number": 20,
        "key": "anaemia_prevalence",
        "category": "nutrition",
        "concept": "Anaemia prevalence",
        "indicator_id": "NUTRITION_ANAEMIA_REPRODUCTIVEAGE_PREV",
        "rationale": "Nutrition and reproductive-age health burden.",
        "reason_selected": "Broad headline anaemia prevalence in women aged 15-49.",
        "alternatives": [
            "NUTRITION_ANAEMIA_CHILDREN_PREV: child-specific.",
            "NUTRITION_ANAEMIA_PREGNANT_PREV: pregnancy-specific.",
        ],
    },
    {
        "number": 21,
        "key": "exclusive_breastfeeding",
        "category": "nutrition",
        "concept": "Exclusive breastfeeding prevalence",
        "indicator_id": "NUT_BF_EBF",
        "rationale": "Infant feeding and early-life nutrition practice.",
        "reason_selected": "Direct exclusive breastfeeding under-six-months series.",
        "alternatives": ["NUTRITION_579: older exact label."],
    },
    {
        "number": 22,
        "key": "premature_ncd_mortality",
        "category": "ncd_risk",
        "concept": "Premature mortality from major NCDs",
        "indicator_id": "NCDMORT3070",
        "rationale": "Combined major NCD outcome.",
        "reason_selected": "Direct combined 30-70 mortality probability for cardiovascular disease, cancer, diabetes, and chronic respiratory disease.",
        "alternatives": ["Separate cardiovascular/cancer/respiratory mortality series avoided as redundant."],
    },
    {
        "number": 23,
        "key": "hypertension_prevalence",
        "category": "ncd_risk",
        "concept": "Hypertension prevalence",
        "indicator_id": "NCD_HYP_PREVALENCE_A",
        "rationale": "Major modifiable NCD risk factor.",
        "reason_selected": "Age-standardized prevalence among adults aged 30-79.",
        "alternatives": ["NCD_HYP_PREVALENCE_C: crude prevalence."],
    },
    {
        "number": 24,
        "key": "diabetes_prevalence",
        "category": "ncd_risk",
        "concept": "Diabetes prevalence",
        "indicator_id": "NCD_DIABETES_PREVALENCE_AGESTD",
        "rationale": "Major NCD burden and risk marker.",
        "reason_selected": "Age-standardized prevalence of diabetes.",
        "alternatives": ["NCD_DIABETES_PREVALENCE_CRUDE: crude prevalence."],
    },
    {
        "number": 25,
        "key": "obesity_prevalence",
        "category": "ncd_risk",
        "concept": "Obesity prevalence",
        "indicator_id": "NCD_BMI_30A",
        "rationale": "Major metabolic risk factor.",
        "reason_selected": "Age-standardized adult obesity prevalence.",
        "alternatives": ["NCD_BMI_30C: crude adult obesity prevalence."],
    },
    {
        "number": 26,
        "key": "tobacco_use_prevalence",
        "category": "ncd_risk",
        "concept": "Tobacco use prevalence",
        "indicator_id": "M_Est_tob_curr_std",
        "rationale": "Modifiable behavioral risk factor.",
        "reason_selected": "Age-standardized estimate of current tobacco-use prevalence, broader than smoking only.",
        "alternatives": ["SDGTOBACCO: current tobacco smoking, not all tobacco use."],
    },
    {
        "number": 27,
        "key": "insufficient_physical_activity",
        "category": "ncd_risk",
        "concept": "Insufficient physical activity",
        "indicator_id": "NCD_PAA",
        "rationale": "Modifiable behavioral risk factor.",
        "reason_selected": "Age-standardized adult insufficient-physical-activity prevalence.",
        "alternatives": ["NCD_PAC: crude estimate."],
    },
    {
        "number": 28,
        "key": "alcohol_consumption",
        "category": "ncd_risk",
        "concept": "Alcohol consumption or harmful alcohol use",
        "indicator_id": "SA_0000001688",
        "rationale": "Modifiable behavioral risk factor.",
        "reason_selected": "SDG 3.5.2 total alcohol per-capita consumption, three-year average.",
        "alternatives": ["SA_0000001749: same construct with 95% CI."],
    },
    {
        "number": 29,
        "key": "tuberculosis_incidence",
        "category": "communicable",
        "concept": "Tuberculosis incidence",
        "indicator_id": "MDG_0000000020",
        "rationale": "Communicable-disease burden.",
        "reason_selected": "Incidence of tuberculosis per 100,000 population per year.",
        "alternatives": ["TB_e_inc_num: incident case counts, not rate."],
    },
    {
        "number": 30,
        "key": "malaria_incidence",
        "category": "communicable",
        "concept": "Malaria incidence",
        "indicator_id": "MALARIA_EST_INCIDENCE",
        "rationale": "Communicable-disease burden.",
        "reason_selected": "Estimated malaria incidence series with country-year observations; the SDGMALARIA data endpoint returned no observations.",
        "alternatives": ["SDGMALARIA: SDG malaria incidence title but OData data endpoint returned no observations."],
        "warnings": ["Estimated incidence; do not equate with reported case incidence without review."],
        "data_filter": "SpatialDimType eq 'COUNTRY'",
    },
    {
        "number": 31,
        "key": "hiv_incidence_or_prevalence",
        "category": "communicable",
        "concept": "HIV incidence or prevalence",
        "indicator_id": "HIV_0000000026",
        "rationale": "Communicable-disease burden.",
        "reason_selected": "Official GHO number of new HIV infections; no rate/prevalence-per-population series was found in the GHO indicator index.",
        "alternatives": ["HIV_0000000001: estimated number of people living with HIV."],
        "warnings": ["This is a count of new infections, not an incidence rate."],
    },
    {
        "number": 32,
        "key": "hepatitis_b_prevalence",
        "category": "communicable",
        "concept": "Hepatitis B incidence or prevalence",
        "indicator_id": "SDGHEPHBSAGPRV",
        "rationale": "Communicable-disease burden where sufficiently comparable.",
        "reason_selected": "SDG hepatitis B surface antigen prevalence.",
        "alternatives": ["HEPATITIS_HBV_PREVALENCE_PER100: chronic HBV prevalence in general population."],
    },
    {
        "number": 33,
        "key": "adolescent_birth_rate",
        "category": "reproductive",
        "concept": "Adolescent birth rate",
        "indicator_id": "MDG_0000000003",
        "rationale": "Reproductive and social outcome.",
        "reason_selected": "Only exact adolescent birth-rate match in the official index.",
        "alternatives": [],
    },
    {
        "number": 34,
        "key": "skilled_birth_attendance",
        "category": "reproductive",
        "concept": "Births attended by skilled health personnel",
        "indicator_id": "MDG_0000000025",
        "rationale": "Delivery-care access.",
        "reason_selected": "General skilled-birth-attendance percentage, not adolescent-only or survey-window shorthand.",
        "alternatives": ["sba: two/three-year survey-window shorthand.", "sba5: five-year survey-window shorthand."],
    },
    {
        "number": 35,
        "key": "antenatal_care_coverage",
        "category": "reproductive",
        "concept": "Antenatal-care coverage",
        "indicator_id": "WHS4_154",
        "rationale": "Prenatal-care access.",
        "reason_selected": "At-least-four-visits antenatal-care coverage, a stricter access/completion measure than one visit.",
        "alternatives": ["WHS4_111: at least one visit."],
    },
    {
        "number": 36,
        "key": "family_planning_modern_methods",
        "category": "reproductive",
        "concept": "Modern contraceptive / family-planning coverage",
        "indicator_id": "SDGFPALL",
        "rationale": "Contraceptive access.",
        "reason_selected": "SDG need for family planning satisfied with modern methods.",
        "alternatives": ["FAMILYPLANNINGUNPDUHC: modelled estimates variant.", "cpmo: contraceptive prevalence - modern methods."],
    },
    {
        "number": 37,
        "key": "unmet_need_family_planning",
        "category": "reproductive",
        "concept": "Unmet need for family planning",
        "indicator_id": None,
        "rationale": "Unmet service demand.",
        "reason_selected": "Deferred: no general-population unmet-need series was found in the current GHO indicator index.",
        "alternatives": ["MDG_0000000006_AGE1519: adolescent-only unmet need; not selected."],
        "warnings": ["Deferred rather than substituting adolescent-only unmet need for the requested general concept."],
    },
    {
        "number": 38,
        "key": "mental_health_workforce_density",
        "category": "mental_health",
        "concept": "Mental-health workforce density",
        "indicator_id": "MH_6",
        "rationale": "Mental-health system capacity.",
        "reason_selected": "Psychiatrist density selected as a working mental-health workforce capacity proxy; the broader total workforce series returned no observations.",
        "alternatives": ["MH_21: broad total workforce but OData data endpoint returned no observations.", "MH_7: mental-health nurses.", "MH_9: psychologists."],
        "warnings": ["Narrower than total mental-health workforce; likely requires special handling."],
        "data_filter": "SpatialDimType eq 'COUNTRY'",
    },
    {
        "number": 39,
        "key": "safely_managed_drinking_water",
        "category": "environment",
        "concept": "Safely managed drinking-water services",
        "indicator_id": "WSH_WATER_SAFELY_MANAGED",
        "rationale": "Basic living conditions and infrastructure.",
        "reason_selected": "Direct safely managed drinking-water services percentage.",
        "alternatives": ["WSH_WATER_BASIC: at least basic drinking-water services."],
    },
    {
        "number": 40,
        "key": "safely_managed_sanitation",
        "category": "environment",
        "concept": "Safely managed sanitation services",
        "indicator_id": "WSH_SANITATION_SAFELY_MANAGED",
        "rationale": "Basic living conditions and infrastructure.",
        "reason_selected": "Direct safely managed sanitation services percentage.",
        "alternatives": ["WSH_SANITATION_BASIC: at least basic sanitation services."],
    },
    {
        "number": 41,
        "key": "ambient_air_pollution_exposure",
        "category": "environment",
        "concept": "Ambient air-pollution exposure or attributable mortality",
        "indicator_id": "SDGPM25",
        "rationale": "Environmental exposure relevant to health and development.",
        "reason_selected": "Exposure/concentration measure: fine particulate matter PM2.5.",
        "alternatives": ["AIR_50: attributable mortality rate; not equivalent to exposure."],
        "measure_note": "exposure/concentration",
    },
    {
        "number": 42,
        "key": "road_traffic_mortality",
        "category": "injury",
        "concept": "Road-traffic mortality",
        "indicator_id": "RS_198",
        "rationale": "External-cause injury mortality.",
        "reason_selected": "Estimated road traffic death rate with country-year observations; the SDGROADAGE data endpoint returned no observations.",
        "alternatives": ["SDGROADAGE: age-standardized SDG road-traffic mortality title but OData data endpoint returned no observations."],
        "warnings": ["Estimated mortality rate, not the age-standardized SDGROADAGE series."],
        "data_filter": "SpatialDimType eq 'COUNTRY'",
    },
]


def http_get(url: str, retries: int = 3, timeout: int = 120) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(request, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise RuntimeError(f"HTTP {status}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(2 * attempt, 8))
    raise RuntimeError(f"failed to GET {url}: {last_error}")


def load_json_bytes(raw: bytes, url: str) -> dict[str, Any]:
    if not raw.strip():
        raise ValueError(f"empty response from {url}")
    head = raw[:256].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        raise ValueError(f"HTML response from {url}")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"unexpected non-object JSON from {url}")
    return value


def write_snapshot(path: Path, raw: bytes, force: bool = False) -> tuple[Path, str, str]:
    digest = hashlib.sha256(raw).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if old_digest == digest:
            return path, digest, "reused_identical"
        if not force:
            versioned = path.with_name(
                f"{path.stem}_{datetime.now(timezone.utc).date().isoformat()}_{digest[:12]}{path.suffix}"
            )
            versioned.write_bytes(raw)
            return versioned, digest, "created_versioned_snapshot"
    path.write_bytes(raw)
    return path, digest, "created" if not force else "overwritten_force"


def fetch_json(url: str) -> tuple[bytes, dict[str, Any]]:
    raw = http_get(url)
    parsed = load_json_bytes(raw, url)
    return raw, parsed


def indicator_lookup(indicators: dict[str, Any]) -> dict[str, str]:
    return {
        item["IndicatorCode"]: item.get("IndicatorName")
        for item in indicators.get("value", [])
        if item.get("IndicatorCode")
    }


def selected_targets(args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = TARGETS
    if args.category:
        selected = [t for t in selected if t["category"] == args.category]
    if args.target:
        needle = args.target.lower()
        selected = [
            t
            for t in selected
            if needle in t["key"].lower()
            or needle == str(t["number"])
            or needle == str(t.get("indicator_id", "")).lower()
        ]
    return selected


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    countries = {r.get("SpatialDim") for r in records if r.get("SpatialDimType") == "COUNTRY" and r.get("SpatialDim")}
    geos = {r.get("SpatialDim") for r in records if r.get("SpatialDim")}
    years = sorted({r.get("TimeDim") for r in records if isinstance(r.get("TimeDim"), int)})
    sex = sorted({r.get("Dim1") for r in records if r.get("Dim1Type") == "SEX" and r.get("Dim1")})
    ages = sorted(
        {
            r.get(dim)
            for r in records
            for dim in ("Dim1", "Dim2", "Dim3")
            if r.get(f"{dim}Type") == "AGEGROUP" and r.get(dim)
        }
    )
    dim_types = sorted(
        {
            r.get(dim)
            for r in records
            for dim in ("Dim1Type", "Dim2Type", "Dim3Type", "DataSourceDimType", "SpatialDimType", "TimeDimType")
            if r.get(dim)
        }
    )
    missing_numeric = sum(1 for r in records if r.get("NumericValue") is None)
    return {
        "observation_count": len(records),
        "unique_geographic_entities": len(geos),
        "unique_country_level_entities": len(countries),
        "year_coverage": {"first": years[0], "last": years[-1]} if years else None,
        "sex_dimensions": sex,
        "age_dimensions": ages,
        "dimension_types_in_data": dim_types,
        "missing_numeric_values": missing_numeric,
    }


def suitability(summary: dict[str, Any], dimensions: list[dict[str, Any]], target: dict[str, Any]) -> str:
    if target.get("indicator_id") is None:
        return "LOW"
    dim_codes = {d.get("Dimension") for d in dimensions}
    years = summary.get("year_coverage") or {}
    countries = summary.get("unique_country_level_entities", 0)
    observations = summary.get("observation_count", 0)
    has_annual = "YEAR" in dim_codes and years.get("first") != years.get("last")
    has_country = "COUNTRY" in dim_codes and countries >= 100
    extra_dims = len([d for d in dim_codes if d not in {"COUNTRY", "REGION", "YEAR", "SEX", "WORLDBANKINCOMEGROUP", "PUBLISHSTATE"}])
    if has_country and has_annual and observations > 0 and not extra_dims and not target.get("warnings"):
        return "HIGH"
    if observations > 0 and has_country:
        return "MEDIUM"
    return "LOW"


def list_targets(targets: list[dict[str, Any]], titles: dict[str, str]) -> None:
    for target in targets:
        indicator_id = target.get("indicator_id") or "DEFERRED"
        title = titles.get(indicator_id, "") if target.get("indicator_id") else target["reason_selected"]
        print(f"{target['number']:02d} {target['category']} {target['key']} -> {indicator_id} | {title}")


def acquire(args: argparse.Namespace) -> int:
    targets = selected_targets(args)
    if not targets:
        print("No targets matched.", file=sys.stderr)
        return 2

    index_url = f"{BASE_URL}/Indicator"
    dimensions_url_template = f"{BASE_URL}/IndicatorDimension?$filter=IndicatorCode%20eq%20%27{{code}}%27"

    if args.dry_run:
        print(index_url)
        for target in targets:
            code = target.get("indicator_id")
            if not code:
                continue
            print(dimensions_url_template.format(code=quote(code, safe='')))
            data_url = f"{BASE_URL}/{quote(code, safe='')}"
            if target.get("data_filter"):
                data_url = f"{data_url}?$filter={quote(target['data_filter'], safe='')}"
            print(data_url)
        return 0

    index_raw, index_json = fetch_json(index_url)
    titles = indicator_lookup(index_json)

    if args.list:
        list_targets(targets, titles)
        return 0

    if not args.download:
        print("Specify --list or --download.", file=sys.stderr)
        return 2

    retrieval_ts = datetime.now(timezone.utc).isoformat()
    metadata_index_path, index_sha, index_status = write_snapshot(
        RAW_ROOT / "metadata" / "Indicator.json", index_raw, force=args.force
    )

    catalog: dict[str, Any] = {
        "provider": "World Health Organization",
        "access_method": "WHO Global Health Observatory OData API",
        "base_url": BASE_URL,
        "retrieval_timestamp": retrieval_ts,
        "indicator_index": {
            "source_endpoint": index_url,
            "local_snapshot_path": str(metadata_index_path),
            "sha256": index_sha,
            "status": index_status,
            "indicator_count": len(index_json.get("value", [])),
        },
        "targets": [],
    }

    for target in targets:
        entry = {
            "target_number": target["number"],
            "conceptual_target": target["concept"],
            "rationale": target["rationale"],
            "category": target["category"],
            "selected_who_indicator_id": target.get("indicator_id"),
            "selected_title": None,
            "alternatives_considered": target.get("alternatives", []),
            "reason_selected": target["reason_selected"],
            "definition": None,
            "topic_theme": None,
            "unit": None,
            "value_type": None,
            "geographic_level": None,
            "temporal_structure": None,
            "available_years": None,
            "sex_dimensions": [],
            "age_dimensions": [],
            "other_important_dimensions": [],
            "estimation_method": None,
            "source_publication_metadata": None,
            "source_endpoint": None,
            "source_filter": target.get("data_filter"),
            "retrieval_status": "deferred" if target.get("indicator_id") is None else "pending",
            "local_snapshot_path": None,
            "retrieval_timestamp": retrieval_ts,
            "sha256": None,
            "file_size": None,
            "observation_count": None,
            "country_coverage": None,
            "year_coverage": None,
            "whether_country_year_observations_exist": None,
            "integration_suitability": "LOW" if target.get("indicator_id") is None else None,
            "warnings": target.get("warnings", []),
            "failure_details": None,
            "measure_note": target.get("measure_note"),
        }
        code = target.get("indicator_id")
        if not code:
            catalog["targets"].append(entry)
            continue
        entry["selected_title"] = titles.get(code)
        if code not in titles:
            entry["retrieval_status"] = "failed"
            entry["failure_details"] = f"{code} not present in official WHO Indicator index."
            catalog["targets"].append(entry)
            continue
        try:
            dimensions_url = dimensions_url_template.format(code=quote(code, safe=""))
            dimensions_raw, dimensions_json = fetch_json(dimensions_url)
            dimensions_path, _, _ = write_snapshot(
                RAW_ROOT / "metadata" / f"{code}_dimensions.json", dimensions_raw, force=args.force
            )
            data_url = f"{BASE_URL}/{quote(code, safe='')}"
            if target.get("data_filter"):
                data_url = f"{data_url}?$filter={quote(target['data_filter'], safe='')}"
            data_raw, data_json = fetch_json(data_url)
            records = data_json.get("value")
            if not isinstance(records, list):
                raise ValueError("data response lacks a JSON array in 'value'")
            if not records:
                raise ValueError("data response contains no observations")
            if any(r.get("IndicatorCode") != code for r in records if isinstance(r, dict)):
                raise ValueError("data response contains a mismatched IndicatorCode")
            data_path, data_sha, data_status = write_snapshot(
                RAW_ROOT / target["category"] / f"{code}.json", data_raw, force=args.force
            )
            summary = summarize_records(records)
            dimensions = dimensions_json.get("value", [])
            dim_codes = [d.get("Dimension") for d in dimensions if d.get("Dimension")]
            entry.update(
                {
                    "source_endpoint": data_url,
                    "retrieval_status": data_status,
                    "local_snapshot_path": str(data_path),
                    "metadata_dimensions_snapshot_path": str(dimensions_path),
                    "sha256": data_sha,
                    "file_size": data_path.stat().st_size,
                    "observation_count": summary["observation_count"],
                    "country_coverage": {
                        "unique_country_level_entities": summary["unique_country_level_entities"],
                        "unique_geographic_entities": summary["unique_geographic_entities"],
                    },
                    "year_coverage": summary["year_coverage"],
                    "available_years": summary["year_coverage"],
                    "sex_dimensions": summary["sex_dimensions"],
                    "age_dimensions": summary["age_dimensions"],
                    "other_important_dimensions": [
                        d for d in dim_codes if d not in {"COUNTRY", "REGION", "YEAR", "SEX", "AGEGROUP"}
                    ],
                    "dimensions": dimensions,
                    "geographic_level": "COUNTRY present" if "COUNTRY" in dim_codes else None,
                    "temporal_structure": "YEAR present" if "YEAR" in dim_codes else None,
                    "whether_country_year_observations_exist": summary["unique_country_level_entities"] > 0
                    and bool(summary["year_coverage"]),
                    "validation_summary": summary,
                    "integration_suitability": suitability(summary, dimensions, target),
                }
            )
        except Exception as exc:
            entry["retrieval_status"] = "failed"
            entry["failure_details"] = str(exc)
        catalog["targets"].append(entry)
        time.sleep(0.4)

    if (args.target or args.category) and CATALOG_PATH.exists():
        existing = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        merged_by_number = {item["target_number"]: item for item in existing.get("targets", [])}
        for item in catalog["targets"]:
            merged_by_number[item["target_number"]] = item
        catalog["targets"] = [merged_by_number[number] for number in sorted(merged_by_number)]

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {CATALOG_PATH}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List resolved WHO indicators without downloading.")
    parser.add_argument("--download", action="store_true", help="Download the curated collection.")
    parser.add_argument("--target", help="Download/list one conceptual target by name, number, or indicator ID.")
    parser.add_argument("--category", help="Download/list one indicator category.")
    parser.add_argument("--dry-run", action="store_true", help="Show intended WHO requests without writing files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing snapshots rather than versioning.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(acquire(parse_args()))
