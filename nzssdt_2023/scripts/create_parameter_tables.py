"""
Complete pipline from NSHM to pdf (using last year's formatting)

"""

import logging
import os
from pathlib import Path, PurePath
from typing import Optional

import pandas as pd

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation.NSHM_to_hdf5 import query_NSHM_to_hdf5
from nzssdt_2023.data_creation.query_NSHM import create_sites_df
from nzssdt_2023.publish.convert import d_and_m_table_to_json, sat_table_to_json

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

working_folder = Path(WORKING_FOLDER)
version_folder = Path(
    PurePath(os.path.realpath(__file__)).parent.parent.parent, "resources", "v_cbc"
)

mini = False
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
    hf_path = working_folder / "all_hcurves.hdf5"
    site_list: Optional[list[str]] = None

# query NSHM
if override | (not hf_path.exists()):
    query_NSHM_to_hdf5(hf_path, site_list=site_list)


# create sa tables
if (
    override
    | (not (version_folder / "named_locations.json").exists())
    | (not (version_folder / "grid_locations.json").exists())
):
    # sat_table_to_json(hf_path, version_folder)
    complete_table_to_json(hf_path, version_folder)

# # create m and d table
# if override | (not (version_folder / "d_and_m.json").exists()):
#     if site_list is None:
#         site_list = list(
#             pd.concat([create_sites_df(), create_sites_df(named_sites=False)]).index
#         )
#     d_and_m_table_to_json(version_folder, site_list)
