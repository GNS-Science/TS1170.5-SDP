## For Seismic Engineers

*Describe the resources & artefacts, versioning and how these relate to NSHM and to the NZ Standard Specifications.*

This repository contains the NZSSDT data in json form for language portability. It is intended
for use by NZ engineering community for seismic design calculations.

**NB:**

 - data herein is derived from the **[NZ National Seismic Hazard Model 2022](https://www.gns.cri.nz/research-projects/national-seismic-hazard-model/)** and was produced by the **Siesmic Risk Working Group** (ref ....)
 - we include a simple versioning system for traceability.
 - we include the original data as supplied from SRWG.
 - we also include python scripts for translating from the source dataframe form into the final form.


### PDF/CSV reports

The tables intended for publication by Standards NZ are located in [reports/v1](https://github.com/GNS-Science/nzssdt-2023/blob/main/reports) folder:

 - tables are provided in CSV and PDF form.
 - tables are produced using nzsddt_20203/report.py


### Manifest

The file **[version_list.json](https://github.com/GNS-Science/nzssdt-2023/blob/main/resources/version_list.json)** describes the contents of each project version.


## For NSHM and SRWG members

See the process documentation