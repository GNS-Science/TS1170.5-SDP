"""
This module contains constants used for mean mag table generation. The intermediate tables are generated for all sites
and probabilities, regardless of what is requested by the call to extract_m_values.
"""

from typing import Any, Dict

from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.model import ProbabilityEnum


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
