"""
This package encapsulates Anne Hulsey's data processing pipeline.

Modules:
 constants: defined constants for this module
 query_NSHM: get hazard data from the NSHM hazard API.
 NSHM_to_hdf5: helper functions for saving hazard data as an HDF5 file.
 extract_data: helper functions to read the the NSHM hdf5.
 sa_parameter_generation: derives the PGA, Sa,s, and Tc parameters from the NSHM hazard curves.
 dm_parameter_generation: produces the magnitude and distances values for the parameter table.
 mean_magnitudes: retrieves magnitude data from the NSHM hazard API
 gis_data: geospatial analysis for the distance to faults
 util: helper function for formatting the latitude and longitude labels
"""
