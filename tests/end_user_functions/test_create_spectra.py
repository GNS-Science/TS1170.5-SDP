"""
tests for creating TS spectra from TS parameters

- functions in `end_user_functions.create_spectra`
"""

import pytest

from end_user_functions.create_spectra import (
    create_enveloped_spectra,
    create_spectrum_from_parameters,
)


@pytest.mark.parametrize(
    "pga, sas, tc, td, periods, expected_spectrum",
    [
        (0.91, 1.84, 0.52, 2.0, [0, 0.5, 1, 1.5, 2], [0.91, 1.84, 0.957, 0.638, 0.478]),
        (0.77, 1.71, 0.66, 2.6, [0, 0.5, 1, 1.5, 2], [0.77, 1.71, 1.129, 0.752, 0.564]),
    ],
)
def test_create_spectrum(pga, sas, tc, td, periods, expected_spectrum):

    assert expected_spectrum == create_spectrum_from_parameters(
        pga, sas, tc, td, periods
    )


@pytest.mark.parametrize(
    "location_id, apoe_n, site_class_list, periods, expected_envelope",
    [
        (
            "Wellington",
            500,
            ["III", "IV"],
            [0, 0.5, 1, 1.5, 2],
            [0.91, 1.84, 1.129, 0.752, 0.564],
        )
    ],
)
def test_create_enveloped_spectra(
    location_id, apoe_n, site_class_list, periods, expected_envelope
):

    envelope = create_enveloped_spectra(location_id, apoe_n, site_class_list, periods)[
        "Envelope"
    ].to_list()

    assert expected_envelope == envelope
