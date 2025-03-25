"""
This module contains end user functions for creating the TS spectra from the tabulated parameters
"""

import numpy as np
import pandas as pd

from nzssdt_2023.end_user_functions.constants import DEFAULT_PERIODS
from nzssdt_2023.end_user_functions.query_parameters import retrieve_sa_parameters
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


def create_enveloped_spectra(
    location_id, apoe_n, site_class_list, periods=DEFAULT_PERIODS, precision=3
):
    """Creates the set of site class spectra for a given location_id and APoE

    Args:
        location_id: label for a TS location (e.g., 'Wellington' or '-47.3~167.8')
        apoe_n: shorthand for APoE (1/n)  # this is commonly known as a return period
        site_class_list: list of TS site class label (e.g., ['III',IV'])

    Returns:
        enveloped_spectra: df of each site class's spectrum and the combined envelope of them all

    """

    df = pd.DataFrame()
    df["Period"] = periods

    for sc in site_class_list:
        pga, sas, tc, td = retrieve_sa_parameters(location_id, apoe_n, sc)
        df[sc] = create_spectrum_from_parameters(pga, sas, tc, td, periods, precision)

    df["Envelope"] = np.max(df.loc[:, df.columns != "Period"], axis=1)
    enveloped_spectra = df.round(precision)

    return enveloped_spectra
