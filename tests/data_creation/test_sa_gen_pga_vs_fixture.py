"""
PGA values vs external fixtures

 - functions in `nzssdt_2023.data_creation.sa_parameter_generation`
 - fixtures in testsw/fixtures/reduced_PGA/*.csv


TODO:
 these tests essentially reproduce sa_gen.create_sa_table, and reduce data scope to a single RP
 in order to make the tests faster.

 This would be much cleaner if the `sa_gen.create_sa_table` function could do this instead.
"""

import numpy as np
import pytest
from pytest_lazy_fixtures import lf

import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen
from nzssdt_2023.data_creation import extract_data


@pytest.mark.skip("WIP - exploratory ")
@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_original_PGAs(
    site_class, city, mini_hcurves_hdf5_path, pga_original_rp_2500, monkeypatch
):
    """
    Original PGA are calculated in extract_spectra() function"""

    # monkeypatch.setattr(sa_gen, "TEST_NO_PGA_REDUCTION", True)

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)
    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    hazard_rp_list_2500 = hazard_rp_list[-1:]
    vs30_list = constants.VS30_LIST

    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    RP_IDX = constants.DEFAULT_RPS.index(2500)
    PGA = PGA[:, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500
    assert PGA.shape == (6, 4, 1, 2)
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    acc_spectra_2500 = acc_spectra[:, :, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500

    assert acc_spectra_2500.shape == (
        6,
        4,
        27,
        1,
        2,
    )  # 6 vs30, 4 sites, 27 IMT, 1 RP, 2 stats

    mean_Td = sa_gen.fit_Td_array(
        PGA, Sas, Tc, acc_spectra_2500, imtls, site_list, vs30_list, hazard_rp_list_2500
    )

    mean_df = sa_gen.create_mean_sa_table(
        PGA, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list_2500
    )

    quantile_list = sa_gen.extract_quantiles(mini_hcurves_hdf5_path)

    sa_gen_df = sa_gen.update_lower_bound_sa(
        mean_df,
        PGA,
        Sas,
        Tc,
        PSV,
        acc_spectra_2500,
        imtls,
        vs30_list,
        hazard_rp_list_2500,
        quantile_list,
    )

    df1 = pga_original_rp_2500
    expected_df = df1[df1["City"] == city]

    expected_df = expected_df.rename(
        columns={
            "SiteClass_IV": "Site Class IV",
            "SiteClass_V": "Site Class V",
            "SiteClass_VI": "Site Class VI",
        }
    )
    # print("Christchurch,0.5782371974177063,0.576551165606152,0.6741478781297515")
    print(expected_df)

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == round(
        sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city], 2
    )


@pytest.mark.skip("SKIP until we have non-rounded expected fixtures")
@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_reduce_PGAs_main_cities_FAST(
    site_class, city, mini_hcurves_hdf5_path, pga_reduced_rp_2500, monkeypatch
):
    """faster because we only process one return period"""

    # monkeypatch.setattr(sa_gen, "TEST_SKIP_CPA_PGA_ROUNDING", True)
    """
    NO SKIP
    -------
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Auckland-Site Class VI] - assert 0.35 ± 3.5e-07 == 0.36
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Auckland-Site Class V] - assert 0.34 ± 3.4e-07 == 0.35
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Christchurch-Site Class IV] - assert 0.67 ± 6.7e-07 == 0.68
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Dunedin-Site Class IV] - assert 0.47 ± 4.7e-07 == 0.48
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Wellington-Site Class VI] - assert 0.98 ± 9.8e-07 == 0.97

    SKIP
    ----
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Auckland-Site Class VI] - assert 0.35 ± 3.5e-07 == 0.36
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Auckland-Site Class V] - assert 0.34 ± 3.4e-07 == 0.35
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Christchurch-Site Class IV] - assert 0.67 ± 6.7e-07 == 0.68
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Dunedin-Site Class IV] - assert 0.47 ± 4.7e-07 == 0.48
    FAILED tests/...::test_reduce_PGAs_main_cities_FAST[Wellington-Site Class VI] - assert 0.98 ± 9.8e-07 == 0.97
    """

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)
    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    hazard_rp_list_2500 = hazard_rp_list[-1:]
    vs30_list = constants.VS30_LIST

    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    RP_IDX = constants.DEFAULT_RPS.index(2500)
    PGA = PGA[:, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500
    assert PGA.shape == (6, 4, 1, 2)
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    acc_spectra_2500 = acc_spectra[:, :, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500

    assert acc_spectra_2500.shape == (
        6,
        4,
        27,
        1,
        2,
    )  # 6 vs30, 4 sites, 27 IMT, 1 RP, 2 stats

    mean_Td = sa_gen.fit_Td_array(
        PGA, Sas, Tc, acc_spectra_2500, imtls, site_list, vs30_list, hazard_rp_list_2500
    )

    mean_df = sa_gen.create_mean_sa_table(
        PGA, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list_2500
    )

    quantile_list = sa_gen.extract_quantiles(mini_hcurves_hdf5_path)

    sa_gen_df = sa_gen.update_lower_bound_sa(
        mean_df,
        PGA,
        Sas,
        Tc,
        PSV,
        acc_spectra_2500,
        imtls,
        vs30_list,
        hazard_rp_list_2500,
        quantile_list,
    )

    df1 = pga_reduced_rp_2500
    expected_df = df1[df1["City"] == city]

    print(expected_df)

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == round(
        sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city], 2
    )


@pytest.mark.skip("SKIP until we have non-rounded expected fixtures")
def test_reduce_PGAs_main_cities_SIMPLE_SLOW(
    mini_hcurves_hdf5_path, pga_reduced_rp_2500
):
    """This is slow because it handles all return periods"""
    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)
    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    vs30_list = constants.VS30_LIST
    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    assert PGA.shape == (6, 4, 7, 2)
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)

    mean_Td = sa_gen.fit_Td_array(
        PGA, Sas, Tc, acc_spectra, imtls, site_list, vs30_list, hazard_rp_list
    )

    mean_df = sa_gen.create_mean_sa_table(
        PGA, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list
    )

    quantile_list = sa_gen.extract_quantiles(mini_hcurves_hdf5_path)
    df0 = sa_gen.update_lower_bound_sa(
        mean_df,
        PGA,
        Sas,
        Tc,
        PSV,
        acc_spectra,
        imtls,
        vs30_list,
        hazard_rp_list,
        quantile_list,
    )

    print(df0)

    df1 = pga_reduced_rp_2500
    akl = df1[df1["City"] == "Auckland"]

    assert pytest.approx(round(float(akl["SiteClass_IV"]), 2)) == float(
        df0[("APoE: 1/2500", "Site Class IV", "PGA")]["Auckland"]
    )


