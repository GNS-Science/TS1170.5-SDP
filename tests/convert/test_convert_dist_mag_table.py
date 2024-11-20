import pathlib

import pytest

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable

@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename)
    return DistMagTable(csv_path)


def test_convert_dm_table(dm_table):
    raw = dm_table.raw_table
    assert len(list(raw.index)) == 3954


def test_flatten_dm_table(dm_table):
    flat = dm_table.flatten()
    assert len(list(flat.index)) == 27678
