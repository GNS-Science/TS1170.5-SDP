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
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

mini = False

output_folder = Path(WORKING_FOLDER)

site_list: Optional[list[str]] = None

if mini:
    hf_path = output_folder / "mini_hcurves.hdf5"
    sa_path = output_folder / "mini_SaT-variables.pkl"

    site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington", ]
else:
    hf_path = output_folder / "all_hcurves.hdf5"
    sa_path = output_folder / "all_SaT-variables.pkl"

df = sa_gen.create_sa_table(hf_path)
sa_gen.save_table_to_pkl(df, sa_path)

