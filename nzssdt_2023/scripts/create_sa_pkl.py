from nzssdt_2023.data_creation import parameter_generation as gen
from nzssdt_2023.data_creation.query_NSHM import hazard_id

hf_name = "hcurves_mini.hdf5"
sa_name = "SaT-variables_mini"

site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington"]

hazard_param = {}
hazard_param["hazard_id"] = hazard_id
hazard_param["site_list"] = site_list

gen.create_sa_pkl(hf_name, sa_name, hazard_param)
