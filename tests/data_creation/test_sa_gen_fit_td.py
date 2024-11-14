"""
test the `fit_Td` and related functions in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

# from collections import namedtuple

import numpy as np
import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

@pytest.mark.skip('todo')
def test_fit_td_exploratory():
    """def fit_Td(
        spectrum: "npt.NDArray", periods: "npt.NDArray", pga: float, sas: float, tc: float
    ) -> float:
    Fit the Td value to obtain the best fit over the response spectrum

    Args:
        spectrum: acceleration spectrum [g]
        periods:  periods over which spectrum is defined [seconds]
        pga: peak ground acceleration [g]
        sas: short-period spectral acceleration [g]
        tc: spectral-acceleration-plateau corner period [seconds]

    Returns:
        td: spectral-velocity-plateau corner period [seconds]
    """
    # TODO: figure out what argument and result values are useful, then
    # these can be parametrized ....
    periods = np.linspace(0.1, 3.0, num=8) # shaking periods in seconds
    spectrum = np.linspace(0.25, 5, num=8) # spectra in g
    pga = 1.0
    sas = 0.1
    tc = 1.0

    result  = sa_gen.fit_Td(spectrum, periods, pga, sas, tc)

    print(result)
    assert 0

@pytest.mark.skip('todo')
def test_relevant_spectrum_domain_exploratory():
    """ spectrum: "npt.NDArray", periods: "npt.NDArray", tc: float, inclusive: bool = False
    ) -> Tuple["npt.NDArray", "npt.NDArray"]:

    Return the spectrum over the relevant domain for potential values of Td

    Args:
        spectrum: acceleration spectrum [g]
        periods:  periods as which spectrum is defined [seconds]
        tc:       spectral-acceleration-plateau corner period [seconds]
        inclusive: if true, the range includes the tc+0.5 value
                   (e.g. for Tc+0.5 = 0.75, 0.7 <= Td rather than 0.8 <= Td)

    Returns:
        relevant_spectrum: spectrum over the relevant periods
        relevant_periods: periods included in the relevant domain
    """

    # TODO: figure out what argument and result values are useful, then
    # these can be parametrized ....
    spectrum = np.linspace(0.25, 5, num=8) # spectra in g
    periods = np.linspace(0.5, 3.0, num=8) # shaking periods in seconds
    tc = 1.0
    inclusive = True

    r_spectrum, r_periods = sa_gen.relevant_spectrum_domain(spectrum, periods, tc, inclusive )

    print('spectrum', spectrum)
    print('r_spectrum', r_spectrum)
    print()
    print('periods', periods)
    print('r_periods', r_periods)
    assert 0

@pytest.mark.skip('todo')
def test_Td_fit_error_exploratory():
    """
    def Td_fit_error(
        td: float,
        relevant_periods: "npt.NDArray",
        relevant_spectrum: "npt.NDArray",
        pga=float,
        sas=float,
        tc=float,
    ) -> float:
    Calculate the spectral fit error term for the selected td value.
    The error is evaluated as the sum of the square root of the absolute difference between
    the fit spectrum and the original spectrum, at relevant periods.

    Args:
        td: spectral-velocity-plateau corner period [seconds]
        relevant_periods: periods included in the relevant domain [seconds]
        relevant_spectrum: spectrum over the relevant periods [g]
        pga: peak ground acceleration [g]
        sas: short-period spectral acceleration [g]
        tc: spectral-acceleration-plateau corner period [seconds]
    """
    ...

    # TODO: figure out what argument and result values are useful, then
    # these can be parametrized ....

    td = 1.0 # seconds
    relevant_periods = np.linspace(0.5, 3.0, num=8) # shaking periods in seconds
    relevant_spectrum = np.linspace(0.25, 5, num=8) # spectra in g
    pga = 1.0
    sas = 0.1
    tc = 1.0

    result = sa_gen.Td_fit_error(td, relevant_periods, relevant_spectrum, pga, sas, tc)

    assert pytest.approx(result, abs=5e-2) == 73 # this passes, but is probably not useful
