"""
Complete pipeline from NSHM to pdf (using new formatting)

"""

import logging
import os
from pathlib import Path, PurePath

import pandas as pd

from nzssdt_2023.config import WORKING_FOLDER
from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen
from nzssdt_2023.data_creation.gis_data import create_geojson_files
from nzssdt_2023.data_creation.NSHM_to_hdf5 import query_NSHM_to_hdf5
from nzssdt_2023.data_creation.query_NSHM import create_sites_df
from nzssdt_2023.publish.convert import (
    AllParameterTable,
    DistMagTable,
    SatTable,
    sat_table_json_path,
    to_standard_json,
)

# configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("toshi_hazard_store").setLevel("ERROR")

log = logging.getLogger(__name__)

working_folder = Path(WORKING_FOLDER)


def create_parameter_tables(
    version: str, site_limit: int = 0, no_cache: bool = False, overwrite_json=True
):

    version_folder = Path(
        PurePath(os.path.realpath(__file__)).parent.parent.parent,
        "resources",
        f"v_{version}",
    )

    hf_path = (
        working_folder / f"first_{site_limit * 2}_hcurves.hdf5"
        if site_limit
        else working_folder / "all_hcurves.hdf5"
    )

    # site_list: Optional[list[str]] = None
    site_list = list(
        pd.concat(
            [
                create_sites_df(site_limit=site_limit),
                create_sites_df(named_sites=False, site_limit=site_limit),
            ]
        ).index
    )

    # query NSM,
    if no_cache | (not hf_path.exists()):
        log.info(f"building hdf5 for {site_limit} sites")
        query_NSHM_to_hdf5(hf_path, site_list=site_list, site_limit=site_limit)

    # output paths
    named_path = sat_table_json_path(
        version_folder, named_sites=True, site_limit=site_limit, combo=True
    )
    gridded_path = sat_table_json_path(
        version_folder, named_sites=False, site_limit=site_limit, combo=True
    )

    if overwrite_json | (not named_path.exists()) | (not gridded_path.exists()):

        log.info("build the SA and D_and_M tables")
        sat_df = sa_gen.create_sa_table(hf_path)
        dm_df = DistMagTable(
            dm_gen.create_D_and_M_df(site_list, rp_list=constants.DEFAULT_RPS)
        ).flatten()

        log.info("combine the tables")
        combined_df = SatTable(sat_df).combine_dm_table(dm_df)
        complete = AllParameterTable(combined_df)

        # write the files
        to_standard_json(complete.named_location_df(), named_path)
        to_standard_json(complete.grid_location_df(), gridded_path)
        log.info(f"wrote json files to {named_path.parent}")


if __name__ == "__main__":

    create_parameter_tables(
        version="cbc", site_limit=5, no_cache=True, overwrite_json=True
    )
