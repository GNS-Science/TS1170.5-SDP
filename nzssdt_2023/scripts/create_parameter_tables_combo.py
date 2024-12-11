"""
Complete pipline from NSHM to pdf (using new formatting)

"""

import logging
import os
from pathlib import Path, PurePath
from typing import Optional

import pandas as pd

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen
from nzssdt_2023.data_creation.gis_data import (
    build_d_value_dataframe,
    create_fault_and_polygon_gpds,
    save_gdf_to_geojson,
)
from nzssdt_2023.data_creation.NSHM_to_hdf5 import query_NSHM_to_hdf5
from nzssdt_2023.data_creation.query_NSHM import create_sites_df
from nzssdt_2023.publish.convert import (
    AllParameterTable,
    DistMagTable,
    SatTable,
    sat_table_json_path,
    to_standard_json,
)

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

working_folder = Path(WORKING_FOLDER)
version_folder = Path(
    PurePath(os.path.realpath(__file__)).parent.parent.parent, "resources", "v_cbc"
)

mini = False
site_limit = 10
override = False

if mini:
    hf_path = working_folder / "mini_hcurves.hdf5"
    site_list = [
        "Auckland",
        "Christchurch",
        "Dunedin",
        "Hamilton",
        "Wellington",
    ]  # be nice if we could do these too... "-43.900~169.100"
else:
    hf_path = (
        working_folder / f"first_{site_limit * 2}_hcurves.hdf5"
        if site_limit
        else working_folder / "all_hcurves.hdf5"
    )
    site_list: Optional[list[str]] = None


# query NSHM
if override | (not hf_path.exists()):
    query_NSHM_to_hdf5(hf_path, site_list=site_list, site_limit=site_limit)

# output paths
named_path = sat_table_json_path(
    version_folder, named_sites=True, site_limit=site_limit, combo=True
)
gridded_path = sat_table_json_path(
    version_folder, named_sites=False, site_limit=site_limit, combo=True
)
polygons_path = Path(version_folder, "urban_area_polygons.geojson")
faults_path = Path(version_folder, "major_faults.geojson")
d_values_path = Path(WORKING_FOLDER, "D_values.json")

if (
    override
    | (not polygons_path.exists())
    | (not faults_path.exists())
    | (not d_values_path.exists())
):
    faults, polygons = create_fault_and_polygon_gpds()
    d_values = build_d_value_dataframe()

    save_gdf_to_geojson(faults, faults_path)
    save_gdf_to_geojson(polygons, polygons_path, include_idx=True)
    d_values.to_json(d_values_path)

if override | (not named_path.exists()) | (not gridded_path.exists()):

    if site_list is None:
        site_list = list(
            pd.concat(
                [
                    create_sites_df(site_limit=site_limit),
                    create_sites_df(named_sites=False, site_limit=site_limit),
                ]
            ).index
        )

    # build and combine the tables
    sat_df = sa_gen.create_sa_table(hf_path)
    dm_df = DistMagTable(
        dm_gen.create_D_and_M_df(site_list, rp_list=constants.DEFAULT_RPS)
    ).flatten()

    combined_df = SatTable(sat_df).combine_dm_table(dm_df)

    complete = AllParameterTable(combined_df)

    # write the files
    to_standard_json(complete.named_location_df(), named_path)
    to_standard_json(complete.grid_location_df(), gridded_path)
