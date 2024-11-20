"""
Test the precision in the json serialization
"""

import pytest


@pytest.mark.parametrize("sc", ["IV", "V", "VI"])
@pytest.mark.parametrize("site", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize("rp", [25, 50, 100, 250, 500, 1000, 2500])
def test_json_precision(site, sc, rp, sa_table):
    def call_sa_parameters(site, rp, sc, sa_table):
        """
        calls parameters from the sa table
        """
        line = [
            line
            for line in sa_table
            if (line["Location"] == site)
            & (line["Site Class"] == sc)
            & (line["APoE (1/n)"] == rp)
        ][0]

        return line["PGA"], line["Sas"], line["Tc"]

    pga, sas, tc = call_sa_parameters(site, rp, sc, sa_table)

    assert pga == round(pga, 3)
    assert sas == round(sas, 3)
    assert tc == round(tc, 3)
