# Changelog

## [0.7.0]

### Added
 - new .geojson of the lat/lon grid points
 - new package for creating the deliverable for Standards New Zealand

## [0.6.0] 2025-03-26 

### Added
 - new `nzssdt_2023.end_user_functions` package for querying TS tables and producing response spectra
 - complete missing documentation for `nzssdt_2023.data_creation` package
 - HomeA/HomeB for documentation review

## [0.5.0] 2025-03-20 

### Added
 - new `nzssdt_2023.data_creation` package for Annes process steps
 - new `nzssdt_2023.scripts` package for cli scripts
 - mkdocs with some intitial structure and standard NSHM doc pages.
 - new `nzssdt_2023.config` module with ENV option for WORKING_FOLDER, used for intermediate file storage
 - test coverage on `data_creation` package
 - PGA reduction feature (committee update)
 - Td calcs and Tc sig figs (committee update)
 - new test using  external test fixtures for committe adjustments (thanks Chris de la Torre & Tom Francis)
 - named report includes macronised maori place names, with ascii altenate for better search support
 - script/publish_cli now implements report and publish commands used to build artefacts
 - new json artefacts in `resources/v2`
 - new report artefacts in `reports/v2`
 - PDF report value tests to ensure layout display the data correctly.
 - reports included in VersionInfo json
 - added the Version 2 geojson artefacts with 
   `poetry run pipeline 04-geometry --verbose 2`
 - added V2 to the version_list with 
   `poetry run pipeline 06-publish 2 NSHM_v1.0.4 "Seismic Demand Parameters version 2, incorporating feedback from reviewers."`
 - added doc publiscation workflow
 
 ## Changed
 - migrated report.py into new `publish` package
 - minor typing improvents
 - renamed `nzssdt_2023\cli.py` -> `nzssdt_2023\scripts\publish_cli.py`
 - refactor `resources\input` to `resources\pipeline`
 - migrated various datafiles from into resources or /WORKING_FOLDER
 - more use of pathlib
 - more use of logging
 - better docstrings for `convert`, `publish`, `build` & `versioning`
 - moved `mean_magnitudes` module to `data_creation` package
 - `mean_magnitudes` functions create DataFrame objects in form expected by functions in `dm_parameter_generation`
 - mean magnitude csv files moved from RESOURCES_FOLDER to WORKING_FOLDER and removed from repo
 - mean magnitude csv files are on demand cache
 - `extract_m_values` function will generate mean magnitude csv files if needed or requested
 - default `config.WORKING_FOLDER` uses platform independent tmp folder
 - we no longer use pkl files for intermediate storage, but hdf5
 - minor v2 report layout changes
 - use latest `nzshm-common` from pypi
 - v2 json form includes D,M with other parameters in one file, so `d_and_m.json` is no longer published
 - removed redundant decimal places in artefacts
 - `pipeline_cli` commands get numeric prefix
 - minor pipeline improvements
 - revised pipeline_cli docs
 - simplified mkdocs index structure


## [0.4.0] 2024-09-11

### Added
 - `mean_magnitudes` package with calculations using disaggregations retrieved via `toshi-hazard-post`

## [0.3.0] 2024-02-15

### Changed
 - fixed APOE_MAPPINGS in report.py so that g/2500 tables are included
 - updated the g/f2500 reports wiht correct table names

## [0.2.0] 2024-02-15

### Changed
 - modified report.py to update table names
 - updated README with reports section
 - model version is NSHM_v1.0.4
 - updated nzshm_model and nzshm_common to latest versions

### Added
 - CHANGELOG.md
 - setup versioning with bump2version

## [0.1.0] 2023-06-05

 - initial release for Standards NZ

