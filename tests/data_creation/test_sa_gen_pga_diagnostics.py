"""
PGA value diagnostics
"""

import pytest
import numpy as np
import random
from pytest_lazy_fixtures import lf

import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

@pytest.mark.skip("exploratory parked - stil need to find our point of reference ")
@pytest.mark.parametrize(
    "site_class", [f"Site Class {sc}" for sc in "V,VI,IV".split(",")]
)
@pytest.mark.parametrize("city", [ "Auckland", "Christchurch", "Dunedin", "Wellington",])
@pytest.mark.parametrize(
    "return_period, expected_pgas",
    [
        (2500, lf("pga_reduced_rp_2500")),
        # (500, lf("pga_reduced_rp_500")),
    ],
)
def test_create_sa_table_reduced_pga_diagnostic(
    mini_hcurves_hdf5_path, city, site_class, return_period, expected_pgas
):

    # df0 = sa_table_reduced
    # we need to drill into the create_sa_table method
    df0 = sa_gen.create_sa_table(mini_hcurves_hdf5_path)
    mini_hcurves_hdf5_path


    print(f'DIAG #5 the expected PGAs from Chris dlT csv files')
    print('=' * 40)
    df1 = expected_pgas
    expected_df = df1[df1["City"].isin(["Auckland", "Christchurch", "Dunedin", "Wellington",])]
    print(expected_df)
    print()

    # assert pytest.approx(round(df_reduced.loc[city,site_class],8)) == pga_reduced

    assert pytest.approx(expected_df[expected_df["City"] == city][site_class], abs=5e-3) == float(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]
    )


@pytest.mark.skip("exploratory parked - stil need to find our point of reference ")
@pytest.mark.parametrize(
    "site_class", [ "Site Class V", ] # "Site Class VI","Site Class IV"
)
@pytest.mark.parametrize("city", ["Christchurch"]) #Auckland"]) #  ), "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize(
    "return_period, pga_reduced_table",
    [
        (2500, lf("pga_reduced_rp_2500")),
        # (500, lf("pga_original_rp_500"), lf("pga_reduced_rp_500")),
    ],
)
def test_reduce_PGAs_vs_expected_values(
    site_class, city, return_period, mini_hcurves_hdf5_path, pga_reduced_table, monkeypatch
):
    """PGA reduction on CdlT's original PGAs"""

    monkeypatch.setattr(sa_gen, "PGA_REDUCTION_ENABLED", True)
    #monkeypatch.setattr(sa_gen, "TEST_SKIP_CPA_PGA_ROUNDING", True)
    #monkeypatch.setattr(sa_gen, "TEST_REDUCE_VS30_MOD", True)

    EXPECTED_TABLE = """
    DIAG #5 the expected PGAs from Chris dlT csv files
    ========================================
                 City  Site Class VI  Site Class V  Site Class IV
    29       Auckland     0.35452432    0.34333392     0.36993928
    135    Wellington     0.97620320    1.00984286     1.27697630
    169  Christchurch     0.57823720    0.57655117     0.67414788
    203       Dunedin     0.42786594    0.42600939     0.47336883
    """

    print()
    print(EXPECTED_TABLE)

    # df_original = pga_original_table.set_index('City')
    # APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)
    # vs30_list = constants.VS30_LIST

    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)

    ### OG TEST == OK
    PGA = acc_spectra[:, :, constants.IMT_LIST.index("PGA"), :, :]
    reduced_pgas = sa_gen.reduce_PGAs(PGA)


    SITE_IDX = 0  # Auckland
    SITE_IDX = 1  # Christchurch
    RP_IDX = constants.DEFAULT_RPS.index(2500)
    STAT_IDX = 0  # mean

    PGA_SITE_RP_STAT = PGA[:, SITE_IDX, RP_IDX, STAT_IDX]

    print("original PGAs calculated")
    print(PGA_SITE_RP_STAT)

    print("reduced PGAs calculated")
    print(reduced_pgas[:, SITE_IDX, RP_IDX, STAT_IDX])
    print()

    df_reduced  = pga_reduced_table.set_index('City')
    pga_expected = df_reduced.loc[city,site_class]

    print("reduced PGAs expected")
    print(pga_expected)
    print()
    assert 0

    ### from sa_create_table
    PGA2, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    assert (np.round(PGA2,3) == np.round(PGA,3)).all()
    assert (np.round(PGA2,5) == np.round(PGA,5)).all()
    assert (np.round(PGA2,9) == np.round(PGA,9)).all()

    assert 0


    SITE_IDX = 0  # Auckland
    SITE_IDX = 1  # Christchurch

    RP_IDX = constants.DEFAULT_RPS.index(2500)
    STAT_IDX = 0  # mean
    PGA1 = reduced_pgas[:, SITE_IDX, RP_IDX, STAT_IDX]



    # site_list = [city]

    # mean_Td = sa_gen.fit_Td_array(
    #     PGA2, Sas, Tc, acc_spectra, imtls, site_list, vs30_list, hazard_rp_list[-1:]
    # )

    # mean_df = sa_gen.create_mean_sa_table(
    #     PGA2, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list[-1:]
    # )

    """
    print('PGA1:', PGA1)

    df_reduced  = pga_reduced_table.set_index('City')
    pga_expected = df_reduced.loc[city,site_class]

    print(pga_expected)

    print(pga_reduced)
    print()
    print(df_reduced.loc[city,site_class])
    """
    # assert pytest.approx(df_reduced.loc[city,site_class]) == pga_reduced # 0.3433339156821064 (AKL, V, 2500)



## TEST 1) Annes test....
# showing that the sa_gen.calc_reduced_PGA() function returns
#  PGA values aligned with expected PGA table from Chris DlT to full machine precision
#
#  NB: this is fine but note the pga_original_table values are incorrectly rounded, so these
#  test values are slightly different than those expected in the final case,
##
@pytest.mark.parametrize(
    "site_class", [ "Site Class V", "Site Class VI","Site Class IV" ]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize(
    "return_period, pga_original_table, pga_reduced_table",
    [
        (2500, lf("pga_original_rp_2500"), lf("pga_reduced_rp_2500")),
        (500, lf("pga_original_rp_500"), lf("pga_reduced_rp_500")),
    ],
)
def test_PGA_reduction_anne(
    site_class, city, return_period, pga_original_table, pga_reduced_table, monkeypatch
):
    """PGA reduction on CdlT's original PGAs"""

    # monkeypatch.setattr(sa_gen, "PGA_REDUCTION_ENABLED", True)
    # monkeypatch.setattr(sa_gen, "TEST_SKIP_CPA_PGA_ROUNDING", True)

    sc = site_class.split(' ')[-1]

    df_original = pga_original_table.set_index('City')
    df_reduced  = pga_reduced_table.set_index('City')

    pga_original = df_original.loc[city,site_class]
    pga_reduced = sa_gen.calc_reduced_PGA(pga_original, sc)

    print(pga_reduced)
    print()
    print(df_reduced.loc[city,site_class])

    assert pytest.approx(df_reduced.loc[city,site_class], 1e-18) == pga_reduced # 0.3433339156821064 (AKL, V, 2500)
    # # assert 0
    # if random.choice([1,2,3]) == 3:
    #     assert 0




