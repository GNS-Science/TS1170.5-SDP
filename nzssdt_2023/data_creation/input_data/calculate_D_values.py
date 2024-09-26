import geopandas as gpd
import pandas as pd

from nzssdt_2023.data_creation.dm_parameter_generation import calc_distance_to_faults
from nzssdt_2023.data_creation.query_NSHM import create_sites_df

filename = "CFM_5mmyr/NZ_CFM_v1_0_SR_Pref_5mmyr+.shp"
faults = gpd.read_file(filename)

filename = "polygons_locations.geojson"
polygons = gpd.read_file(filename).set_index("UR2022_V_2")
D_polygons = calc_distance_to_faults(polygons, faults)

grid_df = create_sites_df(named_sites=False)
grid = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(grid_df.lon, grid_df.lat, crs="EPSG:4326"), data=grid_df
)
D_grid = calc_distance_to_faults(grid, faults)

D_values = pd.concat([D_polygons, D_grid])
D_values.to_json("D_values.json")
