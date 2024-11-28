"""
Sas, Tc, Td values vs external fixtures

 - functions in `nzssdt_2023.data_creation.sa_parameter_generation`
 - fixtures in testsw/fixtures/sas-tc-td_parameters

"""

import pytest

import pandas as pd
from io import StringIO

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen
from nzssdt_2023.publish.convert import SatTable

import nzssdt_2023.data_creation.extract_data as ext_data


@pytest.mark.parametrize(
    "site",
    ["Auckland", "Christchurch", "Dunedin", "Wellington"],  # need to add Hamilton
)
@pytest.mark.parametrize("return_period", [25, 50, 100, 250, 500, 1000, 2500])
@pytest.mark.parametrize("sc", ["I", "II", "III", "IV", "V", "VI"])
@pytest.mark.parametrize("parameter", ["Sas", "Tc", "Td"])
def test_parameter_table(
    site, return_period, sc, parameter, sas_tc_td_parameters, mini_hcurves_hdf5_path
):
    """Test the generated output table against fixture values."""

    if parameter == "PGA":
        assert (
            0
        ), "PGA values should not be checked again the sas_tc_td_parameters fixture."

    apoe = f"APoE: 1/{return_period}"
    site_class = f"Site Class {sc}"

    fixture_df = sas_tc_td_parameters
    fixture_value = fixture_df.loc[site, (apoe, site_class, parameter)]

    df = sa_gen.create_sa_table(mini_hcurves_hdf5_path, lower_bound_flags=False)
    flat_df = SatTable(df).flatten().infer_objects()
    fsim = StringIO()
    flat_df.to_json(fsim, index=True, orient="table", indent=2, double_precision=3)
    fsim.seek(0)
    df = pd.read_json(fsim, orient="table")
    df_value = df[
        (df["Location"] == site)
        & (df["APoE (1/n)"] == return_period)
        & (df["Site Class"] == sc)
    ][parameter].to_numpy()[0]
    print(df_value)

    assert df_value == fixture_value
