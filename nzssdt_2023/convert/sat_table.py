#!python main.py
"""Copied from Anne Hulsey's example"""

import pathlib
from functools import lru_cache

import pandas as pd

from nzssdt_2023 import RESOURCES_FOLDER

APoEs = [f"APoE: 1/{rp}" for rp in [25, 100, 250, 500, 1000, 2500]]
site_class_labels = [
    f"Site Soil Class {n}" for n in ["I", "II", "III", "IV", "V", "VI"]
]
parameters = ["PGA", "Sas", "Tc"]


def flatten_df(df: pd.DataFrame):
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
    df3.level_2 = df3.level_2.apply(lambda x: x.replace("Site Soil Class ", ""))
    df3.level_3 = df3.level_3.apply(lambda x: int(x.replace("APoE: 1/", "")))
    df3 = df3.rename(
        columns={
            "level_0": "Location",
            "level_2": "Site Soil Class",
            "level_3": "APoE (1/n)",
        }
    )
    return df3.set_index(["Location", "APoE (1/n)", "Site Soil Class"])


class SatTable:
    def __init__(self, raw_table: pd.DataFrame):
        self.raw_table = raw_table

    @lru_cache
    def flatten(self):
        return flatten_df(self.raw_table).sort_index()

    def named_location_df(self):
        df = self.flatten()
        sites = list(df.index.get_level_values("Location"))
        # print(sites, len(sites))
        named_sites = [site for site in sites if "~" not in site]
        return df[df.index.get_level_values("Location").isin(named_sites)]

    def grid_location_df(self):
        df = self.flatten()
        sites = list(df.index.get_level_values("Location"))
        grid_sites = [site for site in sites if "~" in site]
        return df[df.index.get_level_values("Location").isin(grid_sites)]


if __name__ == "__main__":
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, filename))

    sat_table = SatTable(df)
    flat = sat_table.flatten()

    flat.to_json(
        pathlib.Path(RESOURCES_FOLDER, "flat_table_v5.json.zip"),
        index=False,
        orient="table",
        indent=2,
    )
