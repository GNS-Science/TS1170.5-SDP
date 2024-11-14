# Changelog

## [0.5.0] TBD

### Added
 - new `nzssdt_2023.data_creation` package for Annes process steps
 - new `nzssdt_2023.scripts` package for cli scripts
 - mkdocs with some intitial structure and standard NSHM doc pages.
 - new `nzssdt_2023.config` module with ENV option for WORKING_FOLDER, used for intermediate file storage
 - test coverage on `data_creation` package
 - PGA reduction feature (committee update)
 - Td calcs and Tc sig figs (committee update)

### Changed
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

