"""
Complete pipeline from NSHM to pdf (using new formatting)

"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER
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


def hf_filepath(site_limit: int = 0, working_folder: Path = working_folder):
    return (
        working_folder / f"first_{site_limit * 2}_hcurves.hdf5"
        if site_limit
        else working_folder / "all_hcurves.hdf5"
    )


# TODO: is this redundant, see NSHM_to_hdf5.query_NSHM_to_hdf5
# we want index but also the complete df, so split this and then we can pass sites_df to get_hazard_curves etc
def get_site_list(site_limit: int = 0):
    """
    extract relevant sites from nzshm_common sites and named and gridded.
    constrained by site-limit set
    """
    return pd.concat(
        [
            create_sites_df(site_limit=site_limit),
            create_sites_df(named_sites=False, site_limit=site_limit),
        ]
    )


def get_hazard_curves(
    site_list: List[str], site_limit: int = 0, hazard_id: str = "NSHM_v1.0.4"
):
    """Retrieve the NSHM hazard curves into an HDF5 file into the working folder.

    Args:
        site_list: the list of site names.
        site_limit: the maximum number of sites to retriece.
        hazard_id: the hazard_id.
    """
    hf_path = hf_filepath(site_limit=site_limit)
    log.info(f"building hdf5 for {hazard_id} with {site_limit} sites")
    query_NSHM_to_hdf5(
        hf_path, hazard_id=hazard_id, site_list=site_list, site_limit=site_limit
    )


def get_resources_version_path(version: str):
    """
    Get the version folder for the given version.

    Args:
        version: the version string
    """
    return Path(RESOURCES_FOLDER, f"v{version}")


def build_json_tables(
    hf_path: Path,
    site_list: List[str],
    version: str,
    site_limit: int = 0,
    overwrite_json: bool = True,
):
    """
    Build the SA and D_and_M tables and write them to json files.

    Args:
        hf_path: the path to the hdf5 file
        site_list: the list of site names
        version: the version string
        site_limit: the number of sites to limit to
        overwrite_json: whether to overwrite existing json files
    """
    version_folder = get_resources_version_path(version)

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


def create_geojsons(version: str, overwrite: bool = False):
    """
    Create the geojson files for the urban area polygons and major faults.

    Args:
        version: the version string
        override: whether to override existing files
    """
    output_folder = get_resources_version_path(version)
    # pipeline_folder = Path(RESOURCES_FOLDER, "pipeline" ,  f"v{version}")
    polygons_path = output_folder / "urban_area_polygons.geojson"
    faults_path = output_folder / "major_faults.geojson"
    grid_path = output_folder / "grid_points.geojson"

    # write geojson files to resources
    create_geojson_files(polygons_path, faults_path, grid_path, override=overwrite)


def create_parameter_tables(
    version: str,
    hazard_id: str,
    site_limit: int = 0,
    no_cache: bool = False,
    overwrite_json: bool = True,
):
    """
    Create and save the parameter tables for the given version and hazard_id.

    This will also fetch the hazard curves if needed.

    Args:
        version: the version string
        hazard_id: the hazard_id string
        site_limit: the number of sites to limit to
        no_cache: whether to ignore the cache
        overwrite_json: whether to overwrite existing json files
    """

    hf_path = hf_filepath(site_limit=site_limit)

    sites_df = get_site_list(site_limit=site_limit)

    # query NSHM,
    if no_cache | (not hf_path.exists()):
        get_hazard_curves(
            site_list=sites_df, site_limit=site_limit, hazard_id=hazard_id
        )

    # build the tables
    sites = sites_df.index.tolist()
    build_json_tables(hf_path, sites, version, site_limit, overwrite_json)


if __name__ == "__main__":

    create_parameter_tables(
        version="cbc", site_limit=5, no_cache=True, overwrite_json=True
    )
