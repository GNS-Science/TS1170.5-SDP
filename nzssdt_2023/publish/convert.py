"""Converts the pandas dataframes produced by the pipeline into .json dictionaries"""

from functools import lru_cache
from pathlib import Path
from typing import List, Union

import pandas as pd

from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

parameters = [
    "PGA",
    "Sas",
    "Tc",
    "Td",
]


class SatTable:
    def __init__(self, raw_table: pd.DataFrame):
        self.raw_table = raw_table

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
    df2 = df.stack().stack().stack().reset_index()
    param_dfs = []
    for param_column in parameters:
        param_dfs.append(
            df2[df2.level_1 == param_column]
            .drop(columns=["level_1"])
            .rename(columns={0: param_column})
            .reset_index()
            .drop(columns=["index"])
        )

    df3 = param_dfs[0].merge(param_dfs[1]).merge(param_dfs[2]).merge(param_dfs[3])
    df3.level_2 = df3.level_2.apply(lambda x: x.replace("Site Class ", ""))
    df3.level_3 = df3.level_3.apply(lambda x: int(x.replace("APoE: 1/", "")))
    df3 = df3.rename(
        columns={
            "level_0": "Location",
            "level_2": "Site Class",
            "level_3": "APoE (1/n)",
        }
    )
    return df3.sort_values(by=["APoE (1/n)", "Site Class"])


def sat_table_to_json(hf_path: Path, version_folder: Union[str, Path]):
    """Creates sat table and saves to json

    Args:
        hf_path: hdf5 filename, containing the hazard data
        version_folder: version folder to save json to

    """

    df = sa_gen.create_sa_table(hf_path)
    sat = SatTable(df)

    # SAT named locations
    out_path = Path(version_folder, "named_locations.json")
    sat.named_location_df().to_json(
        out_path,
        index=False,
        orient="table",
        indent=2,
        double_precision=3,  # need to confirm that this is as intended for sigfig rounding
    )

    # SAT grid locations
    out_path = Path(version_folder, "grid_locations.json")
    sat.grid_location_df().to_json(
        out_path,
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
):
    """Compiles the D and M parameter tables

    Args:
        version_folder: version folder to save json to
        site_list: list of sites of interest
        rp_list    : list of return periods of interest
        no_cache: if True, ignore the cache file
        legacy: if True double rounds magnitudes to match original mean mags from v1 of the workflow.

    """
    dm_df = dm_gen.create_D_and_M_df(
        site_list, rp_list=rp_list, no_cache=no_cache, legacy=legacy
    )
    dandm = DistMagTable(dm_df)

    out_path = Path(version_folder, "d_and_m.json")
    dandm.flatten().infer_objects().to_json(
        out_path,
        index=True,
        orient="table",
        indent=2,
    )
