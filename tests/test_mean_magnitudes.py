import os
from pathlib import Path

import pandas as pd
import pandas.testing
import pytest
from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.model import AggregationEnum, ProbabilityEnum

from nzssdt_2023.data_creation.dm_parameter_generation import raw_mag_to_df
from nzssdt_2023.data_creation.mean_magnitudes import (
    get_mean_mag_df,
    poe_to_rp_rounded,
    read_mean_mag_df,
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


@pytest.mark.parametrize("apoe,expected", poe_data)
def test_poe_to_freq(apoe, expected):
    assert poe_to_rp_rounded(apoe) == expected


@pytest.mark.skipif(
    os.getenv("NZSHM22_HAZARD_STORE_STAGE") != "PROD",
    reason="requires access to toshi hazard store",
)
def test_mean_mag_df_legacy():

    raw_df_filepath_leg = (
        Path(__file__).parent / "fixtures" / "SRWG214_mean_mag_legacy.csv"
    )
    df_expected_leg = get_df_expected(raw_df_filepath_leg)
    df_leg = get_mean_mag_df(HAZARD_ID, LOCATIONS, POES, HAZARD_AGG, legacy=True)

    pandas.testing.assert_frame_equal(df_leg, df_expected_leg)


@pytest.mark.skipif(
    os.getenv("NZSHM22_HAZARD_STORE_STAGE") != "PROD",
    reason="requires access to toshi hazard store",
)
def test_mean_mag_df(tmp_path):

    raw_df_filepath = Path(__file__).parent / "fixtures" / "SRWG214_mean_mag.csv"
    df_expected = get_df_expected(raw_df_filepath)

    df = get_mean_mag_df(HAZARD_ID, LOCATIONS, POES, HAZARD_AGG, legacy=False)

    pandas.testing.assert_frame_equal(df, df_expected)

    # test that the df written to csv and read back is identical
    csv_filepath = tmp_path / "df.csv"
    df.to_csv(csv_filepath)
    df_from_csv = read_mean_mag_df(csv_filepath)
    pandas.testing.assert_frame_equal(df, df_from_csv)
