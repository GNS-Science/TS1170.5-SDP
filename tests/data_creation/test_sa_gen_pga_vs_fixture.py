"""
PGA values vs external fixtures

 - functions in `nzssdt_2023.data_creation.sa_parameter_generation`
 - fixtures in testsw/fixtures/reduced_PGA/*.csv


TODO:
 these tests essentially reproduce sa_gen.create_sa_table, and reduce data scope to a single RP
 in order to make the tests faster.

 This would be much cleaner if the `sa_gen.create_sa_table` function could do this instead.
"""

import pytest
from pytest_lazy_fixtures import lf

import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen
from nzssdt_2023.data_creation import extract_data


@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_unreduced_unrounded_PGAs(
    site_class, city, mini_hcurves_hdf5_path, pga_original_rp_2500, monkeypatch
):
    """
    Original PGA are calculated in extract_spectra() function"""

    ## Setting these constants on sa_gen produces unreduced, unroubded PGA values
    #  these are the inputs provided for external validattion wiht CDLT code.

    monkeypatch.setattr(sa_gen, "PGA_REDUCTION_ENABLED", False)
    monkeypatch.setattr(sa_gen, "PGA_ROUNDING_ENABLED", False)

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)
    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    hazard_rp_list_2500 = hazard_rp_list[-1:]
    vs30_list = constants.VS30_LIST

    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    RP_IDX = constants.DEFAULT_RPS.index(2500)
    PGA = PGA[:, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500
    assert PGA.shape == (6, 5, 1, 2)
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    acc_spectra_2500 = acc_spectra[:, :, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500

    assert acc_spectra_2500.shape == (
        6,
        5,
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

    assert (
        pytest.approx(float(expected_df[site_class].iloc[0]))
        == sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city]
    )


@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_reduce_PGAs_main_cities_FAST(
    site_class, city, mini_hcurves_hdf5_path, pga_reduced_rp_2500, monkeypatch
):
    """faster because we only process one return period"""

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)
    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    hazard_rp_list_2500 = hazard_rp_list[-1:]
    vs30_list = constants.VS30_LIST

    PGA, Sas, PSV, Tc = sa_gen.calculate_parameter_arrays(mini_hcurves_hdf5_path)

    RP_IDX = constants.DEFAULT_RPS.index(2500)
    PGA = PGA[:, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500
    assert PGA.shape == (6, 5, 1, 2)
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    acc_spectra_2500 = acc_spectra[:, :, :, RP_IDX : RP_IDX + 1, :]  # only the RP=2500

    assert acc_spectra_2500.shape == (
        6,
        5,
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

    assert pytest.approx(round(float(expected_df[site_class].iloc[0]), 2)) == round(
        sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city], 2
    )


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
    # print(df1)
    expected_df = df1[df1["City"] == city]

    print("reduced_table:", df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city])
    print()
    print("expected: ", expected_df[site_class])
    print()

    assert pytest.approx(round(float(expected_df[site_class].iloc[0]), 2)) == float(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]
    )


# @pytest.mark.skip('testing fixtures, not functions')
# @pytest.mark.parametrize(
#     "site_class", [f"Site Class {sc}" for sc in "IV,V,VI".split(",")]
# )
# @pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
# @pytest.mark.parametrize(
#     "return_period, expected_pgas",
#     [
#         (2500, lf("pga_original_rp_2500")),
#         (500, lf("pga_original_rp_500")),
#     ],
# )
# def test_create_sa_table_original_pga(
#     sa_table_original, city, site_class, return_period, expected_pgas
# ):

#     df0 = sa_table_original

#     print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")])
#     print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city])

#     df1 = expected_pgas
#     print(df1)
#     expected_df = df1[df1["City"] == city]

#     assert pytest.approx(expected_df[site_class]) == df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]


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
    assert site_list == [
        "Auckland",
        "Hamilton",
        "Wellington",
        "Christchurch",
        "Dunedin",
    ]


def getpga(pga_array, siteclass, sitelist, city, return_period):
    """A test helper function"""
    vs30 = constants.SITE_CLASSES[siteclass].representative_vs30
    i_vs30 = constants.VS30_LIST.index(vs30)
    i_site = sitelist.index(city)
    i_rp = constants.DEFAULT_RPS.index(return_period)
    i_stat = 0
    return pga_array[i_vs30, i_site, i_rp, i_stat]


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

    sc = site_class.split(" ")[-1]

    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)

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
