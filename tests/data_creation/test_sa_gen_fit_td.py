"""
test the `fit_Td` and related functions in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

# from collections import namedtuple

import numpy as np
import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen


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

    # these spectral values are interpolated from Wellington, IV, 1/500
    periods = np.arange(0, 10.1, 0.1)  # shaking periods in seconds
    spectrum = np.array(
        [
            0.86224788,
            1.38337982,
            1.82800424,
            1.8950038,
            1.82104588,
            1.71904314,
            1.57814586,
            1.45586884,
            1.34675848,
            1.24527383,
            1.16286707,
            1.07204857,
            0.98123007,
            0.90555633,
            0.84502736,
            0.78449839,
            0.74109324,
            0.69768809,
            0.65955479,
            0.62669334,
            0.5938319,
            0.56307794,
            0.53232399,
            0.50157004,
            0.47081609,
            0.44006214,
            0.42105881,
            0.40205548,
            0.38305216,
            0.36404883,
            0.34504551,
            0.33190709,
            0.31876868,
            0.30563027,
            0.29249185,
            0.27935344,
            0.26994467,
            0.26053591,
            0.25112714,
            0.24171838,
            0.23230961,
            0.2238579,
            0.21540619,
            0.20695448,
            0.19850277,
            0.19005106,
            0.18335436,
            0.17665766,
            0.16996095,
            0.16326425,
            0.15656754,
            0.15211688,
            0.14766621,
            0.14321554,
            0.13876487,
            0.1343142,
            0.12986353,
            0.12541286,
            0.1209622,
            0.11651153,
            0.11206086,
            0.10961958,
            0.10717831,
            0.10473703,
            0.10229576,
            0.09985448,
            0.09741321,
            0.09497193,
            0.09253065,
            0.09008938,
            0.0876481,
            0.08520683,
            0.08276555,
            0.08032428,
            0.077883,
            0.07544173,
            0.07421994,
            0.07299815,
            0.07177636,
            0.07055457,
            0.06933278,
            0.06811099,
            0.06688921,
            0.06566742,
            0.06444563,
            0.06322384,
            0.06200205,
            0.06078026,
            0.05955847,
            0.05833669,
            0.0571149,
            0.05589311,
            0.05467132,
            0.05344953,
            0.05222774,
            0.05100596,
            0.04978417,
            0.04856238,
            0.04734059,
            0.0461188,
            0.04489701,
        ]
    )  # spectra in g
    pga = 0.77
    sas = 1.71
    tc = 0.66

    result = sa_gen.fit_Td(spectrum, periods, pga, sas, tc)

    print(result)
    assert result == 2.6


@pytest.mark.parametrize("tc", [0.75, 0.8])
@pytest.mark.parametrize("inclusive", [False, True])
def test_relevant_spectrum_domain_exploratory(tc, inclusive):
    """spectrum: "npt.NDArray", periods: "npt.NDArray", tc: float, inclusive: bool = False
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

    # these spectral values are interpolated from Wellington, IV, 1/500, stopping at 6.1 seconds
    periods = np.arange(0, 6.2, 0.1)  # shaking periods in seconds
    spectrum = np.array(
        [
            0.86224788, 1.38337982, 1.82800424, 1.8950038, 1.82104588,
            1.71904314, 1.57814586, 1.45586884, 1.34675848, 1.24527383,
            1.16286707, 1.07204857, 0.98123007, 0.90555633, 0.84502736,
            0.78449839, 0.74109324, 0.69768809, 0.65955479, 0.62669334,
            0.5938319, 0.56307794, 0.53232399, 0.50157004, 0.47081609,
            0.44006214, 0.42105881, 0.40205548, 0.38305216, 0.36404883,
            0.34504551, 0.33190709, 0.31876868, 0.30563027, 0.29249185,
            0.27935344, 0.26994467, 0.26053591, 0.25112714, 0.24171838,
            0.23230961, 0.2238579, 0.21540619, 0.20695448, 0.19850277,
            0.19005106, 0.18335436, 0.17665766, 0.16996095, 0.16326425,
            0.15656754, 0.15211688, 0.14766621, 0.14321554, 0.13876487,
            0.1343142, 0.12986353, 0.12541286, 0.1209622, 0.11651153,
            0.11206086, 0.10961958
        ]
    )  # spectra in g

    r_spectrum, r_periods = sa_gen.relevant_spectrum_domain(
        spectrum, periods, tc, inclusive
    )
    n = len(r_periods)

    assert np.all(r_spectrum == spectrum[-n-1:-1])
    assert np.all(r_periods == periods[-n-1:-1])

    if tc == 0.75:
        if inclusive:
            r_periods[0] == 0.7
        else:
            r_periods[0] == 0.8
    elif tc == 0.8:
        if inclusive:
            r_periods[0] == 0.8
        else:
            r_periods[0] == 0.8
    else:
        assert 0


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

    # these spectral values are interpolated from Wellington, IV, 1/500
    periods = np.arange(0, 10.1, 0.1)  # shaking periods in seconds
    spectrum = np.array(
        [
            0.86224788,
            1.38337982,
            1.82800424,
            1.8950038,
            1.82104588,
            1.71904314,
            1.57814586,
            1.45586884,
            1.34675848,
            1.24527383,
            1.16286707,
            1.07204857,
            0.98123007,
            0.90555633,
            0.84502736,
            0.78449839,
            0.74109324,
            0.69768809,
            0.65955479,
            0.62669334,
            0.5938319,
            0.56307794,
            0.53232399,
            0.50157004,
            0.47081609,
            0.44006214,
            0.42105881,
            0.40205548,
            0.38305216,
            0.36404883,
            0.34504551,
            0.33190709,
            0.31876868,
            0.30563027,
            0.29249185,
            0.27935344,
            0.26994467,
            0.26053591,
            0.25112714,
            0.24171838,
            0.23230961,
            0.2238579,
            0.21540619,
            0.20695448,
            0.19850277,
            0.19005106,
            0.18335436,
            0.17665766,
            0.16996095,
            0.16326425,
            0.15656754,
            0.15211688,
            0.14766621,
            0.14321554,
            0.13876487,
            0.1343142,
            0.12986353,
            0.12541286,
            0.1209622,
            0.11651153,
            0.11206086,
            0.10961958,
            0.10717831,
            0.10473703,
            0.10229576,
            0.09985448,
            0.09741321,
            0.09497193,
            0.09253065,
            0.09008938,
            0.0876481,
            0.08520683,
            0.08276555,
            0.08032428,
            0.077883,
            0.07544173,
            0.07421994,
            0.07299815,
            0.07177636,
            0.07055457,
            0.06933278,
            0.06811099,
            0.06688921,
            0.06566742,
            0.06444563,
            0.06322384,
            0.06200205,
            0.06078026,
            0.05955847,
            0.05833669,
            0.0571149,
            0.05589311,
            0.05467132,
            0.05344953,
            0.05222774,
            0.05100596,
            0.04978417,
            0.04856238,
            0.04734059,
            0.0461188,
            0.04489701,
        ]
    )  # spectra in g
    pga = 0.77
    sas = 1.71
    tc = 0.66
    td = 2.6
    relevant_spectrum, relevant_periods = sa_gen.relevant_spectrum_domain(
        spectrum, periods, tc
    )
    result = sa_gen.Td_fit_error(td, relevant_periods, relevant_spectrum, pga, sas, tc)

    assert pytest.approx(result) == 0.013511859172484967
