## Dynamic access to the TS Seismic Demand Parameters

*Python functions to dynamically query the TS tables for use in seismic design*

This set of functions allows engineers to:

 - identify which TS table is relevant for a site with a given latitude and longitude 
    - Table 3.1 for locations within the named urban boundaries
	- Table 3.2 for other locations that snap to the nearest grid locations
	
 - retrieve the TS parameters associated with a given site:
    - for all annual probabilities of exceedance (APoE) and site classes
	- for specific combinations of APoEs and site classes
	
 - calculate the distance from a site to the nearest major fault
 
 - develop the spectral accelerations associated with a set of TS parameters
    - a single spectrum for one site class
	- an enveloped spectrum across multiple site class spectra 