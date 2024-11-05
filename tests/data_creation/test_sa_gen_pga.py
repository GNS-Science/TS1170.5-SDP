"""
test the pga functions in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

import numpy as np
import pytest

import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen


def test_pga_reduction_constants():
    rdc = constants.PGA_REDUCTIONS
    # members
    assert len(rdc) == 3
    assert ["IV", "V", "VI"] == [r for r in rdc.keys()]
    assert ["IV", "V", "VI"] == [r.site_class for r in rdc.values()]

    # member attributes
    assert rdc["V"].A0 >= 0
    assert rdc["V"].A1 >= 0
    assert rdc["V"].PGA_threshold >= 0
    assert rdc["V"].site_class == "V"


@pytest.mark.parametrize("site_class", constants.PGA_REDUCTIONS.keys())
def test_calc_R_PGA_below_threshold(site_class):
    r = constants.PGA_REDUCTIONS[site_class]
    assert (
        sa_gen.calc_R_PGA(r.PGA_threshold - 1e-3, site_class) == 0
    ), f"`{site_class}` below threshold"


@pytest.mark.parametrize("site_class", constants.PGA_REDUCTIONS.keys())
def test_calc_R_PGA_above_threshold(site_class):
    r = constants.PGA_REDUCTIONS[site_class]
    assert (
        sa_gen.calc_R_PGA(r.PGA_threshold + 1e-3, site_class) > 0
    ), f"`{site_class}` above threshold"


@pytest.mark.parametrize("site_class", constants.PGA_REDUCTIONS.keys())
def test_calc_R_PGA_at_1pt0(site_class):
    pga = 1.0
    r = constants.PGA_REDUCTIONS[site_class]
    assert (
        sa_gen.calc_R_PGA(pga, site_class) == r.A0 * np.log(pga) + r.A1
    ), f"`{site_class}` reduction factor at PGA==1.0"


def test_extract_spectra(mini_hcurves_hdf5_path):
    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    print(acc_spectra.shape)
    assert acc_spectra.shape == (6, 4, 27, 7, 2)
    PGA = acc_spectra[:, :, constants.IMT_LIST.index("PGA"), :, :]
    print(PGA.shape)
    assert PGA.shape == (6, 4, 7, 2)


def test_reduce_PGAs(mini_hcurves_hdf5_path):
    """Apply peak ground acceleration adjustments to all PGA values (Eq. C3.14)"""

    acc_spectra, imtls = sa_gen.extract_spectra(mini_hcurves_hdf5_path)
    PGA = acc_spectra[:, :, constants.IMT_LIST.index("PGA"), :, :]

    reduced_PGA = sa_gen.reduce_PGAs(PGA)

    assert reduced_PGA.shape == PGA.shape, "array shape is identical"
    assert (
        reduced_PGA <= PGA
    ).all(), "reduced PGA should not exceed the original value"


# def test_extract_spectra(mini_hcurves_hdf5_path):
#     acc_spectra, imtls = extract_spectra(mini_hcurves_hdf5_path)

#     print(acc_spectra)
#     assert 0


@pytest.mark.parametrize(
    "site_class", ["Site Class VI", "Site Class V", "Site Class IV"]
)
@pytest.mark.parametrize("city", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
def test_reduce_PGAs_main_cities_FAST(
    site_class, city, mini_hcurves_hdf5_path, pga_adjusted_rp_2500
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

    df1 = pga_adjusted_rp_2500
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


def test_reduce_PGAs_main_cities_SIMPLE_SLOW(
    mini_hcurves_hdf5_path, pga_adjusted_rp_2500
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

    df1 = pga_adjusted_rp_2500
    akl = df1[df1["City"] == "Auckland"]

    assert pytest.approx(round(float(akl["SiteClass_IV"]), 2)) == float(
        df0[("APoE: 1/2500", "Site Class IV", "PGA")]["Auckland"]
    )