@pytest.mark.skip("SKIP until we have non-rounded expected fixtures")
@pytest.mark.parametrize(
    "site_class", [f"Site Class {sc}" for sc in "IV,V,VI".split(",")]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize(
    "return_period, pga_table",
    [
        (2500, lf("pga_reduced_rp_2500")),
        (500, lf("pga_reduced_rp_500")),
    ],
)
def test_create_sa_table_reduced_pga(
    sa_table_reduced, city, site_class, return_period, pga_table
):

    df0 = sa_table_reduced

    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")])
    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city])

    df1 = pga_table
    print(df1)
    expected_df = df1[df1["City"] == city]

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == float(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]
    )


@pytest.mark.parametrize(
    "site_class", [f"Site Class {sc}" for sc in "IV,V,VI".split(",")]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize(
    "return_period, expected_pgas",
    [
        (2500, lf("pga_original_rp_2500")),
        (500, lf("pga_original_rp_500")),
    ],
)
def test_create_sa_table_original_pga(
    sa_table_original, city, site_class, return_period, expected_pgas
):

    df0 = sa_table_original

    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")])
    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city])

    df1 = expected_pgas
    print(df1)
    expected_df = df1[df1["City"] == city]

    assert pytest.approx(expected_df[site_class]) == round(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city], 2
    )


