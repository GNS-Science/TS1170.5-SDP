from pathlib import Path

import pandas as pd
import pytest

# import nzssdt_2023.data_creation.constants as constants

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def mini_hcurves_hdf5_path():
    yield FIXTURES / "mini_hcurves.hdf5"


@pytest.fixture(scope="module")
def pga_reduced_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_Adjusted_RP_2500_years.csv"
    yield pd.read_csv(path)

@pytest.fixture(scope="module")
def pga_original_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_TS1170_RP_2500_years.csv"
    yield pd.read_csv(path)