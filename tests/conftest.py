import itertools
import pathlib

import pandas as pd
import pytest

import nzssdt_2023.data_creation.dm_parameter_generation as dm_parameter_generation
import nzssdt_2023.data_creation.mean_magnitudes as mean_magnitudes
from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def mock_get_mean_mags(
    hazard_id,
    locations,
    vs30s,
    imts,
    poes,
    hazard_agg,
):
    for location, vs30, imt, poe in itertools.product(locations, vs30s, imts, poes):
        _, name = mean_magnitudes.get_loc_id_and_name(location.downsample(0.001).code)
        yield dict(
            name=name,
            poe=poe,
            mag=5.0,
        )


@pytest.fixture
def mean_mags_fixture(monkeypatch):
    monkeypatch.setattr(mean_magnitudes, "get_mean_mags", mock_get_mean_mags)


@pytest.fixture(scope="function")
def workingfolder_fixture(monkeypatch, tmp_path):
    monkeypatch.setattr(dm_parameter_generation, "WORKING_FOLDER", str(tmp_path))


@pytest.fixture(scope="module")
def sat_table_v1():
    filepath = FIXTURES / "v1_pkl" / "mini_SaT-variables.pkl"
    df = pd.read_pickle(filepath)
    return SatTable(df)


@pytest.fixture(scope="module")
def sat_named_table_v2():
    filepath = FIXTURES / "v2_json" / "named_locations.json"
    return pd.read_json(filepath, orient="table")


@pytest.fixture(scope="module")
def dm_table_v1():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(
        RESOURCES_FOLDER, "pipeline", "v1", filename
    )  # not as per publish/report @ v1
    return DistMagTable(csv_path)


@pytest.fixture(scope="module")
def dm_table_v2():
    filepath = FIXTURES / "v2_json" / "d_and_m.json"
    return pd.read_json(filepath, orient="table")
