## Project structure:

 - The file **[version_list.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/version_list.json)**
   describes the contents of each project version.
 - The folder **[resources](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources)**
   contains the original data supplied by SRWG, and the results in json and geojson form. 
   _The geojson files can be uploaded and viewed at [https://geojson.tools](https://geojson.tools)._

 - The folder  **[reports](https://github.com/GNS-Science/nzssdt-2023/blob/main/reports)**
   contains the PDF tables for inclusion on the TS1170.5 Techcnial Standards document and CSV versions of these tables.
 - The folder  **[deliverables](https://github.com/GNS-Science/nzssdt-2023/tree/main/deliverables)**
   contains the final deliverables for use by Standards NZ.
 

## Version 1  - June 2023

This version contains the following files, all located in the [resources/v1](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1) folder:

 - **[named_locations.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/named_locations.json)** contains the acceleration spectra-related site parameters for the named locations that correspond to the polygons in the **urban_area_polygons.geojson**
 - **[location_replacements.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/location_replacements.json)** contains mappings for a small set of named locations for which the parameter values are superceded other named locations.
 - **[grid_locations.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/grid_locations.json)** contains the acceleration spectra-related site parameters that correspond to a 0.1 lat/lon degree grid spacing across New Zealand.
 - **[d_and_m.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/d_and_m.json)** contains the d and m site parameters for all locations (both named and grid spacing).
 - **[urban_area_polygons.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/urban_area_polygons.geojson)** contains the polygons for use with the **named_locations.json**, using the CRS84 coordinate system.
 - **[major_faults.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/major_faults.geojson)** contains the major NZ faults using the CRS84 coordinate system.
 
## Version 2 -  March 2025

This version contains the following files, all located in the [resources/v2](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v2) folder:

 - **[named_locations_combo.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v2/named_locations_combo.json)** contains all the site parameters for the named locations that correspond to the polygons in the **urban_area_polygons.geojson**
 - **[grid_locations_combo.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v2/grid_locations_combo.json)** contains all the site parameters that correspond to a 0.1 lat/lon degree grid spacing across New Zealand.
 - **[urban_area_polygons.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/urban_area_polygons.geojson)** contains the polygons for use with the **named_locations_combo.json**, using the CRS84 coordinate system.
 - **[grid_points.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/grid_points.geojson)** contains the grid points for use with the **grid_locations_combo.json**, using the CRS84 coordinate system.
 - **[major_faults.geojson](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/v1/major_faults.geojson)** contains the major NZ faults using the CRS84 coordinate system.