## Annes test....
@pytest.mark.parametrize(
    "site_class", ["Site Class V", "Site Class VI", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize(
    "return_period, pga_original_table, pga_reduced_table",
    [
        (2500, lf("pga_original_rp_2500"), lf("pga_reduced_rp_2500")),
        (500, lf("pga_original_rp_500"), lf("pga_reduced_rp_500")),
    ],
)
def test_PGA_reduction(
    site_class, city, return_period, pga_original_table, pga_reduced_table
):
    """PGA reduction on CdlT's original PGAs"""

    sc = site_class.split(" ")[-1]

    df_original = pga_original_table.set_index("City")
    df_reduced = pga_reduced_table.set_index("City")

    pga_original = df_original.loc[
        city, site_class
    ]  # get the single PGA vlue using city/site_class indices
    pga_reduced = sa_gen.calc_reduced_PGA(
        pga_original, sc
    )  # get the single PGA value using our formulae and NSHM hazard tables

    print(pga_reduced)
    print()
    print(df_reduced.loc[city, site_class])

    # the two values must be equivalent to 8 decimal places
    assert (
        pytest.approx(df_reduced.loc[city, site_class], 1e-18) == pga_reduced
    )  # 0.3433339156821064 (AKL, V, 2500)


def test_hdf5_vs30_indices(mini_hcurves_hdf5_path):
    vs30_list = extract_data.extract_vs30s(mini_hcurves_hdf5_path)
    assert vs30_list == constants.VS30_LIST


def test_hdf5_site_indices(mini_hcurves_hdf5_path):
    site_list = list(extract_data.extract_sites(mini_hcurves_hdf5_path).index)
    assert site_list == ["Auckland", "Christchurch", "Dunedin", "Wellington"]


def getpga(pga_array, siteclass, sitelist, city, return_period):
    """A test helper function"""
    vs30 = constants.SITE_CLASSES[siteclass].representative_vs30
    i_vs30 = constants.VS30_LIST.index(vs30)
    i_site = sitelist.index(city)
    i_rp = constants.DEFAULT_RPS.index(return_period)
    i_stat = 0
    return pga_array[i_vs30, i_site, i_rp, i_stat]


@pytest.mark.skip('SKIP until we have non-rounded expected fixtures"')
@pytest.mark.parametrize(
    "site_class", ["Site Class V", "Site Class VI", "Site Class IV"]
)
@pytest.mark.parametrize(
    "city", ["Christchurch", "Dunedin", "Wellington"]
)  # "Auckland",
@pytest.mark.parametrize(
    "return_period, pga_original_table, pga_reduced_table",
    [
        (2500, lf("pga_original_rp_2500"), lf("pga_reduced_rp_2500")),
        (500, lf("pga_original_rp_500"), lf("pga_reduced_rp_500")),
    ],
)
def test_calculate_parameter_arrays_function(
    site_class,
    city,
    return_period,
    pga_original_table,
    pga_reduced_table,
    mini_hcurves_hdf5_path,
    monkeypatch,
):

    # monkeypatch.setattr(sa_gen, "TEST_NO_PGA_REDUCTION", False)
    # monkeypatch.setattr(sa_gen, "TEST_SKIP_CPA_PGA_ROUNDING", False)
    # monkeypatch.setattr(sa_gen, "TEST_REDUCE_VS30_MOD", False)

    sc = site_class.split(" ")[-1]

    # print()
    # print(f'sc: {sc}')
    # print(f'site_class: {site_class}')
    # print(f'siteclass_obj: {siteclass_obj}')
    # print()

    # df_reduced  = pga_reduced_table.set_index('City')
    # print(df_reduced.loc[city,site_class])

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)

    # ##########
    # # setup for no PGA reduction ....

    # monkeypatch.setattr(sa_gen, "TEST_NO_PGA_REDUCTION", True)
    # monkeypatch.setattr(sa_gen, "TEST_SKIP_CPA_PGA_ROUNDING", True)

    # PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)
    # test_original_pga = getpga(PGA, sc, site_list, city, return_period)

    # print('test_original_pga', test_original_pga)

    # df_original  = pga_original_table.set_index('City')
    # print(df_original.loc[city,site_class])
    # print('test pga_original PGA array')
    # print(df_original.loc[city,:])
    # assert pytest.approx(test_original_pga) == df_original.loc[city,site_class]
    # ###########

    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    test_reduced_pga = getpga(PGA, sc, site_list, city, return_period)

    print("test_reduced_pga:", test_reduced_pga)

    df_reduced = pga_reduced_table.set_index("City")
    print(df_reduced.loc[city, site_class])

    print("test pga_reduced PGA array")
    print(
        df_reduced.loc[city, :],
    )
    assert pytest.approx(round(test_reduced_pga, 2)) == round(
        df_reduced.loc[city, site_class], 2
    )


@pytest.mark.parametrize(
    "site_class", ["Site Class V", "Site Class VI", "Site Class IV"]
)
@pytest.mark.parametrize(
    "city", ["Christchurch", "Dunedin", "Wellington"]
)  # "Auckland"
@pytest.mark.parametrize(
    "return_period, pga_original_table, pga_reduced_table",
    [
        (2500, lf("pga_original_rp_2500"), lf("pga_reduced_rp_2500")),
        (500, lf("pga_original_rp_500"), lf("pga_reduced_rp_500")),
    ],
)
def test_extract_spectra_and_reproduce_rounding_error(
    site_class,
    city,
    return_period,
    pga_original_table,
    pga_reduced_table,
    mini_hcurves_hdf5_path,
):
    """
    This test helped us figure out that the reason other tests are failing is that the
    fixtures/reduced_PGA tables were based on an `all_SaT-varaibles.pkl` file that
    had PGA rounded to two DP, instead of to full precision.

    Note that 'Auckland' is excluded from these tests becuase it requires the lower_bound step
    """
    sc = site_class.split(" ")[-1]

    # from calculate_parameter_arrays( in sa_gen
    acc_spectra, imtls = extract_data.extract_spectra(mini_hcurves_hdf5_path)
    PGA = acc_spectra[:, :, constants.IMT_LIST.index("PGA"), :, :]

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)

    test_original_pga = getpga(PGA, sc, site_list, city, return_period)

    # Part ONE
    # check expected PGA before reduction
    df_original = pga_original_table.set_index("City")
    assert (
        pytest.approx(round(test_original_pga, 2)) == df_original.loc[city, site_class]
    )

    # PART TWO !!!!
    # here we're rounding the PGA values to reproduce what the erroneous fixtures do.
    reduced_pga = sa_gen.reduce_PGAs(
        np.round(PGA, 2)
    )  # THIS reproduced the test fixtures provided by CdlT

    df_reduced = pga_reduced_table.set_index("City")

    test_reduced_pga = getpga(reduced_pga, sc, site_list, city, return_period)
    assert pytest.approx(test_reduced_pga) == df_reduced.loc[city, site_class]
