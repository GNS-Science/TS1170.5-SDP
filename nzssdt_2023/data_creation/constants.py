"""
This module contains constants.
"""

from typing import Any, Dict, NamedTuple

import numpy as np
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.model import ProbabilityEnum


class SiteClass(NamedTuple):
    site_class: str
    representative_vs30: int
    label: str
    lower_bound: float
    upper_bound: float


class LocationReplacement(NamedTuple):
    preferred_location: str
    replaced_locations: list[str]


class PGA_reductions(NamedTuple):
    site_class: str
    A0: float
    A1: float
    PGA_threshold: float


def lat_lon_from_id(id):
    return (location_by_id(id)["latitude"], location_by_id(id)["longitude"])


location_list = "SRWG214"
location_grid = "NZ_0_1_NB_1_1"
akl_location_id = "srg_29"

RP_TO_POE = {
    10000: ProbabilityEnum._05_PCT_IN_50YRS,
    5000: ProbabilityEnum._1_PCT_IN_50YRS,
    2500: ProbabilityEnum._2_PCT_IN_50YRS,
    1000: ProbabilityEnum._5_PCT_IN_50YRS,
    500: ProbabilityEnum._10_PCT_IN_50YRS,
    250: ProbabilityEnum._18_PCT_IN_50YRS,
    100: ProbabilityEnum._39_PCT_IN_50YRS,
    50: ProbabilityEnum._63_PCT_IN_50YRS,
    25: ProbabilityEnum._86_PCT_IN_50YRS,
}
POE_TO_RP = {poe: rp for rp, poe in RP_TO_POE.items()}

ALL_SITES: Dict[str, Dict[str, Any]] = {
    location_by_id(_id)["name"]: location_by_id(_id)
    for _id in LOCATION_LISTS[location_list]["locations"]
}

DEFAULT_RPS = [25, 50, 100, 250, 500, 1000, 2500]


AGG_LIST = ["mean", "0.9"]
IMT_LIST = [
    "PGA",
    "SA(0.1)",
    "SA(0.15)",
    "SA(0.2)",
    "SA(0.25)",
    "SA(0.3)",
    "SA(0.35)",
    "SA(0.4)",
    "SA(0.5)",
    "SA(0.6)",
    "SA(0.7)",
    "SA(0.8)",
    "SA(0.9)",
    "SA(1.0)",
    "SA(1.25)",
    "SA(1.5)",
    "SA(1.75)",
    "SA(2.0)",
    "SA(2.5)",
    "SA(3.0)",
    "SA(3.5)",
    "SA(4.0)",
    "SA(4.5)",
    "SA(5.0)",
    "SA(6.0)",
    "SA(7.5)",
    "SA(10.0)",
]

IMTL_LIST = [
    0.0001,
    0.0002,
    0.0004,
    0.0006,
    0.0008,
    0.001,
    0.002,
    0.004,
    0.006,
    0.008,
    0.01,
    0.02,
    0.04,
    0.06,
    0.08,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    6.0,
    7.0,
    8.0,
    9.0,
    10.0,
]

SITE_CLASSES: dict[str, SiteClass] = {
    "I": SiteClass("I", 750, "Site Class I", 750, np.nan),
    "II": SiteClass("II", 525, "Site Class II", 450, 750),
    "III": SiteClass("III", 375, "Site Class III", 300, 450),
    "IV": SiteClass("IV", 275, "Site Class IV", 250, 300),
    "V": SiteClass("V", 225, "Site Class V", 200, 250),
    "VI": SiteClass("VI", 175, "Site Class VI", 150, 200),
}


VS30_LIST = [SITE_CLASSES[sc].representative_vs30 for sc in SITE_CLASSES.keys()]


LOWER_BOUND_PARAMETERS: dict[str, str | float] = {
    "controlling_site": "Auckland",
    "controlling_percentile": 0.9,
}

LOCATION_REPLACEMENTS: dict[str, LocationReplacement] = {
    "Auckland": LocationReplacement("Auckland", ["Manukau City"]),
    "Tauranga": LocationReplacement("Tauranga", ["Mount Maunganui"]),
    "Wellington": LocationReplacement("Wellington", ["Wellington CBD"]),
    "Lower Hutt": LocationReplacement("Lower Hutt", ["Wainuiomata", "Eastbourne"]),
}

PGA_REDUCTIONS: dict[str, PGA_reductions] = {
    "IV": PGA_reductions("IV", 0.076, 0.123, 0.198),
    "V": PGA_reductions("V", 0.114, 0.227, 0.137),
    "VI": PGA_reductions("VI", 0.085, 0.171, 0.133),
}

# specify number of decimal places or significant figures to round to
PGA_N_DP = 2
SAS_N_DP = 2
TC_N_SF = 2
TD_N_SF = 2
