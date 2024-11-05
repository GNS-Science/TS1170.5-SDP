from pathlib import Path

import pandas as pd
import pytest

# import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def mini_hcurves_hdf5_path():
    yield FIXTURES / "mini_hcurves.hdf5"


@pytest.fixture(scope="module")
def pga_reduced_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_Adjusted_RP_2500_years.csv"
    yield pd.read_csv(path)


@pytest.fixture(scope="module")
def pga_reduced_rp_500():
    path = FIXTURES / "reduced_PGA/PGA_Adjusted_RP_500_years.csv"
    yield pd.read_csv(path)


@pytest.fixture(scope="module")
def pga_original_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_TS1170_RP_2500_years.csv"
    yield pd.read_csv(path)


@pytest.fixture(scope="module")
def pga_original_rp_500():
    path = FIXTURES / "reduced_PGA/PGA_TS1170_RP_500_years.csv"
    yield pd.read_csv(path)


@pytest.fixture(scope="module")
def monkeymodule():
    """
    allow monkeypatch module see https://stackoverflow.com/q/73385558
    """
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="module")
def sa_table_original(monkeymodule, mini_hcurves_hdf5_path):
    monkeymodule.setattr(sa_gen, "TEST_NO_PGA_REDUCTION", True)
    yield sa_gen.create_sa_table(mini_hcurves_hdf5_path)


@pytest.fixture(scope="module")
def sa_table_reduced(mini_hcurves_hdf5_path):
    yield sa_gen.create_sa_table(mini_hcurves_hdf5_path)
