"""
Test the precision in the json serialization
"""

import pandas as pd
import pytest


@pytest.mark.parametrize("sc", ["I", "II", "III", "IV", "V", "VI"])
@pytest.mark.parametrize("site", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize("rp", [25, 50, 100, 250, 500, 1000, 2500])
@pytest.mark.parametrize("parameter", ["PGA", "Sas", "Tc", "Td"])
def test_json_precision(site, sc, rp, parameter, fsim_json_table):

    fsim = fsim_json_table
    fsim.seek(0)
    df = pd.read_json(fsim, orient="table", precise_float=True)
    value = df[
        (df["Location"] == site) & (df["APoE (1/n)"] == rp) & (df["Site Class"] == sc)
    ][parameter].to_numpy()[0]

    assert value == round(value, 3)
