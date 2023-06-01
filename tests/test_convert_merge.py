import pathlib

import pandas as pd
import pytest

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename))
    return SatTable(df)


@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename)
    return DistMagTable(csv_path)


def test_merge(sat_table, dm_table):
    print(
        sat_table.flatten()
    )  # .set_index(['Location', 'APoE (1/n)', 'Site Soil Class']))
    print(dm_table.flatten())  # .set_index(['Location', 'APoE (1/n)']))


sat_named_expected = [
    ("Akaroa", 25, "I", [0.04, 0.08, 0.3]),
    ("Kaikoura", 100, "I", [0.24, 0.53, 0.3]),
    ("Woodville", 2500, "II", [1.71, 3.69, 0.4]),
    ("Woodville", 2500, "III", [1.62, 3.26, 0.5]),
]


@pytest.mark.parametrize("location,apoe,site_soil_class,expected", sat_named_expected)
def test_spot_check_sat_table(sat_table, location, apoe, site_soil_class, expected):
    named_df = sat_table.named_location_df()

    assert named_df.loc[location, apoe, site_soil_class]["PGA"] == pytest.approx(
        expected[0]
    )
    assert named_df.loc[location, apoe, site_soil_class]["Sas"] == pytest.approx(
        expected[1]
    )
    assert named_df.loc[location, apoe, site_soil_class]["Tc"] == pytest.approx(
        expected[2]
    )


@pytest.mark.parametrize("location,apoe,site_soil_class,expected", sat_named_expected)
def test_spot_check_sat_table_raw(sat_table, location, apoe, site_soil_class, expected):
    df = sat_table.raw_table
    rec = df.loc[location][f"APoE: 1/{apoe}"][f"Site Soil Class {site_soil_class}"]
    assert rec["PGA"] == pytest.approx(expected[0])
    assert rec["Sas"] == pytest.approx(expected[1])
    assert rec["Tc"] == pytest.approx(expected[2])
