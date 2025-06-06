"""
This module contains constants for the end user functions module

The data is linked directly to the Standards NZ deliverables folder for V2, using the associated filenames

Three constants are imported from other parts of the library:

    from nzssdt_2023.config import DELIVERABLES_FOLDER, RESOURCES_FOLDER

    from nzssdt_2023.data_creation.constants import DEFAULT_RPS, SITE_CLASSES
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from nzssdt_2023.config import DELIVERABLES_FOLDER, RESOURCES_FOLDER
from nzssdt_2023.data_creation.constants import DEFAULT_RPS, SITE_CLASSES

TS_VERSION = "v2"
SNZ_NAME_PREFIX = "TS1170-5"
PUBLICATION_YEAR = 2025
DELIVERABLES_VERSION = Path(DELIVERABLES_FOLDER, TS_VERSION)

NAMED_PARAMETERS_PATH = Path(
    DELIVERABLES_VERSION, f"{SNZ_NAME_PREFIX}_Table3-1_{PUBLICATION_YEAR}.json"
)
GRID_PARAMETERS_PATH = Path(
    DELIVERABLES_VERSION, f"{SNZ_NAME_PREFIX}_Table3-2_{PUBLICATION_YEAR}.json"
)
POLYGONS_PATH = Path(
    DELIVERABLES_VERSION,
    f"{SNZ_NAME_PREFIX}_Figure3-2_{PUBLICATION_YEAR}.geojson",
)
GRID_POINTS_PATH = Path(
    DELIVERABLES_VERSION, f"{SNZ_NAME_PREFIX}_GridPoints_{PUBLICATION_YEAR}.geojson"
)
FAULTS_PATH = Path(
    DELIVERABLES_VERSION, f"{SNZ_NAME_PREFIX}_MajorFaults_{PUBLICATION_YEAR}.geojson"
)
NZ_MAP_PATH = Path(RESOURCES_FOLDER, "end_user_functions", "nz_map.geojson")


NAMED_PARAMETER_TABLE = pd.read_json(
    NAMED_PARAMETERS_PATH, orient="table", precise_float=True
)
GRID_PARAMETER_TABLE = pd.read_json(
    GRID_PARAMETERS_PATH, orient="table", precise_float=True
)
PARAMETER_TABLE = pd.concat([NAMED_PARAMETER_TABLE, GRID_PARAMETER_TABLE], axis=0)

APOE_NS = DEFAULT_RPS
APOES = [f"1/{n}" for n in APOE_NS]
SITE_CLASSES_LIST = list(SITE_CLASSES.keys())
SA_PARAMETER_NAMES = ["PGA", "Sas", "Tc", "Td"]

APOE_N_THRESHOLD_FOR_D = 500

DEFAULT_PERIODS = list(np.arange(0, 3 + 0.01, 0.01)) + [3.5, 4, 4.5, 5, 6, 7, 8, 9, 10]


POLYGONS = gpd.read_file(POLYGONS_PATH).set_index("Name")
GRID_PTS = gpd.read_file(GRID_POINTS_PATH).set_index("Name")
FAULTS = gpd.read_file(FAULTS_PATH)
NZ_MAP = gpd.read_file(NZ_MAP_PATH)
