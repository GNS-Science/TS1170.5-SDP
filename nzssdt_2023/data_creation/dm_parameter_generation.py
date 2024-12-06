"""
This module compiles the magnitude and distances values for the parameter table.

TODO:
    - `extract_m_values` uses/builds entire mean mag tables independent of what locations and PoEs
        are requested in function args.
    - Consolidate the mean mag csv files into one cache rather than 3 separate files. Any locations/poes
        not available can be looked up and added to the cache.
"""
import itertools
import os
from pathlib import Path
from typing import TYPE_CHECKING, List

import numpy as np
import pandas as pd
from toshi_hazard_store.model import AggregationEnum

from nzssdt_2023.data_creation.constants import DEFAULT_RPS
from nzssdt_2023.data_creation.mean_magnitudes import (
    empty_mean_mag_df,
    frequency_to_poe,
    get_mean_mag,
    get_mean_mag_df,
    read_mean_mag_df,
    site_name_to_coded_location,
)
from nzssdt_2023.data_creation.sa_parameter_generation import replace_relevant_locations

from .util import set_coded_location_resolution

if TYPE_CHECKING:
    import geopandas.typing as gpdt
    import pandas.typing as pdt

from nzssdt_2023.config import DISAGG_HAZARD_ID, RESOURCES_FOLDER, WORKING_FOLDER

# prevent SettingWithCopyWarning
pd.options.mode.copy_on_write = True


def extract_m_values(
    site_names: List[str],
    freqs: List[str],
    agg: AggregationEnum,
    no_cache: bool = False,
    legacy: bool = False,
) -> "pdt.DataFrame":
    """Extracts the magnitudes from the input .csv folder into a manageable dataframe

    Args:
        site_names: names of sites of interest
        frequencies: list of the frequencys (1/return period) of interest
        agg: the aggregate hazard curve at which to calculate mean magnitude (e.g., "mean", "0.9", ...)
        no_cache: if True, ignore the cache file
        legacy: if True double rounds magnitudes to match origional mean mags from v1 of the workflow.

    Returns:
        mags: mean magnitudes

    The format of the frequencies entries is e.g. "APoE: 1/25"

    If no_cache is False then the mean magnitudes will be looked up in a cache file. If not found
    there, they will be calculated and added to the cache. The cache file is in the WORKING_FOLDER
    named mags_{agg}.csv where {agg} is the hazard curve aggregate.

    site names are location names or lat~lon codes e.g. "Pukekohe" or "-45.500~166.600"
    """

    locations = [site_name_to_coded_location(name) for name in site_names]
    poes = [frequency_to_poe(freq) for freq in freqs]

    if no_cache:
        return get_mean_mag_df(DISAGG_HAZARD_ID, locations, poes, agg, legacy)

    cache_filepath = Path(WORKING_FOLDER) / f"mag_agg-{agg.name}.csv"
    if cache_filepath.exists():
        mags = read_mean_mag_df(cache_filepath)
    else:
        poes = [frequency_to_poe(freq) for freq in freqs]
        mags = empty_mean_mag_df(poes)
        mags = get_mean_mag_df(DISAGG_HAZARD_ID, locations, poes, agg, legacy)
        mags.to_csv(cache_filepath)
        return mags.loc[site_names, freqs]

    # fill in the missing values one at a time
    for site, freq in itertools.product(site_names, freqs):
        if (
            (site not in mags.index)
            or (freq not in mags.columns)
            or (pd.isnull(mags.loc[site, freq]))
        ):
            location = site_name_to_coded_location(site)
            poe = frequency_to_poe(freq)
            mag = get_mean_mag(DISAGG_HAZARD_ID, location, poe, agg, legacy)
            mags.loc[site, freq] = mag

    mags.to_csv(cache_filepath)
    return mags.loc[site_names, freqs]


def create_D_and_M_df(
    site_list: List[str],
    rp_list: List[int] = DEFAULT_RPS,
    no_cache: bool = False,
    legacy: bool = False,
) -> "pdt.DataFrame":
    """Compiles the D and M parameter tables

    Args:
        site_list: list of sites of interest
        rp_list    : list of return periods of interest
        no_cache: if True, ignore the cache file
        legacy: if True double rounds magnitudes to match original mean mags from v1 of the workflow.

    Returns:
        D_and_M: dataframe of the d and m tables
    """

    folder = Path(RESOURCES_FOLDER, "pipeline", "v1", "input_data")
    assert os.path.isdir(folder)

    D_values = pd.read_json(Path(folder, "D_values.json"))
    D_sites = [site for site in list(D_values.index) if site in site_list]

    APoEs = [f"APoE: 1/{rp}" for rp in rp_list]

    M_mean = extract_m_values(site_list, APoEs, AggregationEnum.MEAN, no_cache, legacy)
    M_p90 = extract_m_values(["Auckland"], APoEs, AggregationEnum._90, no_cache, legacy)

    D_and_M = pd.DataFrame(index=site_list, columns=["D"] + APoEs)

    # include D values
    D_and_M.loc[D_sites, "D"] = D_values.loc[D_sites, "D"]

    # include M values
    for APoE in APoEs:
        # M value is >= the 90th %ile values for Auckland
        D_and_M.loc[site_list, APoE] = np.maximum(
            M_mean.loc[site_list, APoE], M_p90.loc["Auckland", APoE]
        )

    D_and_M = replace_relevant_locations(D_and_M)
    D_and_M = set_coded_location_resolution(D_and_M)
    return D_and_M
