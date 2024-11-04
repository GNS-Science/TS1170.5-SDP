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


@pytest.mark.skip("covered by test_reduce_PGAs")
def test_calc_reduced_PGA() -> float:
    """Calculate the adjusted peak ground acceleration (Eq. C3.14)"""
    assert 0


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

#def test_reduce_PGAs_main_cities(mini_hcurves_hdf5_path, pga_adjusted_rp_2500):
