import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def sa_table():
    path = FIXTURES / "named_locations.json"
    with open(path, "r") as file:
        sa_table = json.load(file)["data"]
    yield sa_table
