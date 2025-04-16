## Project structure:

 - The file **[version_list.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/version_list.json)**
   describes the contents of each project version.
 - The folder **[resources](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources)**
   contains the original data supplied by SRWG, and the results in json and geojson form. 
 - The folder  **[reports](https://github.com/GNS-Science/nzssdt-2023/blob/main/reports)**
   contains the PDF tables for inclusion on the TS1170.5 Techcnial Standards document and CSV versions of these tables.
 - The folder  **[deliverables](https://github.com/GNS-Science/nzssdt-2023/tree/main/deliverables)**
   contains the final deliverables for use by Standards NZ.
 

## Version 1  - June-2023

This version contains the following files, all located in the [resources/v1](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1) folder:

 - **[named_locations.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/named_locations.json)** contains site parameters for named locations that correspond to the polygons in **urban_area_polygons.geojson**
 - **[grid_locations.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/grid_locations.json)** contains the site parameters for NZ at 0.1 degree grid spacing.
 - **[location_replacements.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/location_replacements.json)** contains mappings for a small set of alternates to be used with location -> polygon lookups.
 - **[major_faults.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/major_faults.geojson)** contains the main NZ faults using a CRS84 coordinate system *.
 - **[urban_area_polygons.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/urban_area_polygons.geojson)** contains the polygons for use with **named_locations.json** and **location_replacements.json**. This also uses CRS84 coordinate system.

 * Use https://geojson.tools to upload and view these geojson files.

## Version 2 -  March 2025

contains al the above and .... a bit m