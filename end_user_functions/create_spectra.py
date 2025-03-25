"""
This module contains end user functions for creating the TS spectra from the tabulated parameters
"""

import numpy as np
import pandas as pd

from end_user_functions.constants import DEFAULT_PERIODS
from nzssdt_2023.data_creation.sa_parameter_generation import uhs_value


def create_spectrum_from_parameters(
    pga, sas, tc, td, periods=DEFAULT_PERIODS, precision=3
):
    """Creates the TS spectrum based on the incoming parameters

    Args:
        pga: peak ground acceleration [g]
        sas: short-period spectral acceleration [g]
        tc: spectral-acceleration-plateau corner period [seconds]
        td: spectral-velocity-plateau corner period [seconds]
        periods: list of periods [seconds] a which to calculate the spectrum
        precision: number of decimals to include in output

    Returns:
        spectrum: acceleration spectrum [g] calculated at the incoming list of periods
    """

    spectrum = np.array(
        [uhs_value(period, pga, sas, tc, td) for period in periods]
    ).round(precision)

    return list(spectrum)
