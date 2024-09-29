"""
This module calcluates d (distances) values fomr polygons to fauls using faults defined in a CFM shapefile


NB this was originally in input_data folder alongside the data files.

Data files are now found in the `{RESOURCES}/pipeline/v1/input_data` folder.
"""


import geopandas as gpd
import pandas as pd
import pathlib

from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER
from nzssdt_2023.data_creation.dm_parameter_generation import calc_distance_to_faults
from nzssdt_2023.data_creation.query_NSHM import create_sites_df

def build_d_value_dataframe() -> 'pdt.DataFrame':
    in_path = pathlib.Path( RESOURCES_FOLDER) / "pipeline/v1/input_data"

    filename = in_path / "CFM_5mmyr" / "NZ_CFM_v1_0_SR_Pref_5mmyr+.shp"
    faults = gpd.read_file(filename)

    filename = in_path / "polygons_locations.geojson"
    polygons = gpd.read_file(filename).set_index("UR2022_V_2")

    D_polygons = calc_distance_to_faults(polygons, faults)

    grid_df = create_sites_df(named_sites=False)
    grid = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(grid_df.lon, grid_df.lat, crs="EPSG:4326"), data=grid_df
    )
    D_grid = calc_distance_to_faults(grid, faults)
    return pd.concat([D_polygons, D_grid])

if __name__ == '__main__':

    d_values_df = build_d_value_dataframe()
    print(d_values_df)
    out_path = pathlib.Path(WORKING_FOLDER)
    assert out_path.exists() and out_path.is_dir(), f"Path {out_path} was not found or is not a folder."
    d_values_df.to_json(out_path / "D_values.json")
