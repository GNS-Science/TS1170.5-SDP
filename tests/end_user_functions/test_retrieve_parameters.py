"""
data retrieval from TS tables

- functions in `end_user_functions.query_parameters` and '.geospatial_analysis'
"""

import numpy as np
import pandas as pd
import pytest

from nzssdt_2023.end_user_functions.geospatial_analysis import (
    calculate_distance_to_fault,
    identify_location_id,
)
from nzssdt_2023.end_user_functions.query_parameters import (
    parameters_by_location_id,
    retrieve_md_parameters,
    retrieve_sa_parameters,
)


@pytest.mark.parametrize(
    "location_id, apoe_n, site_class, expected_parameters",
    [
        ("Wellington", 500, "IV", (0.77, 1.71, 0.66, 2.6)),
        ("Auckland", 100, "II", (0.06, 0.12, 0.45, 2.4)),
    ],
)
def test_retrieve_sa_parameters(location_id, apoe_n, site_class, expected_parameters):

    assert expected_parameters == retrieve_sa_parameters(
        location_id, apoe_n, site_class
    )


@pytest.mark.parametrize(
    "location_id, apoe_n, site_class, expected_parameters",
    [
        ("Wellington", 100, "IV", (7.5, np.nan)),
        ("Wellington", 500, "IV", (7.8, 0)),
    ],
)
def test_retrieve_md_parameters(location_id, apoe_n, site_class, expected_parameters):

    assert expected_parameters == retrieve_md_parameters(
        location_id, apoe_n, site_class
    )


@pytest.mark.parametrize("location_id", ["Auckland", "Wellington"])
def test_parameters_by_location_id(location_id, expected_parameters_by_location_id):

    df = parameters_by_location_id(location_id).fillna("NULL")
    expected_df = pd.DataFrame(expected_parameters_by_location_id[location_id]).fillna(
        "NULL"
    )

    assert df.equals(expected_df)


@pytest.mark.parametrize(
    "latlon, expected_location_id",
    [
        ((-41.25, 174.775), "Wellington"),
        ((-41.25, 174.65), "-41.2~174.6"),
        ((-41.35, 174.65), "outside NZ"),
    ],
)
def test_identify_location_id(latlon, expected_location_id):

    latitude, longitude = latlon

    assert expected_location_id == identify_location_id(longitude, latitude)


@pytest.mark.parametrize(
    "latlon, expected_d",
    [
        ((-41.25, 174.65), 10),
        ((-41.32, 174.65), 5),
    ],
)
def test_distance_to_fault(latlon, expected_d):

    latitude, longitude = latlon

    assert expected_d == calculate_distance_to_fault(longitude, latitude)
