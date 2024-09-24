import pickle as pkl

import numpy as np

from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

mini = True

if mini:
    hf_name = "mini_hcurves.hdf5"
    sa_name = "mini_SaT-variables"
    dm_name = "mini_D-M-tables"

    site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington"]

else:
    hf_name = "recreated_hcurves.hdf5"
    sa_name = "recreated_SaT-variables"
    dm_name = "recreated_D-M-tables"

    site_list = None

# generate Sa Parameter Tables
sa_gen.create_sa_pkl(hf_name, sa_name, site_list=site_list)

# extract metadata from Sa Parameter Tables
with open(sa_name + ".pkl", "rb") as file:
    df = pkl.load(file)
    site_list, APoEs, site_class_list = dm_gen.return_table_indices(df)

    rps = np.sort([int(APoE.split("/")[1]) for APoE in APoEs])
    APoEs = [f"APoE: 1/{rp}" for rp in rps]

# generate D and M Tables
dm_gen.create_D_and_M_table(site_list, APoEs, dm_name)
