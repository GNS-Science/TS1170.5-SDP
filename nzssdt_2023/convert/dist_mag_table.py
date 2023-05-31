import pathlib
from functools import lru_cache
from typing import Union

import pandas as pd


class DistMagTable:
    def __init__(self, csv_path: Union[str, pathlib.Path]):
        self.csv_path = csv_path
        if not pathlib.Path(csv_path).exists():
            raise ValueError("Invalid csv path: {csv_path}")
        self.raw_table = pd.read_csv(self.csv_path)

    @lru_cache
    def flatten(self):
        df2 = self.raw_table.rename(columns={"Unnamed: 0": "Location"})
        df2 = df2.set_index(["Location", "D"]).stack().reset_index()
        df2.level_2 = df2.level_2.apply(lambda x: int(x.replace("APoE: 1/", "")))
        df2 = df2.rename(
            columns={
                0: "M",
                "level_2": "APoE (1/n)",
            }
        )
        return df2.set_index(["Location", "APoE (1/n)"])
