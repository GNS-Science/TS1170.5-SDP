"""
Superceded by create_parameter_tables

TODO: delete??
"""
from nzssdt_2023.data_creation import sa_parameter_generation as gen

hf_name = "mini_hcurves.hdf5"
sa_name = "mini_SaT-variables"

site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington"]

gen.create_sa_pkl(hf_name, sa_name, site_list=site_list)
