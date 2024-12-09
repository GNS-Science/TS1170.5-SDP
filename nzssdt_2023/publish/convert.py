"""Converts the pandas dataframes produced by the pipeline into .json dictionaries"""

from functools import lru_cache
from pathlib import Path
from typing import List, Union

import pandas as pd

from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen


class SatTable:
    def __init__(self, raw_table: pd.DataFrame):
        self.raw_table = raw_table

    def combine_dm_table(self, dm_df: pd.DataFrame):
        return self.flatten().merge(dm_df, how="left", on=["Location", "APoE (1/n)"])

    @lru_cache
    def flatten(self):
        return flatten_sat_df(self.raw_table)

    def named_location_df(self):
        df = self.flatten()
        sites = list(df.Location.unique())
        named_sites = [site for site in sites if "~" not in site]
        return df[df.Location.isin(named_sites)]

    def grid_location_df(self):
        df = self.flatten()
        sites = list(df.Location.unique())
        grid_sites = [site for site in sites if "~" in site]
        return df[df.Location.isin(grid_sites)]


def flatten_sat_df(df: pd.DataFrame):

    df2 = df.stack().stack().stack()  # .reset_index()
    df2 = df2.unstack(level=1).reset_index()

    df2.level_1 = df2.level_1.apply(lambda x: x.replace("Site Class ", ""))
    df2.level_2 = df2.level_2.apply(lambda x: int(x.replace("APoE: 1/", "")))

    return df2.rename(
        columns={
            "level_0": "Location",
            "level_1": "Site Class",
            "level_2": "APoE (1/n)",
        }
    )


def sat_table_json_path(
    root_folder: Union[Path, str], named_sites: bool = True, site_limit=0, combo=False
):
    """get path for json files

    Args:
      named_sites: if True returns SRG sites, False returns lat/lon sites
      site_limit: for test fixtures
    Returns:
      file_path:
    """
    file_name = "_TYPE_locations_combo.json" if combo else "_TYPE_locations.json"

    if site_limit:
        file_name = f"first_{site_limit}" + file_name

    if named_sites:
        return Path(root_folder, file_name.replace("TYPE", "named"))

    else:
        return Path(root_folder, file_name.replace("TYPE", "grid"))


def sat_table_to_json(
    hf_path: Path, version_folder: Union[str, Path], site_limit: int = 0
):
    """Creates sat table and saves to json

    Args:
        hf_path: hdf5 filename, containing the hazard data
        version_folder: version folder to save json to
        site_limit: for test fixtures
    """

    df = sa_gen.create_sa_table(hf_path)
    sat = SatTable(df)

    # SAT named locations
    sat.named_location_df().to_json(
        sat_table_json_path(version_folder, named_sites=True, site_limit=site_limit),
        index=False,
        orient="table",
        indent=2,
        double_precision=3,  # need to confirm that this is as intended for sigfig rounding
    )

    # SAT grid locations
    sat.grid_location_df().to_json(
        sat_table_json_path(version_folder, named_sites=False, site_limit=site_limit),
        index=False,
        orient="table",
        indent=2,
        double_precision=3,  # need to confirm that this is as intended for sigfig rounding
    )


class DistMagTable:
    def __init__(self, raw_table: pd.DataFrame):
        self.raw_table = raw_table

    @lru_cache
    def flatten(self):
        df2 = self.raw_table
        df2["Location"] = df2.index
        df2 = df2.set_index(["Location", "D"]).stack().reset_index()
        df2.level_2 = df2.level_2.apply(lambda x: int(x.replace("APoE: 1/", "")))
        df2 = df2.rename(
            columns={
                0: "M",
                "level_2": "APoE (1/n)",
            }
        )
        return df2.set_index(["Location", "APoE (1/n)"])


def d_and_m_table_to_json(
    version_folder,
    site_list: List[str],
    rp_list: List[int] = constants.DEFAULT_RPS,
    no_cache: bool = False,
    legacy: bool = False,
    site_limit: int = 0,
):
    """Compiles the D and M parameter tables

    Args:
        version_folder: version folder to save json to
        site_list: list of sites of interest
        rp_list    : list of return periods of interest
        no_cache: if True, ignore the cache file
        legacy: if True double rounds magnitudes to match original mean mags from v1 of the workflow.
        site_limit: for building test fixtures
    """
    dm_df = dm_gen.create_D_and_M_df(
        site_list, rp_list=rp_list, no_cache=no_cache, legacy=legacy
    )
    dandm = DistMagTable(dm_df)

    out_path = (
        Path(version_folder, "d_and_m.json")
        if not site_limit
        else Path(version_folder, f"first_{site_limit}_d_and_m.json")
    )
    dandm.flatten().infer_objects().to_json(
        out_path,
        index=True,
        orient="table",
        indent=2,
    )


class AllParameterTable:
    def __init__(self, complete_table: pd.DataFrame):
        self._raw_table = complete_table

    # set up whatever needs to set up here...
    # when flattening we want the following columns:
    # ["M", "D"]
    # ["PGA", "Sas", "Tc", "Td", ]
    # ["PSV", "PGA Floor", "Sas Floor", "PSV Floor", "Td Floor"]
    ### NOTE that "PSV adjustment" is not included. It was just for diagnostics

    def named_location_df(self):
        df = self._raw_table
        sites = list(df.Location.unique())
        named_sites = [site for site in sites if "~" not in site]
        return df[df.Location.isin(named_sites)]

    def grid_location_df(self):
        df = self._raw_table
        sites = list(df.Location.unique())
        grid_sites = [site for site in sites if "~" in site]
        return df[df.Location.isin(grid_sites)]


def to_standard_json(table: pd.DataFrame, filepath: Path):
    table.to_json(
        filepath,
        index=False,
        orient="table",
        indent=2,
        double_precision=3,  # need to confirm that this is as intended for sigfig rounding
    )
