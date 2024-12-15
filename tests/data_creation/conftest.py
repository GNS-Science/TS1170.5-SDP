from pathlib import Path

import pandas as pd
import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

FIXTURES = Path(__file__).parent.parent / "fixtures"

SITECLASS_COLUMN_MAPPING = {
    "SiteClass_IV": "Site Class IV",
    "SiteClass_V": "Site Class V",
    "SiteClass_VI": "Site Class VI",
}  # modify CSV file headings to match ours


@pytest.fixture(scope="module")
def sas_tc_td_parameters():
    path = FIXTURES / "sas-tc-td_parameters/TS_parameters_all.csv"
    df = pd.read_csv(path, header=[0, 1, 2])
    yield df.set_index(keys=df.iloc[:, 0])


@pytest.fixture(scope="module")
def mini_hcurves_hdf5_path():
    yield FIXTURES / "mini_hcurves.hdf5"


@pytest.fixture(scope="module")
def pga_reduced_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_Adjusted_RP_2500_years.csv"
    yield pd.read_csv(path).rename(columns=SITECLASS_COLUMN_MAPPING)


@pytest.fixture(scope="module")
def pga_reduced_rp_500():
    path = FIXTURES / "reduced_PGA/PGA_Adjusted_RP_500_years.csv"
    yield pd.read_csv(path).rename(columns=SITECLASS_COLUMN_MAPPING)


@pytest.fixture(scope="module")
def pga_original_rp_2500():
    path = FIXTURES / "reduced_PGA/PGA_TS1170_RP_2500_years.csv"
    yield pd.read_csv(path).rename(columns=SITECLASS_COLUMN_MAPPING)


@pytest.fixture(scope="module")
def pga_original_rp_500():
    path = FIXTURES / "reduced_PGA/PGA_TS1170_RP_500_years.csv"
    yield pd.read_csv(path).rename(columns=SITECLASS_COLUMN_MAPPING)


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
    monkeymodule.setattr(sa_gen, "PGA_REDUCTION_ENABLED", False)
    yield sa_gen.create_sa_table(mini_hcurves_hdf5_path)


@pytest.fixture(scope="module")
def sa_table_reduced(mini_hcurves_hdf5_path):
    yield sa_gen.create_sa_table(mini_hcurves_hdf5_path)


@pytest.fixture(scope="module")
def dandm_v1():
    path = FIXTURES / "gis_data/D_and_M_with_floor.csv"
    yield pd.read_csv(path,index_col="Location")
