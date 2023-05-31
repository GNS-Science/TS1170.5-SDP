import pathlib

import pandas as pd
import pytest

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "input", filename))
    return SatTable(df)


@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(RESOURCES_FOLDER, "input", filename)
    return DistMagTable(csv_path)


def test_merge(sat_table, dm_table):
    print(
        sat_table.flatten()
    )  # .set_index(['Location', 'APoE (1/n)', 'Site Soil Class']))
    print(dm_table.flatten())  # .set_index(['Location', 'APoE (1/n)']))
