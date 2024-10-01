"""
This module calculates D (distance) values between polygons and faults

Required data:
 - faults defined in a CFM shapefile.
 - polygons defined in geojson fle

NB these was originally in input_data folder alongside the data files and are now
found in the `{RESOURCES}/pipeline/v1/input_data` folder.
"""


from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER
from nzssdt_2023.data_creation.dm_parameter_generation import calc_distance_to_faults
from nzssdt_2023.data_creation.query_NSHM import create_sites_df

if TYPE_CHECKING:
    import pandas.typing as pdt


def build_d_value_dataframe() -> "pdt.DataFrame":
    in_path = Path(RESOURCES_FOLDER) / "pipeline/v1/input_data"

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


if __name__ == "__main__":

    d_values_df = build_d_value_dataframe()
    print(d_values_df)
    out_path = Path(WORKING_FOLDER)
    assert (
        out_path.exists() and out_path.is_dir()
    ), f"Path {out_path} was not found or is not a folder."
    d_values_df.to_json(out_path / "D_values.json")
