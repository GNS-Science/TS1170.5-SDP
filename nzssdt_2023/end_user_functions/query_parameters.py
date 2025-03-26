"""
This module contains end user functions for querying the TS table
"""

from typing import TYPE_CHECKING, Tuple

import numpy as np
import pandas as pd

from nzssdt_2023.end_user_functions.constants import (
    APOE_N_THRESHOLD_FOR_D,
    APOE_NS,
    APOES,
    PARAMETER_TABLE,
    SA_PARAMETER_NAMES,
    SITE_CLASSES,
)

if TYPE_CHECKING:
    import pandas.typing as pdt


def retrieve_sa_parameters(
    location_id: str, apoe_n: int, site_class: str
) -> Tuple[float, float, float, float]:
    """retrieves the spectral acceleration parameters for a single line of the TS table

    Args:
        location_id: label for a TS location (e.g., 'Wellington' or '-47.3~167.8')
        apoe_n: shorthand for APoE (1/n)  # this is commonly known as a return period
        site_class: TS site class label (e.g., 'IV')

    Returns:
        pga: peak ground acceleration
        sas: short-period acceleration
        tc: spectral-acceleration-plateau corner period
        td: spectral-velocity-plateau corner period
    """

    loc_idx = PARAMETER_TABLE["Location"] == location_id
    apoe_idx = PARAMETER_TABLE["APoE (1/n)"] == apoe_n
    sc_idx = PARAMETER_TABLE["Site Class"] == site_class

    idx = loc_idx & apoe_idx & sc_idx
    pga, sas, tc, td = PARAMETER_TABLE[idx][SA_PARAMETER_NAMES].iloc[0]

    return pga, sas, tc, td


def retrieve_md_parameters(
    location_id: str, apoe_n: int, site_class: str
) -> Tuple[float, float | str]:
    """retrieves the M and D parameters for a single line of the TS table

    Args:
        location_id: label for a TS location (e.g., 'Wellington' or '-47.3~167.8')
        apoe_n: shorthand for APoE (1/n)  # this is commonly known as a return period
        site_class: TS site class label (e.g., 'IV')

    Returns:
        m: earthquake magnitude
        d: distance to nearest fault
    """

    loc_idx = PARAMETER_TABLE["Location"] == location_id
    apoe_idx = PARAMETER_TABLE["APoE (1/n)"] == apoe_n
    sc_idx = PARAMETER_TABLE["Site Class"] == site_class

    idx = loc_idx & apoe_idx & sc_idx
    m, d = PARAMETER_TABLE[idx][["M", "D"]].iloc[0]

    # d values are NAN for high APoE (low apoe_n)
    if apoe_n < APOE_N_THRESHOLD_FOR_D:
        d = np.nan

    return m, d


def parameters_by_location_id(location_id: str) -> "pdt.DataFrame":
    """retrieves all parameters associated with a given location id

    Args:
        location_id: label for a TS location (e.g., Wellington or -47.3~167.8)

    Returns:
        df: dataframe with all the parameters
    """

    # initialize df for sa parameters
    index = pd.Index(APOES, name="APoE")
    columns = pd.MultiIndex.from_product(
        [SITE_CLASSES, SA_PARAMETER_NAMES], names=["Site Class", "Parameter"]
    )
    sa_df = pd.DataFrame(index=index, columns=columns)

    for apoe_n in APOE_NS:
        apoe = f"1/{apoe_n}"
        for site_class in SITE_CLASSES:
            sa_df.loc[(apoe), (site_class, slice(None))] = retrieve_sa_parameters(
                location_id, apoe_n, site_class
            )

    # initialize df for dm parameters
    columns = pd.MultiIndex.from_tuples(
        [("", "M"), ("", "D")], names=["Site Class", "Parameter"]
    )
    md_df = pd.DataFrame(index=index, columns=columns)
    for apoe_n in APOE_NS:
        apoe = f"1/{apoe_n}"
        for site_class in [SITE_CLASSES[0]]:
            m, d = retrieve_md_parameters(location_id, apoe_n, site_class)
            md_df.loc[(apoe), ("", "M")] = m
            md_df.loc[(apoe), ("", "D")] = d

    # combine md and sa parameters
    df = pd.concat([md_df, sa_df], axis=1)

    return df
