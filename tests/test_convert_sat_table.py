import pathlib

import pandas as pd
import pytest

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import SatTable


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename))
    return SatTable(df)


def test_convert_sat_table(sat_table):
    flat = sat_table.flatten()
    assert len(list(flat.index)) == 166068


def test_sat_table_named(sat_table):
    print(sat_table.flatten())
    df = sat_table.named_location_df()
    assert len(list(df.index)) == 8988


def test_sat_table_grid(sat_table):
    df = sat_table.grid_location_df()
    assert len(list(df.index)) == 157080  # 166068 - 8988


def test_sat_table_components(sat_table):
    df = sat_table.flatten()
    df_named = sat_table.named_location_df()
    df_grid = sat_table.grid_location_df()
    assert len(list(df.index)) == len(list(df_named.index)) + len(list(df_grid.index))
