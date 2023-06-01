### NZ Seismic Site Demand Table 2023 (NZSSDT-2023)

This repository contains the NZSSDT data in json form for language portability. It is intended
for use by NZ engineering community for seismic design calculations.

**NB:**
 - the reposotiry includes a simple versioning system for calcluation traceability.
 - data herein is derived from NSHM 2022 (Link) and produced by the Siesmic Risk Working Group (ref ....
 - we include the original data as supplied from SRWG.
 - we also include python scripts for translating from the source dataframe form into the final form.

## Version Manifest

the ![version_list](resources/version_list.json) file desecribes the content of all project versions

## Version 1  - June-2023

This version contains the following files all in the resources folder:

 - **v1/named_locations.json** contains site parammeters for named locations that correspond to the polygons in **polygons.geojson**
 - **v1/location_replacements.json"** contains mappings for a small set of alternate mappgins to be used in location -> polygon lookups.
 - **v1/grid_locations.json** contains the site parameters for NZ at 0,1 degree grid spacing.
 - **v1/major_faults.geojson** contains the main NZ faults using a CRS84 coordinate system*.
 - **v1/polygons.geojson** contains the polygons for use with **named_locations.json** and **location_replacements.json**. This also uses CRS84 coordinate system.

 Use https://geojson.tools to upload and view these geojson files.

```
[
  {
    "version_number": 1,
    "nzshm_model_version": "NSHM_v1.0.4",
    "description": null,
    "conversions": [
      {
        "input_filepath": "input/v1/SaT-variables_v5_corrected-locations.pkl",
        "output_filepath": "v1/named_locations.json"
      },
      {
        "input_filepath": "input/v1/SaT-variables_v5_corrected-locations.pkl",
        "output_filepath": "v1/grid_locations.json"
      },
      {
        "input_filepath": "input/v1/D_and_M_with_floor.csv",
        "output_filepath": "v1/d_and_m.json"
      }
    ],
    "manifest": [
      {
        "filepath": "v1/named_locations.json"
      },
      {
        "filepath": "v1/grid_locations.json"
      },
      {
        "filepath": "v1/d_and_m.json"
      },
      {
        "filepath": "v1/location_replacements.json"
      },
      {
        "filepath": "v1/major_faults.geojson"
      },
      {
        "filepath": "v1/polygons.geojson"
      }
    ],
    "nzshm_common_lib_version": "0.6.0",
    "nzshm_model_lib_version": "0.3.0"
  }
]
```