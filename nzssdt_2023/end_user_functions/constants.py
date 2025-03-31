"""
This module contains constants for the end user functions module

Three constants are imported from other parts of the library:

    from nzssdt_2023.config import RESOURCES_FOLDER

    from nzssdt_2023.data_creation.constants import DEFAULT_RPS, SITE_CLASSES
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.data_creation.constants import DEFAULT_RPS, SITE_CLASSES

TS_VERSION = "v2"

NAMED_PARAMETERS_PATH = Path(RESOURCES_FOLDER, TS_VERSION, "named_locations_combo.json")
GRID_PARAMETERS_PATH = Path(RESOURCES_FOLDER, TS_VERSION, "grid_locations_combo.json")
POLYGONS_PATH = Path(RESOURCES_FOLDER, TS_VERSION, "urban_area_polygons.geojson")
FAULTS_PATH = Path(RESOURCES_FOLDER, TS_VERSION, "major_faults.geojson")
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
FAULTS = gpd.read_file(FAULTS_PATH)
NZ_MAP = gpd.read_file(NZ_MAP_PATH)


# function for creating geodataframe as a constant
def create_grid_gdf():
    """Creates a geodataframe with each grid point in the TS table

    Returns:
        grid_pts: a geodataframe of TS grid points
    """

    # filter by apoe and site class to get an index of unique locations
    apoe_n = APOE_NS[0]
    site_class = SITE_CLASSES_LIST[0]

    apoe_idx = GRID_PARAMETER_TABLE["APoE (1/n)"] == apoe_n
    sc_idx = GRID_PARAMETER_TABLE["Site Class"] == site_class
    idx = apoe_idx & sc_idx

    # create list of names, latitudes, and longitudes
    grid_names = list(GRID_PARAMETER_TABLE[idx]["Location"].values)
    lats = [float(latlon.split("~")[0]) for latlon in grid_names]
    lons = [float(latlon.split("~")[1]) for latlon in grid_names]

    # create gdf
    grid_pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats)).set_crs(4326)
    grid_pts["latlon"] = [(lat, lon) for lat, lon in zip(lats, lons)]
    grid_pts["name"] = grid_names
    grid_pts.set_index("name", inplace=True)

    return grid_pts


GRID_PTS = create_grid_gdf()
