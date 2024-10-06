"""
This module contains constants used for mean mag table generation. The intermediate tables are generated for all sites
and probabilities, regardless of what is requested by the call to extract_m_values.
"""

from pathlib import Path

from nzshm_common.grids import load_grid
from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS
from toshi_hazard_store.model import ProbabilityEnum

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation.mean_magnitudes import lat_lon_from_id

location_list = "SRWG214"
location_grid = "NZ_0_1_NB_1_1"
akl_location_id = "srg_29"

SRWG_LOCATIONS = [
    CodedLocation(*lat_lon_from_id(_id), 0.001)
    for _id in LOCATION_LISTS[location_list]["locations"]
]
GRID_LOCATIONS = [CodedLocation(*loc, 0.001) for loc in load_grid(location_grid)]
AKL_LOCATIONS = [CodedLocation(*lat_lon_from_id(akl_location_id), 0.001)]
POES = [
    ProbabilityEnum._2_PCT_IN_50YRS,
    ProbabilityEnum._5_PCT_IN_50YRS,
    ProbabilityEnum._10_PCT_IN_50YRS,
    ProbabilityEnum._18_PCT_IN_50YRS,
    ProbabilityEnum._39_PCT_IN_50YRS,
    ProbabilityEnum._63_PCT_IN_50YRS,
    ProbabilityEnum._86_PCT_IN_50YRS,
]


SRWG_214_MEAN_MAG_FILEPATH = Path(WORKING_FOLDER, "SRWG214_mean_mag.csv")
GRID_MEAN_MAG_FILEPATH = Path(WORKING_FOLDER, "grid_mean_mag.csv")
AKL_MEAN_MAG_P90_FILEPATH = Path(WORKING_FOLDER, "AKL_90pct_mean_mag.csv")
