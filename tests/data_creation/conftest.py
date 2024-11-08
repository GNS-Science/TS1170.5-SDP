from pathlib import Path

import pandas as pd
import pytest
import pickle as pkl

# import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

from nzssdt_2023.config import WORKING_FOLDER

working_folder = Path(WORKING_FOLDER)

FIXTURES = Path(__file__).parent.parent / "fixtures"

SITECLASS_COLUMN_MAPPING = {
    "SiteClass_IV": "Site Class IV",
    "SiteClass_V": "Site Class V",
    "SiteClass_VI": "Site Class VI",
}  # modify CSV file headings to match ours

@pytest.fixture(scope="module")
def sas_tc_td_parameters():
    path = FIXTURES / "sas-tc-td_parameters/TS_parameters_nshmv5_allvariables_allsites.xlsx"
    df_dict = pd.read_excel(path, sheet_name=None)
    for key in df_dict.keys():
        df_dict[key].set_index('Location', inplace=True)
    yield df_dict

@pytest.fixture(scope="module")
def output_table_mini():
    path = working_folder / 'mini_SaT-variables.pkl'
    with open(path, "rb") as file:
        df = pkl.load(file)
    yield



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




