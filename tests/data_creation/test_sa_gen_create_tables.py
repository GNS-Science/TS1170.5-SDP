"""
test the pga functions in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen


def test_inspect_create_sa_table(mini_hcurves_hdf5_path, pga_reduced_rp_2500):
    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)

    print(site_list)  # ['Auckland', 'Christchurch', 'Dunedin', 'Hamilton', 'Wellington']
    assert len(site_list) == 5

    print("pga_reduced", pga_reduced_rp_2500)

    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    print("APoEs", APoEs)
    print()
    print("hazard_rp_list", hazard_rp_list)
    print()

    quantile_list = sa_gen.extract_quantiles(mini_hcurves_hdf5_path)
    print("quantile_list", quantile_list)
    print()


@pytest.mark.skip("WIP demo stage only")
def test_create_sa_table(mini_hcurves_hdf5_path, pga_reduced_rp_2500):

    df0 = sa_gen.create_sa_table(mini_hcurves_hdf5_path)

    print(df0)
    print()
    print(df0.columns)

    print(df0[("APoE: 1/2500", "Site Class IV", "PGA")])
    print(df0[("APoE: 1/2500", "Site Class IV", "PGA")]["Auckland"])

    df1 = pga_reduced_rp_2500
    print(df1)
    akl = df1[df1["City"] == "Auckland"]

    assert pytest.approx(round(float(akl["SiteClass_IV"]), 2)) == float(
        df0[("APoE: 1/2500", "Site Class IV", "PGA")]["Auckland"]
    )
