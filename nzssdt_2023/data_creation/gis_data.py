"""
This module creates .geojson version of all gis data and calculates D (distance) values between polygons and faults

Required data:
 - faults defined in a CFM shapefile.
 - polygons defined in geojson fle

The are found in the `{RESOURCES}/pipeline/v2/input_data/original_gis` folder.
"""


from pathlib import Path
from typing import TYPE_CHECKING, List

import geopandas as gpd
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER
from nzssdt_2023.data_creation.query_NSHM import create_sites_df
from nzssdt_2023.data_creation.constants import LOCATION_REPLACEMENTS

if TYPE_CHECKING:
    import pandas.typing as pdt

version = 'v_gisdata'  # for development only. eventually this will be v2


def polygon_location_list() -> List[str]:
    """ Returns the urban and rural settlement names, excluding those that do not have their own polygon

    Returns:
        polygon_list: ordered list of polygon names
    """

    replaced_locations = []
    for location in LOCATION_REPLACEMENTS:
        for replaced_location in LOCATION_REPLACEMENTS[location].replaced_locations:
            replaced_locations.append(replaced_location)

    polygon_list = [loc for loc in list(create_sites_df().index) if loc not in replaced_locations]

    return polygon_list


def polygons_to_clean_geojson(version):
    """Creats a new file without the extra columns in the polygon.geojson from Nick Horpool

    """
    # read original file
    in_path = Path(RESOURCES_FOLDER) / "pipeline" / version / "input_data/original_gis"
    filename = in_path / "polygons_locations.geojson"
    gdf = gpd.read_file(filename).set_index('UR2022_V_2')[['geometry']]
    gdf['Name'] = gdf.index

    # sort the order
    polygon_list = polygon_location_list()
    gdf = gdf.loc[polygon_list, :]

    # convert to WGS84
    wgs_epsg = 4326
    gdf = gdf.to_crs(epsg=wgs_epsg)

    # save new file
    out_path = Path(RESOURCES_FOLDER) / version
    filename = out_path / "urban_area_polygons.geojson"
    gdf.to_file(filename, driver="GeoJSON", index=False)




def cfm_to_geojson():
    """Converts the Community Fault Model (CFM) .shp file from Nick Horspool into a .geojson file

    Nick derived this .shp from the original CFM, using the >X (slip rate) criterion
    TODO need further documentation on this
    """




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
    faults.to_crs(epsg=meter_epsg)
    gdf = gdf.to_crs(epsg=meter_epsg)

    gdf["distance"] = round(
        gdf.geometry.apply(lambda x: faults.distance(x).min()) / 1000.0
    )

    gdf["D"] = gdf["distance"].astype("int")
    gdf.loc[gdf["D"] >= 20, "D"] = None

    wgs_epsg = 4326
    gdf = gdf.to_crs(epsg=wgs_epsg)

    gdf.index.names = [""]

    return gdf[["D"]]


def build_d_value_dataframe() -> "pdt.DataFrame":
    in_path = Path(RESOURCES_FOLDER) / "pipeline/v2/input_data/original_gis"

    filename = in_path / "CFM_5mmyr" / "NZ_CFM_v1_0_SR_Pref_5mmyr+.shp"
    faults = gpd.read_file(filename)

    filename = in_path / "polygons_locations.geojson"
    polygons = gpd.read_file(filename).set_index("UR2022_V_2")

    D_polygons = calc_distance_to_faults(polygons, faults)

    grid_df = create_sites_df(named_sites=False)
    grid = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(grid_df.lon, grid_df.lat, crs="EPSG:4326"),
        data=grid_df,
    )
    D_grid = calc_distance_to_faults(grid, faults)
    return pd.concat([D_polygons, D_grid])


# if __name__ == "__main__":
#
#     d_values_df = build_d_value_dataframe()
#     print(d_values_df)
#     out_path = Path(WORKING_FOLDER)
#     assert (
#         out_path.exists() and out_path.is_dir()
#     ), f"Path {out_path} was not found or is not a folder."
#     d_values_df.to_json(out_path / "D_values.json")
