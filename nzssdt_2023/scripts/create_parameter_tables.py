"""
This uses everthing in Annes pipeline

pre-requisities:
 - input_files/CFM_5mmyr/* was supplied by Nick H
 - input_files/polygons_locations.geojson supplied by Nick H
 - together, these produce: D_Values (`input_data/D_values.json`)

 - input_file/mean_magnitudes (3 csv files) are available (input data) (check this matches new CDC package)

"""

import logging
import pickle as pkl
from pathlib import Path
from typing import Optional

import numpy as np

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

mini = False
legacy = True

output_folder = Path(WORKING_FOLDER)

site_list: Optional[list[str]] = None

if mini:
    hf_path = output_folder / "mini_hcurves.hdf5"
    sa_path = output_folder / "mini_SaT-variables.pkl"
    dm_path = output_folder / "mini_D-M-tables.csv"

    site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington"]
else:
    hf_path = output_folder / "recreated_hcurves.hdf5"
    sa_path = output_folder / "recreated_SaT-variables.pkl"
    dm_path = output_folder / "recreated_D-M-tables.csv"

# generate Sa Parameter Tables (writes pkl and hdf5 files)
sa_gen.create_sa_pkl(hf_path, sa_path, site_list=site_list)

# extract metadata from Sa Parameter Tables
with open(sa_path, "rb") as file:
    df = pkl.load(file)
    site_list, APoEs, site_class_list = dm_gen.return_table_indices(df)

    rps = np.sort([int(APoE.split("/")[1]) for APoE in APoEs])
    APoEs = [f"APoE: 1/{rp}" for rp in rps]

# generate D and M Tables
dm_df = dm_gen.create_D_and_M_table(site_list, APoEs, legacy=legacy)
dm_df.to_csv(dm_path)

# print(f"{filename} saved to \n\t{os.getcwd()}")
# (writes the D&M csv files)
