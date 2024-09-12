from nzssdt_2023 import *

hf_name = 'hcurves_mini.hdf5'

site_list = ['Auckland','Christchurch','Dunedin','Wellington']
sites = create_sites_df(site_list=site_list)

vs30_list = [275,400]
imt_list  = ['SA(0.5)','SA(1.0)']
agg_list  = ['mean','0.9']

hcurves,imtl_list = retrieve_hazard_curves(sites,vs30_list,imt_list,agg_list,hazard_id)
data = create_hcurve_dictionary(sites,vs30_list,imt_list,imtl_list,agg_list,hcurves)
save_hdf(hf_name, data)
