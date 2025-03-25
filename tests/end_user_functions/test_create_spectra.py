"""
tests for creating TS spectra from TS parameters

- functions in `end_user_functions.create_spectra`
"""

import pytest

from end_user_functions.create_spectra import create_spectrum_from_parameters


@pytest.mark.parametrize(
    "pga, sas, tc, td, periods, spectrum",
    [
        (0.77, 1.71, 0.66, 2.6, [0, 0.5, 1, 1.5, 2], [0.77, 1.71, 1.129, 0.752, 0.564]),
        (
            0.06,
            0.12,
            0.45,
            2.4,
            [0, 0.5, 1, 1.5, 2],
            [0.06, 0.108, 0.054, 0.036, 0.027],
        ),
    ],
)
def test_create_spectrum(pga, sas, tc, td, periods, spectrum):

    assert spectrum == create_spectrum_from_parameters(pga, sas, tc, td, periods)
