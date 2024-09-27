import os
from pathlib import Path

import pandas as pd
import pytest
from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.model import AggregationEnum, ProbabilityEnum

from nzssdt_2023.data_creation.dm_parameter_generation import raw_mag_to_df
from nzssdt_2023.mean_magnitudes.mean_magnitudes import (
    get_mean_mag_df,
    poe_to_rp_rounded,
)


def lat_lon(id):
    return (location_by_id(id)["latitude"], location_by_id(id)["longitude"])


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
def test_mean_mag_df():

    nsites = 10
    apoes = [
        "APoE: 1/25",
        "APoE: 1/50",
        "APoE: 1/100",
        "APoE: 1/250",
        "APoE: 1/500",
        "APoE: 1/1000",
        "APoE: 1/2500",
    ]
    site_list = [
        location_by_id(loc)["name"] for loc in LOCATION_LISTS["SRWG214"]["locations"]
    ][0:nsites]
    raw_df_filepath = Path(__file__).parent / "fixtures" / "SRWG214_mean_mag.csv"
    raw_df = pd.read_csv(raw_df_filepath)
    df_expected = raw_mag_to_df(raw_df, site_list, apoes).iloc[0:nsites, :]

    poes = [
        ProbabilityEnum._2_PCT_IN_50YRS,
        ProbabilityEnum._5_PCT_IN_50YRS,
        ProbabilityEnum._10_PCT_IN_50YRS,
        ProbabilityEnum._18_PCT_IN_50YRS,
        ProbabilityEnum._39_PCT_IN_50YRS,
        ProbabilityEnum._63_PCT_IN_50YRS,
        ProbabilityEnum._86_PCT_IN_50YRS,
    ]
    hazard_id = "NSHM_v1.0.4_mag"
    locations = [
        CodedLocation(*lat_lon(_id), 0.001)
        for _id in LOCATION_LISTS["SRWG214"]["locations"]
    ]
    hazard_agg = AggregationEnum.MEAN

    df = get_mean_mag_df(hazard_id, locations, poes, hazard_agg)

    assert df.equals(df_expected)
