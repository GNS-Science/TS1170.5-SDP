"""
This module creates .geojson version of all gis data and calculates D (distance) values between polygons and faults

"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, Union

import geopandas as gpd
import pandas as pd

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation.constants import (
    CFM_URL,
    LOCATION_REPLACEMENTS,
    POLYGON_PATH,
)
from nzssdt_2023.data_creation.query_NSHM import create_sites_df
from nzssdt_2023.data_creation.util import set_coded_location_resolution

from nzssdt_2023.data_creation.util import set_coded_location_resolution

if TYPE_CHECKING:
    import geopandas.typing as gpdt
    import pandas.typing as pdt

log = logging.getLogger(__name__)


def save_gdf_to_geojson(gdf: "gpdt.DataFrame", path, include_idx=False):
    """Saves a geodataframe to a .geojson file

    TODO: set up typing for the path input

    Args:
        gdf: geodataframe to save as .geosjon
        path: path of new geojson
        include_idx: False drops the index from the gpd (e.g. if index is just a range, 0 -> n)
    """

    gdf.to_file(path, driver="GeoJSON", index=include_idx)


def polygon_location_list() -> List[str]:
    """Returns the urban and rural settlement names, excluding those that do not have their own polygon

    Returns:
        polygon_list: ordered list of polygon names
    """
    ts_urban_locations_list = list(create_sites_df().index)

    replaced_locations = []
    for location in LOCATION_REPLACEMENTS:
        for replaced_location in LOCATION_REPLACEMENTS[location].replaced_locations:
            replaced_locations.append(replaced_location)

    polygon_list = [
        loc for loc in ts_urban_locations_list if loc not in replaced_locations
    ]

    return polygon_list


def cleanup_polygon_gpd(polygon_path) -> "gpdt.DataFrame":
    """Removes extra columns from input polygon file

    Args:
        polygon_path: path to the original polygon file

    Returns:
        gdf: geodataframe with only relevant columns
    """

    # read original file
    gdf = gpd.read_file(polygon_path).set_index("UR2022_V_2")[["geometry"]]
    gdf["Name"] = gdf.index
    gdf.set_index("Name", inplace=True)

    # sort the order
    polygon_list = polygon_location_list()
    gdf = gdf.loc[polygon_list, :]

    # convert to WGS84
    wgs_epsg = 4326
    gdf = gdf.to_crs(epsg=wgs_epsg)

    return gdf


def filter_cfm_by_sliprate(cfm_url, slip_rate: float = 5.0) -> "gpdt.DataFrame":
    """Filters the original Community Fault Model (CFM) .shp file

    The faults are filtered by the (Slip Rate Preferred >=5 mmyr) criterion.

    Args:
        slip_rate: slip rate for filter criterion, >= slip_rate

    Returns:
        gdf: geodataframe of filtered faults
    """

    gdf = gpd.read_file(cfm_url)

    idx = gdf["SR_pref"] >= slip_rate
    gdf = gdf[idx].sort_values("Name").reset_index()
    gdf.drop("index", axis=1, inplace=True)

    wgs_epsg = 4326
    gdf = gdf.to_crs(epsg=wgs_epsg)

    gdf["Slip rate preferred value"] = gdf["SR_pref"]
    gdf["Slip rate filter"] = f"≥{slip_rate} mm/yr"
    gdf[
        "Source for linework and slip rate assessment"
    ] = "NZ CFM v1.0 (Seebeck et al. 2022, 2023)"
    gdf = gdf[
        [
            "Name",
            "Slip rate preferred value",
            "Slip rate filter",
            "Source for linework and slip rate assessment",
            "geometry",
        ]
    ]

    return gdf


def calc_distance_to_faults(
    gdf: "gpdt.DataFrame", faults: "gpdt.DataFrame"
) -> "pdt.DataFrame":
    """Calculates the closest distance of polygons or points to a set of fault lines

    Args:
        gdf: geodataframe of locations (polygons or points)
        faults: geodataframe of fault lines

    Returns:
        df: dataframe of distance from each location to the closest fault
    """
    meter_epsg = 2193
    faults.to_crs(epsg=meter_epsg, inplace=True)
    gdf.to_crs(epsg=meter_epsg, inplace=True)

    gdf["distance"] = round(
        gdf.geometry.apply(lambda x: faults.distance(x).min()) / 1000.0
    )

    gdf["D"] = gdf["distance"].astype("int")
    gdf.loc[gdf["D"] >= 20, "D"] = None

    wgs_epsg = 4326
    gdf.to_crs(epsg=wgs_epsg, inplace=True)

    gdf.index.names = [""]

    return gdf[["D"]]


def create_fault_and_polygon_gpds() -> Tuple["gpdt.DataFrame", "gpdt.DataFrame"]:
    """Creates the two geodataframes for resource output

    Returns:
        faults: geodataframe of major faults
        polygons: geodataframe of urban area polygons
    """

    polygons = cleanup_polygon_gpd(POLYGON_PATH)
    faults = filter_cfm_by_sliprate(CFM_URL)

    return faults, polygons


def create_grid_gpd() -> "gpdt.DataFrame":
    """Creates one geodataframe for resource output

    Returns:
        grid: geodataframe of lat/lon grid points
    """

    grid_df = create_sites_df(named_sites=False)
    grid_df = set_coded_location_resolution(grid_df)
    grid_df.index.name = "Name"

    grid = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(grid_df.lon, grid_df.lat, crs="EPSG:4326"),
        data=grid_df,
    )

    return grid[["geometry"]]


def create_geojson_files(
    polygons_path: Union[str | Path],
    faults_path: Union[str | Path],
    grid_path: Union[str | Path],
    override: bool = False,
):
    """Create the .geojsons for the version resources

    Args:
        polygons_path: path to polygon .geojson
        faults_path: path to faults .geojson
        override: if True, rewrite all files

    """

    if (
        override
        | (not Path(polygons_path).exists())
        | (not Path(faults_path).exists())
        | (not Path(grid_path).exists())
    ):

        faults, polygons = create_fault_and_polygon_gpds()

        save_gdf_to_geojson(faults, faults_path)
        save_gdf_to_geojson(polygons, polygons_path, include_idx=True)

        grid = create_grid_gpd()
        save_gdf_to_geojson(grid, grid_path, include_idx=True)

    if override:
        d_values_path = Path(WORKING_FOLDER, "D_values.json")
        if d_values_path.exists():
            os.remove(d_values_path)


def build_d_value_dataframe() -> "pdt.DataFrame":
    """Calculates the distance from faults to each named location and grid point

    The number of sites considered is always the full amount, regardless of whether
    the site_list has been reduced for the rest of the table generation

    Returns:


    """
    log.info("build_d_value_dataframe() processesing distance to fault for each site")

    faults, polygons = create_fault_and_polygon_gpds()

    D_polygons = calc_distance_to_faults(polygons, faults)

    grid = create_grid_gpd()
    D_grid = calc_distance_to_faults(grid, faults)

    D_values = pd.concat([D_polygons, D_grid])
    D_values.index.name = "Location"

    return D_values
