"""
This package encapsluates Anne Hulseys' data processing pipeline.

Modules:
 calculate_D_values: get distances from locations to the urban polygons
 query_NSHM: get hazard data from the NSHM hazard API.
 dm_parameter_generation: produces the magnitude and distances values for the parameter table.
 sa_parameter_generation: derives the PGA, Sa,s, and Tc parameters from the NSHM hazard curves.
 NSHM_to_hdf5: helper functions for producing an HDF5 file for the NZSSDT tables
 extract_data: helper functions to read the the NSHM hdf5.
"""
