### NZ Seismic Site Demand Table 2023 (NZSSDT-2023)

[![Build Status](https://github.com/daily-science/nzssdt-2023/actions/workflows/dev.yml/badge.svg)](https://github.com/daily-science/nzssdt-2023/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/daily-science/nzssdt-2023/branch/main/graphs/badge.svg)](https://codecov.io/github/daily-science/nzssdt-2023)

* GitHub: <https://github.com/daily-science/nzssdt-2023>
* Free software: AGPL-3.0-only

This repository contains the NZSSDT data in json form for language portability. It is intended
for use by NZ engineering community for seismic design calculations.

**NB:**

 - data herein is derived from **[NSHM 2022](https:nshm.gms.cri.nz) and was produced by the **Siesmic Risk Working Group** (ref ....)
 - we include a simple versioning system for traceability.
 - we include the original data as supplied from SRWG.
 - we also include python scripts for translating from the source dataframe form into the final form.

## Version 1  - June-2023

This version contains the following files, all located in the [resources/v1](resources/v1) folder:

 - **[named_locations.json](resources/v1/named_locations.json)** contains site parameters for named locations that correspond to the polygons in **polygons.geojson**
 - **[grid_locations.json](resources/v1/grid_locations.json)** contains the site parameters for NZ at 0.1 degree grid spacing.
 - **[location_replacements.json](resources/v1/location_replacements.json)** contains mappings for a small set of alternates to be used with location -> polygon lookups.
 - **[major_faults.geojson](resources/v1/major_faults.geojson)** contains the main NZ faults using a CRS84 coordinate system *.
 - **[polygons.geojson](resources/v1/polygons.geojson)** contains the polygons for use with **named_locations.json** and **location_replacements.json**. This also uses CRS84 coordinate system.

 * Use https://geojson.tools to upload and view these geojson files.


## Manifest

The file **[version_list.json](resources/version_list.json)** describes the contents of each project version.


