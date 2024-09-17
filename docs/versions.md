## Version 1  - June-2023

*migrated from old README.md*

This version contains the following files, all located in the [resources/v1](resources/v1) folder:

 - **[named_locations.json](resources/v1/named_locations.json)** contains site parameters for named locations that correspond to the polygons in **urban_area_polygons.geojson**
 - **[grid_locations.json](resources/v1/grid_locations.json)** contains the site parameters for NZ at 0.1 degree grid spacing.
 - **[location_replacements.json](resources/v1/location_replacements.json)** contains mappings for a small set of alternates to be used with location -> polygon lookups.
 - **[major_faults.geojson](resources/v1/major_faults.geojson)** contains the main NZ faults using a CRS84 coordinate system *.
 - **[urban_area_polygons.geojson](resources/v1/urban_area_polygons.geojson)** contains the polygons for use with **named_locations.json** and **location_replacements.json**. This also uses CRS84 coordinate system.

 * Use https://geojson.tools to upload and view these geojson files.
