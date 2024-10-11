import json
from collections import namedtuple
from pathlib import Path

import numpy as np
import pandas as pd
import pandas.testing
import pytest
import toshi_hazard_store.query as query
from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.model import AggregationEnum, ProbabilityEnum

from nzssdt_2023.data_creation.mean_magnitudes import (
    frequency_to_poe,
    get_mean_mag_df,
    poe_to_rp,
    read_mean_mag_df,
    site_name_to_coded_location,
)


def lat_lon(id):
    return (location_by_id(id)["latitude"], location_by_id(id)["longitude"])


NSITES = 10
HAZARD_AGG = AggregationEnum.MEAN
HAZARD_ID = "NSHM_v1.0.4_mag"
POES = [
    ProbabilityEnum._2_PCT_IN_50YRS,
    ProbabilityEnum._5_PCT_IN_50YRS,
    ProbabilityEnum._10_PCT_IN_50YRS,
    ProbabilityEnum._18_PCT_IN_50YRS,
    ProbabilityEnum._39_PCT_IN_50YRS,
    ProbabilityEnum._63_PCT_IN_50YRS,
    ProbabilityEnum._86_PCT_IN_50YRS,
]
APOES = [
    "APoE: 1/25",
    "APoE: 1/50",
    "APoE: 1/100",
    "APoE: 1/250",
    "APoE: 1/500",
    "APoE: 1/1000",
    "APoE: 1/2500",
]
LOCATION_IDS = [_id for _id in LOCATION_LISTS["SRWG214"]["locations"]]
LOCATIONS = [CodedLocation(*lat_lon(_id), 0.001) for _id in LOCATION_IDS][0:NSITES]

Disagg = namedtuple(
    "Disagg",
    [
        "disaggs",
        "bins",
        "nloc_001",
        "lat",
        "lon",
        "vs30",
        "probability",
        "imt",
        "shaking_level",
    ],
)


def raw_mag_to_df(raw_df, site_list, APoEs):
    """compile magnitudes dataframe into a more manageable dataframe

    Args:
        raw_df: dataframe from the initial NSHM query of magnitudes
        site_list: list of sites included in the sa tables
        APoEs    : list of APoEs included in the sa tables

    Returns:
        df: dataframe with rows: sites and columns: APoEs
    """
    poe_duration = 50

    rps = [int(APoE.split("/")[1]) for APoE in APoEs]

    df = pd.DataFrame(index=site_list, columns=APoEs, dtype=float)

    for site in site_list:
        for rp in rps:
            apoe = 1 / rp
            poe_50 = np.round((100 * (1 - np.exp(-apoe * poe_duration))), 0).astype(
                "int"
            )

            APoE = f"APoE: 1/{rp}"
            site_idx = raw_df["site name"] == site
            poe_idx = raw_df["poe (% in 50 years)"] == poe_50
            df.loc[site, APoE] = (
                raw_df[site_idx & poe_idx]["mean magnitude"].values[0].round(1)
            )

    return df


def mock_get_disagg(
    hazard_model_ids,
    disagg_aggs,
    hazard_aggs,
    locs,
    vs30s,
    imts,
    probabilities,
):
    dissag_filepth = Path(__file__).parent / "fixtures" / "disagg_fixture_all.json"
    with dissag_filepth.open() as disagg_file:
        disaggs = json.load(disagg_file)
    for disagg in disaggs:
        disagg["disaggs"] = np.array(disagg["disaggs"])
        disagg["bins"] = np.array(disagg["bins"])
        disagg["probability"] = ProbabilityEnum[disagg["probability"]]
        yield Disagg(**disagg)


def get_df_expected(raw_df_filepath):
    site_list = [location_by_id(_id)["name"] for _id in LOCATION_IDS][0:NSITES]
    raw_df = pd.read_csv(raw_df_filepath)
    df_expected = raw_mag_to_df(raw_df, site_list, APOES)
    df_expected.index.name = "site_name"
    return df_expected


poe_data = [
    (ProbabilityEnum._05_PCT_IN_50YRS, 10000),
    (ProbabilityEnum._1_PCT_IN_50YRS, 5000),
    (ProbabilityEnum._2_PCT_IN_50YRS, 2500),
    (ProbabilityEnum._5_PCT_IN_50YRS, 1000),
    (ProbabilityEnum._10_PCT_IN_50YRS, 500),
    (ProbabilityEnum._18_PCT_IN_50YRS, 250),
    (ProbabilityEnum._39_PCT_IN_50YRS, 100),
    (ProbabilityEnum._63_PCT_IN_50YRS, 50),
    (ProbabilityEnum._86_PCT_IN_50YRS, 25),
]


name_location = [
    ("Kerikeri", CodedLocation(-35.229696132, 173.958389289, 0.001)),
    ("-46.200~166.600", CodedLocation(-46.200, 166.600, 0.001)),
]


@pytest.mark.parametrize("name,location", name_location)
def test_name_to_location(name, location):
    assert site_name_to_coded_location(name) == location


@pytest.mark.parametrize("apoe,rp", poe_data)
def test_frequency_to_poe(apoe, rp):
    frequency = f"APoE: 1/{rp}"
    assert frequency_to_poe(frequency) == apoe


@pytest.mark.parametrize("apoe,rp", poe_data)
def test_poe_to_freq(apoe, rp):
    assert poe_to_rp(apoe) == rp


@pytest.fixture
def get_disagg_fixture(monkeypatch):
    monkeypatch.setattr(query, "get_disagg_aggregates", mock_get_disagg)


def test_mean_mag_df_legacy(get_disagg_fixture):

    raw_df_filepath_leg = (
        Path(__file__).parent / "fixtures" / "SRWG214_mean_mag_legacy.csv"
    )
    df_expected_leg = get_df_expected(raw_df_filepath_leg)
    df_leg = get_mean_mag_df(HAZARD_ID, LOCATIONS, POES, HAZARD_AGG, legacy=True)

    pandas.testing.assert_frame_equal(df_leg, df_expected_leg)


def test_mean_mag_df(get_disagg_fixture, tmp_path):

    raw_df_filepath = Path(__file__).parent / "fixtures" / "SRWG214_mean_mag.csv"
    df_expected = get_df_expected(raw_df_filepath)

    df = get_mean_mag_df(HAZARD_ID, LOCATIONS, POES, HAZARD_AGG, legacy=False)

    pandas.testing.assert_frame_equal(df, df_expected)

    # test that the df written to csv and read back is identical
    csv_filepath = tmp_path / "df.csv"
    df.to_csv(csv_filepath)
    df_from_csv = read_mean_mag_df(csv_filepath)
    pandas.testing.assert_frame_equal(df, df_from_csv)
