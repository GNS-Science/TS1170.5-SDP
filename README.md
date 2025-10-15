# New Zealand | Aotearoa Seismic Site Demand Table 2023 (NZSSDT-2023)

[![Build Status](https://github.com/GNS-Science/TS1170.5-SDP/actions/workflows/dev.yml/badge.svg)](https://github.com/GNS-Science/TS1170.5-SDP/actions/workflows/dev.yml)
[![codecov](https://app.codecov.io/github/GNS-Science/TS1170.5-SDP/branch/main/graphs/badge.svg)](https://app.codecov.io/github/GNS-Science/TS1170.5-SDP)

* Documentation: <https://GNS-Science.github.io/TS1170.5-SDP>
* GitHub: <https://github.com/GNS-Science/TS1170.5-SDP>

## About TS1170.5

**TS1170.5-SDP** stands for **NZ Technical Standard 1170.5 Seismic Demand Parameters**. 

This project contains the source code and configuration used to 
produce the tables published as part of TS1170.5:2024 DRAFT by Standards NZ. These tables are derived from the **[NZ National Seismic Hazard Model 2022](https://www.gns.cri.nz/research-projects/national-seismic-hazard-model/)** **Seismic Risk Working Group** . 

For more about TS1170.5, please see:

 - [NZSEE:Overview of TS 1170.5:2025 and changes from NZS 1170.5:2004](https://bulletin.nzsee.org.nz/index.php/bnzsee/article/view/1695)
 - [TS1170.5:2024 DRAFT (PDF)](https://consultations.standards.govt.nz/draft-standards/ts1170-5-public-consultation/user_uploads/20240215-ts-1170.5---public-comment-draft_v2.pdf)
 
## About this repository
This repository is also intended for use by NZ engineering community for seismic design calculations. For future revisions, it captures the entire processing pipeline we used to produce the TS1170.5-SDP design tables.

This project includes:

 - [User Orientation](./docs/user_orientation/index.md) for more about the Seismic Demand Parameters (SDP) terminology and the organisation of the SDP tables.
 - the SDP tables intended for publication by Standards NZ in CSV and PDF form. See [reports/v2](https://github.com/GNS-Science/TS1170.5-SDP/blob/main/reports/v2).
 - the published artefacts, with a versioning system for traceability. See [Versions](./docs/versions.md).
 - the original data as supplied from SRWG. See [resources/v2](https://github.com/GNS-Science/TS1170.5-SDP/blob/main/resources/v2).
 - [python code](./docs/api/index.md) for translating from the source dataframe form into the final formats.
 - documentation about the [production process](./docs/scripts/pipeline_cli.md) (aka the pipeline).
 - Python [functions for end-users](./docs/end_user_functions/index.md) to simplify use of the published datasets.



