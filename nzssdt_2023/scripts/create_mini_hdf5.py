from nzssdt_2023.data_creation import NSHM_to_hdf5 as to_hdf5
from nzssdt_2023.data_creation import query_NSHM as q_haz
from nzssdt_2023.data_creation.query_NSHM import (
    agg_list,
    hazard_id,
    imt_list,
    vs30_list,
)

hf_name = "hcurves_mini.hdf5"


# query NSHM
site_list = ["Auckland", "Christchurch", "Dunedin", "Wellington"]
sites = q_haz.create_sites_df(site_list=site_list)

hcurves, imtl_list = q_haz.retrieve_hazard_curves(
    sites, vs30_list, imt_list, agg_list, hazard_id
)

# prep and save hcurves to hdf5
data = to_hdf5.create_hcurve_dictionary(
    sites, vs30_list, imt_list, imtl_list, agg_list, hcurves
)

data = to_hdf5.add_uniform_hazard_spectra(data)
to_hdf5.save_hdf(hf_name, data)
