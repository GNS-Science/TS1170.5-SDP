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


# @pytest.mark.skip('WIP')
@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_original_PGAs(
    site_class, city, mini_hcurves_hdf5_path, pga_original_rp_2500, monkeypatch
):
    """Original PGA are calculated in extract_spectra() function"""

    monkeypatch.setattr(sa_gen, "TEST_NO_PGA_REDUCTION", True)

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

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == float(
        sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city]
    )


@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
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

    sc = site_class.split(' ')[-1]

    df_original = pga_original_table.set_index('City')
    df_reduced  = pga_reduced_table.set_index('City')

    pga_original = df_original.loc[city,site_class]
    pga_reduced = sa_gen.calc_reduced_PGA(pga_original, sc)

    assert pytest.approx(df_reduced.loc[city,site_class]) == pga_reduced


@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_reduce_PGAs_main_cities_FAST(
    site_class, city, mini_hcurves_hdf5_path, pga_reduced_rp_2500
):
    """faster because we only process one return period"""

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

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == float(
        sa_gen_df[("APoE: 1/2500", site_class, "PGA")][city]
    )


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

    # print(df0)
    # print()
    # print(df0.columns)

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
    "return_period, pga_table",
    [
        (2500, lf("pga_original_rp_2500")),
        (500, lf("pga_original_rp_500")),
    ],
)
def test_create_sa_table_original_pga(
    sa_table_original, city, site_class, return_period, pga_table
):

    df0 = sa_table_original

    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")])
    print(df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city])

    df1 = pga_table
    print(df1)
    expected_df = df1[df1["City"] == city]

    assert pytest.approx(round(float(expected_df[site_class]), 2)) == float(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]
    )
