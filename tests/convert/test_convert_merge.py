import pathlib

import numpy as np
import pandas as pd
import pytest

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename))
    return SatTable(df)


@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename)
    return DistMagTable(csv_path)


def test_merge(sat_table, dm_table):
    print(
        sat_table.flatten()
    )  # .set_index(['Location', 'APoE (1/n)', 'Site Soil Class']))
    print(dm_table.flatten())  # .set_index(['Location', 'APoE (1/n)']))


sat_grid_expected = [
    ("-34.300~172.900", 25, "I", [0.02, 0.03, 0.4]),
    ("-43.700~169.100", 100, "I", [0.15, 0.32, 0.3]),
    ("-44.700~170.600", 2500, "II", [0.49, 1.07, 0.4]),
    ("-44.700~170.600", 2500, "III", [0.53, 1.15, 0.6]),
]


@pytest.mark.parametrize("location,apoe,site_soil_class,expected", sat_grid_expected)
def test_spot_check_sat_table_grid(
    sat_table, location, apoe, site_soil_class, expected
):
    grid_df = sat_table.grid_location_df()
    filtered_df = grid_df[
        (grid_df.Location == location)
        & (grid_df["APoE (1/n)"] == apoe)
        & (grid_df["Site Soil Class"] == site_soil_class)
    ]
    assert filtered_df["PGA"].values[0] == pytest.approx(expected[0])
    assert filtered_df["Sas"].values[0] == pytest.approx(expected[1])
    assert filtered_df["Tc"].values[0] == pytest.approx(expected[2])


sat_named_expected = [
    ("Akaroa", 25, "I", [0.04, 0.08, 0.3]),
    ("Kaikoura", 100, "I", [0.24, 0.53, 0.3]),
    ("Woodville", 2500, "II", [1.71, 3.69, 0.4]),
    ("Woodville", 2500, "III", [1.62, 3.26, 0.5]),
]


@pytest.mark.parametrize("location,apoe,site_soil_class,expected", sat_named_expected)
def test_spot_check_sat_table_named(
    sat_table, location, apoe, site_soil_class, expected
):
    named_df = sat_table.named_location_df()
    filtered_df = named_df[
        (named_df.Location == location)
        & (named_df["APoE (1/n)"] == apoe)
        & (named_df["Site Soil Class"] == site_soil_class)
    ]

    assert filtered_df["PGA"].values[0] == pytest.approx(expected[0])
    assert filtered_df["Sas"].values[0] == pytest.approx(expected[1])
    assert filtered_df["Tc"].values[0] == pytest.approx(expected[2])


@pytest.mark.parametrize(
    "location,apoe,site_soil_class,expected", sat_named_expected + sat_grid_expected
)
def test_spot_check_sat_table_raw(sat_table, location, apoe, site_soil_class, expected):
    df = sat_table.raw_table
    rec = df.loc[location][f"APoE: 1/{apoe}"][f"Site Soil Class {site_soil_class}"]
    assert rec["PGA"] == pytest.approx(expected[0], 3)
    assert rec["Sas"] == pytest.approx(expected[1])
    assert rec["Tc"] == pytest.approx(expected[2])


dm_expected = [
    ("Akaroa", 25, [np.NaN, 6.3]),
    (
        "Kaikoura",
        100,
        [
            np.NaN,
            7.2,
        ],
    ),
    ("Woodville", 1000, [6.0, 7.8]),
    ("Woodville", 2500, [6.0, 7.9]),
]


@pytest.mark.parametrize("location,apoe,expected", dm_expected)
def test_spot_check_dm_table_raw(dm_table, location, apoe, expected):
    df = dm_table.raw_table
    # print(df)
    # print(location, apoe,)
    rec = df[df["Unnamed: 0"] == location]
    if expected[0] is np.NaN:
        assert isinstance(list(rec["D"])[0], type(np.NaN))
    else:
        assert list(rec["D"])[0] == pytest.approx(expected[0])
    assert list(rec[f"APoE: 1/{apoe}"])[0] == pytest.approx(expected[1])


@pytest.mark.parametrize("location,apoe,expected", dm_expected)
def test_spot_check_dm_table_flat(dm_table, location, apoe, expected):
    df = dm_table.flatten()
    print(df)
    print(
        location,
        apoe,
    )
    rec = df.loc[location, apoe]
    if expected[0] is np.NaN:
        assert isinstance(rec["D"], type(np.NaN))
    else:
        assert rec["D"] == pytest.approx(expected[0])
    assert rec["M"] == pytest.approx(expected[1])
