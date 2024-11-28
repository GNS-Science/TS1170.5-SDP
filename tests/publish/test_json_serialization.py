"""
Test the precision in the json serialization
"""

import pandas as pd
import pytest


@pytest.mark.parametrize("sc", ["I", "II", "III", "IV", "V", "VI"])
@pytest.mark.parametrize("site", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize("rp", [25, 50, 100, 250, 500, 1000, 2500])
def test_json_precision(site, sc, rp, fsim_json_table):

    fsim = fsim_json_table
    fsim.seek(0)
    df = pd.read_json(fsim, orient="table",precise_float=True)
    parameters = df[
        (df["Location"] == site)
        & (df["APoE (1/n)"] == rp)
        & (df["Site Class"] == sc)][['PGA','Sas','Tc','Td']]
    print(parameters)

    for parameter in parameters:
        print(parameter)
        print(type(parameter))
        assert parameter == round(parameter, 3)
    # assert pga == round(pga, 3)
    # assert sas == round(sas, 3)
    # assert tc == round(tc, 3)
    # assert td == round(td, 3)

