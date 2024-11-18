"""
Complete pipline from NSHM to pdf (using last year's formatting)

"""

import logging
import pickle as pkl
import os
from pathlib import Path, PurePath
from typing import Optional

import numpy as np

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation.NSHM_to_hdf5 import query_NSHM_to_hdf5
from nzssdt_2023.data_creation.sa_parameter_generation import create_sa_table
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.publish.convert import sat_table_to_json

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

working_folder = Path(WORKING_FOLDER)
version_folder = Path(PurePath(os.path.realpath(__file__)).parent.parent.parent, "resources", "v_test")

mini = True
override = False

if mini:
    hf_path = working_folder / "mini_hcurves.hdf5"
    site_list = ["Auckland", "Christchurch", "Dunedin", "Hamilton", "Wellington"]
else:
    hf_path = working_folder / "all_hcurves.hdf5"
    site_list: Optional[list[str]] = None

# query NSHM
if override | (not hf_path.exists()):
    query_NSHM_to_hdf5(hf_path, site_list=site_list)

# create table
if override | (not (version_folder / "named_locations.json").exists()):
    sat_table_to_json(hf_path, version_folder)





# # extract metadata from Sa Parameter Tables
# with open(sa_path, "rb") as file:
#     df = pkl.load(file)
#     site_list, APoEs, site_class_list = dm_gen.return_table_indices(df)
#
#     rps = np.sort([int(APoE.split("/")[1]) for APoE in APoEs])
#     APoEs = [f"APoE: 1/{rp}" for rp in rps]
#
# # generate D and M Tables
# dm_df = dm_gen.create_D_and_M_table(site_list, APoEs, legacy=legacy)
# dm_df.to_csv(dm_path)
