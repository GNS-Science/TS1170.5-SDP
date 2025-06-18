## Dynamic access to the TS Seismic Demand Parameters

*Python functions to dynamically query the TS tables for use in seismic design*

&nbsp;

These tools allows engineers to:

 - **identify which row** in the TS tables is relevant for a site with a given latitude and longitude 
    - Table 3.1 for locations within the named urban boundaries
	- Table 3.2 for other locations that snap to the nearest grid locations

 - **calculate the distance** from a site to the nearest major fault

 - **retrieve the TS parameters** associated with a given site:
    - for all annual probabilities of exceedance (APoE) and site classes
	- for specific combinations of APoEs and site classes

 - **develop the spectral accelerations** associated with a set of TS parameters
    - a single spectrum for one site class
	- an enveloped spectrum across multiple site class spectra 
	
&nbsp;

### Example usage

```python
latitude, longitude = (-41.25, 174.775)
apoe_n = 500
site_class = "IV"
site_class_list = ["III", "IV", "V"]


from nzssdt_2023.end_user_functions.geospatial_analysis import (
	identify_location_id, 
	calculate_distance_to_fault
)
location_id = identify_location_id(longitude, latitude)
D = calculate_distance_to_fault(longitude, latitude)


from nzssdt_2023.end_user_functions.query_parameters import (
	parameters_by_location_id,
	retrieve_sa_parameters,
	retrieve_md_parameters
)
pga, sas, tc, td = retrieve_sa_parameters(location_id, apoe_n, site_class)
m, d = retrieve_md_parameters(location_id, apoe_n, site_class)
parameters = parameters_by_location_id(location_id)


from nzssdt_2023.end_user_functions.create_spectra import (
	create_enveloped_spectra,
	create_spectrum_from_parameters
)
spectrum = create_spectrum_from_parameters(pga, sas, tc, td)
spectra = create_enveloped_spectra(location_id, apoe_n, site_class_list)
```