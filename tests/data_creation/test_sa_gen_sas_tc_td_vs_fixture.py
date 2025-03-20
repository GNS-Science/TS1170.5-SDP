"""
Sas, Tc, Td values vs external fixtures

 - functions in `nzssdt_2023.data_creation.sa_parameter_generation`
 - fixtures in testsw/fixtures/sas-tc-td_parameters

"""

import pandas as pd
import pytest


# @pytest.mark.skip('update fixture')
@pytest.mark.parametrize(
    "site", ["Auckland", "Christchurch", "Dunedin", "Hamilton", "Wellington"]
)
@pytest.mark.parametrize("return_period", [25, 50, 100, 250, 500, 1000, 2500])
@pytest.mark.parametrize("sc", ["I", "II", "III", "IV", "V", "VI"])
@pytest.mark.parametrize("parameter", ["Sas", "Tc", "Td"])
def test_parameter_table(
    site, return_period, sc, parameter, sas_tc_td_parameters, fsim_json_table
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

    fsim = fsim_json_table
    fsim.seek(0)
    df = pd.read_json(fsim, orient="table", precise_float=True)

    print(df)

    df_value = df[
        (df["Location"] == site)
        & (df["APoE (1/n)"] == return_period)
        & (df["Site Class"] == sc)
    ][parameter].to_numpy()[0]

    assert df_value == fixture_value
