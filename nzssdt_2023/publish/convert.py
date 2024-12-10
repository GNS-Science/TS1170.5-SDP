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
        flat = self.flatten()
        return flat.join(dm_df, how="left", on=["Location", "APoE (1/n)"])

    @lru_cache
    def flatten(self):
        return OG_flatten_sat_df(self.raw_table)

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


def OG_flatten_sat_df(df: pd.DataFrame):
    parameters = list(df.columns.levels[2])
    parameters.remove("PSV adjustment")

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

    df3 = param_dfs[0]
    for idx in range(1, len(parameters)):
        df3 = df3.merge(param_dfs[idx])

    df3.level_2 = df3.level_2.apply(lambda x: x.replace("Site Class ", ""))
    df3.level_3 = df3.level_3.apply(lambda x: int(x.replace("APoE: 1/", "")))

    df3 = df3.rename(
        columns={
            "level_0": "Location",
            "level_2": "Site Class",
            "level_3": "APoE (1/n)",
        }
    ).sort_values(by=["APoE (1/n)", "Site Class"])
    return df3


def flatten_sat_df(df: pd.DataFrame):
    """
    Unfortunatley this solution does not retain the oroginal dort order of the dataframe
    maybe this is resolved in pandas 2.2 but we're stuck with 2.03 for now.

    So for now, we're using OG_flatten_sat_df() instead.
    """
    df2 = df.stack().stack().stack()
    df2 = df2.unstack(
        level=1, sort=False
    ).reset_index()  # not supported yet - will it work

    df2.level_1 = df2.level_1.apply(lambda x: x.replace("Site Class ", ""))
    df2.level_2 = df2.level_2.apply(lambda x: int(x.replace("APoE: 1/", "")))

    df2 = df2.rename(
        columns={
            "level_0": "Location",
            "level_1": "Site Class",
            "level_2": "APoE (1/n)",
        }
    ).sort_values(by=["APoE (1/n)", "Site Class"])
    return df2


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
    file_name = "TYPE_locations_combo.json" if combo else "TYPE_locations.json"

    if site_limit:
        file_name = f"first_{site_limit}_" + file_name

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
    table.infer_objects().to_json(
        filepath,
        index=False,
        orient="table",
        indent=2,
        double_precision=3,
    )
