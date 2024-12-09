import json
from pathlib import Path

import pandas as pd
import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def sa_table():
    path = FIXTURES / "named_locations.json"
    with open(path, "r") as file:
        sa_table = json.load(file)["data"]
    yield sa_table


@pytest.fixture
def combo_table():
    path = FIXTURES / "v2_json" / "first_10_named_locations_combo.json"
    yield pd.read_json(path)


@pytest.fixture(scope="module")
def mini_sat_table(mini_hcurves_hdf5_path):
    yield sa_gen.create_sa_table(mini_hcurves_hdf5_path, lower_bound_flags=True)
