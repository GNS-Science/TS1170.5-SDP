"""Converts the pandas dataframes produced by the pipeline into .json dictionaries"""

from functools import lru_cache
from pathlib import Path
from typing import Union

import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

APoEs = [f"APoE: 1/{rp}" for rp in constants.DEFAULT_RPS]
site_class_labels = [f"Site Class {key}" for key in constants.SITE_CLASSES]

parameters = ["PGA", "Sas", "Tc"]  # Td will be added after this workflow is established


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

    df3 = param_dfs[0].merge(param_dfs[1]).merge(param_dfs[2])
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

