#!python main.py
"""Copied from Anne Hulsey's example"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.data_creation import constants

APoEs = [f"APoE: 1/{rp}" for rp in constants.DEFAULT_RPS]
site_class_labels = [
    f"Site Soil Class {key}" for key in constants.SITE_CLASSES
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
    return df3.sort_values(by=["APoE (1/n)", "Site Soil Class"])


class SatTable:
    def __init__(self, raw_table: pd.DataFrame):
        self.raw_table = raw_table

    @lru_cache
    def flatten(self):
        return flatten_df(self.raw_table)  # .sort_index()

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


def one_off_export_for_cdlt():
    filename = "WORKING/all_SaT-variables.pkl"
    df = pd.read_pickle(Path(filename))
    sat = SatTable(df)

    # SAT named
    out_path = Path("WORKING/named_locations_not_rounded.json")
    sat.named_location_df().to_json(
        out_path,
        index=False,
        orient="table",
        indent=2,
        double_precision=12,
    )


if __name__ == "__main__":
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(Path(RESOURCES_FOLDER, filename))

    sat_table = SatTable(df)
    flat = sat_table.flatten()

    flat.to_json(
        Path(RESOURCES_FOLDER, "flat_table_v5.json.zip"),
        index=False,
        orient="table",
        indent=2,
    )
