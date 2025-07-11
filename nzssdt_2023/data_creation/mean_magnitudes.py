"""
This module contains functions for extracting mean magnitudes from disaggregations and packaging into DataFrame objects.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Union

import numpy as np
import pandas as pd
from nzshm_common.location import CodedLocation, location_by_id
from nzshm_common.location.location import LOCATION_LISTS
from toshi_hazard_store import model, query

from .constants import ALL_SITES, POE_TO_RP, RP_TO_POE, lat_lon_from_id

if TYPE_CHECKING:
    import numpy.typing as npt

INV_TIME = 1.0
VS30 = 275
IMT = "PGA"
DTYPE = float


coded_locations_with_id = [
    CodedLocation(*lat_lon_from_id(_id), 0.001)
    for _id in LOCATION_LISTS["ALL"]["locations"]
]
location_codes_with_id = [loc.code for loc in coded_locations_with_id]


def get_loc_id_and_name(location_code):

    if location_code in location_codes_with_id:
        location_id = LOCATION_LISTS["ALL"]["locations"][
            location_codes_with_id.index(location_code)
        ]
        name = location_by_id(location_id)["name"]
    else:
        location_id = location_code
        name = location_code

    return location_id, name


def site_name_to_coded_location(site_name: str) -> CodedLocation:
    """get the coded location from the site name

    Args:
        site_name: the site name

    Returns:
        the coded location

    site names are e.g. "Pukekohe", "Tairua", "-45.600~166.600", or "-45.500~166.600"
    """

    if not ("~" in site_name or site_name in ALL_SITES):
        raise ValueError(
            "site_name must be in list of site names or take form `lat~lon`"
        )

    if "~" in site_name:
        lat, lon = map(float, site_name.split("~"))
        return CodedLocation(lat, lon, resolution=0.001)

    loc = ALL_SITES[site_name]
    return CodedLocation(loc["latitude"], loc["longitude"], resolution=0.001)


def prob_to_rate(prob: "npt.NDArray") -> "npt.NDArray":
    return -np.log(1.0 - prob) / INV_TIME


def calculate_mean_magnitude(disagg: "npt.NDArray", bins: "npt.NDArray"):
    """
    Calculate the mean magnitude for a single site using the magnitude disaggregation.

    Parameters:
        disaggregation: The probability contribution to hazard of the magnitude bins (in apoe).
        bins: The bin centers of the magnitude disaggregation.

    Returns:
        the mean magnitude
    """
    shape_bins = bins.shape
    shape_disagg = disagg.shape
    if (
        len(shape_bins) != 2
        or shape_bins[0] != 1
        or shape_bins[1] != len(disagg)
        or len(shape_disagg) != 1
    ):
        raise Exception(
            """Disaggregation does not have the correct shape.
            This function assumes that disaggregations are for magnitude only."""
        )

    disagg = prob_to_rate(disagg)

    return np.sum(disagg / np.sum(disagg) * bins[0])


def get_mean_mags(
    hazard_id: str,
    locations: Iterable[CodedLocation],
    vs30s: Iterable[int],
    imts: Iterable[str],
    poes: Iterable[model.ProbabilityEnum],
    hazard_agg: model.AggregationEnum,
) -> Generator[Dict[str, Any], None, None]:
    """
    The mean magnitudes for a collection of sites.

    This function uses `toshi-hazard-store` to retrieve disaggregations from the database and therefore requires read
    access. It assumes all disaggregations are done for magnitude only (i.e., not distance, epsilon, etc.)

    Parameters:
        hazard_id: the hazard id of the model in the database.
        locations: the site locations for which to obtain the mean magnitude.
        vs30s: the site vs30 values for which to obtain the mean magnitude.
        imts: the intensity measure types for which to obtain the mean magnitude.
        poes: the probability of exeedances for which to obtain the mean magnitude.
        aggregate: the hazard curve aggregation at which to obtain the mean magnitude (e.g. mean, 20th percentile, etc.)

    Yields:
        A dict for each location, vs30, imt, poe, aggregate with keys:
            location_id: str, the locaiton id from `nzshm-common` if the location has one
            name: str, the location name from `nzshm-common` if the location has one
            lat: float, the latitude
            lon: float, the longitude
            vs30: int, the vs30
            poe: model.ProbabilityEnum, the probability of exeedance
            imt: str, the intensity measure type
            imtl: float, the intensity level of the hazard curve at the poe of interest
            mag: float, the mean magnitude
    """

    clocs = [loc.code for loc in locations]
    disaggs = query.get_disagg_aggregates(
        hazard_model_ids=[hazard_id],
        disagg_aggs=[model.AggregationEnum.MEAN],
        hazard_aggs=[hazard_agg],
        locs=clocs,
        vs30s=vs30s,
        imts=imts,
        probabilities=poes,
    )
    for disagg in disaggs:
        mean_mag = calculate_mean_magnitude(disagg.disaggs, disagg.bins)
        location_id, name = get_loc_id_and_name(disagg.nloc_001)

        d = dict(
            location_id=location_id,
            name=name,
            lat=disagg.lat,
            lon=disagg.lon,
            vs30=disagg.vs30,
            poe=disagg.probability,
            imt=disagg.imt,
            imtl=disagg.shaking_level,
            mag=mean_mag,
        )
        yield d


def frequency_to_poe(frequency: str) -> model.ProbabilityEnum:
    """
    converts a frequency string (e.g., "APoE: 1/25") to a annual probability of exceedance

    Args:
        frequency: the frequency string

    Returns:
        the annual probability of exceedance
    """

    rp = int(frequency.split("/")[1])
    return RP_TO_POE[rp]


def poe_to_rp(apoe: model.ProbabilityEnum) -> int:
    """
    Converts annual probability to a rounded return period. The return periods are "conventional"
    return periods used by the hazard and risk community that are roughly equivalent to the
    (more exact) annual probabilities.

    Args:
        apoe: annual probability of exceedance

    Returns:
        the approximate return period rounded to the nearest "conventional" number.
    """

    return POE_TO_RP[apoe]


def read_mean_mag_df(filepath: Union[Path, str]) -> pd.DataFrame:
    df = pd.read_csv(Path(filepath), index_col=["site_name"])
    return df.astype(DTYPE)


def rp_to_freqstr(rp: int):
    return f"APoE: 1/{rp}"


def get_sorted_rp_strs(poes: List[model.ProbabilityEnum]) -> List[str]:
    return_periods = np.array([poe_to_rp(poe) for poe in poes])
    return_periods = np.sort(return_periods)
    return [rp_to_freqstr(rp) for rp in return_periods]


def empty_mean_mag_df(poes: List[model.ProbabilityEnum]) -> pd.DataFrame:
    rp_strs = get_sorted_rp_strs(poes)
    return pd.DataFrame(
        index=pd.Series([], name="site_name"), columns=rp_strs, dtype=DTYPE
    )


def get_mean_mag_df(
    hazard_id: str,
    locations: List[CodedLocation],
    poes: List[model.ProbabilityEnum],
    hazard_agg: model.AggregationEnum,
    legacy: bool = False,
) -> pd.DataFrame:
    """
    Get the mean magnitude table for the requested locations and annual probabilities.

    Args:
        hazard_id: the toshi-hazard-post ID of the hazard model from which to get disaggregations.
        locations: the locations at which to calculate mean magnitudes.
        poes: the annual probabilities of exceedences at which to calculate mean magnitudes.
        hazard_agg: the hazard aggregate (e.g. mean or a fractile) at which to calculate mean magnitudes.
        legacy: if True double rounds magnitudes to match origional mean mags from v1 of the workflow.

    Returns:
        the mean magnitudes. The DataFrame index is the location name and the columns are frequencies.

    The legacy calculation is necessary to match the original mean magnitude dataframe because the original
    csv file had magnitudes rounded to 2 decimal places. When the final output is rounded to one decimal
    place, this results in rounding errors. For example:
    ```python
    >>> round(5.948071422587211, 1)
    5.9
    >>> round(round(5.948071422587211, 2), 1)
    6.0
    ```

    NB: "APoE in the column name is a misnomer as they are approximate return frequencies not probabilities.
    Magnitudes are rounded to the nearest decimal. The rounding error introduced in the original workflow
    (incurred by rounding to the nearest 2 decimal places and then nearest 1) have been reproduced
    here to ensure output is stable.

    The format of the output DataFrame is:

    ```
                    APoE: 1/25 APoE: 1/50 APoE: 1/100 APoE: 1/250 APoE: 1/500 APoE: 1/1000 APoE: 1/2500
    Kaitaia             5.7        5.8         5.8         5.9         6.0          6.0          6.1
    Kerikeri            5.7        5.8         5.9         5.9         6.0          6.0          6.1
    ...                 ...        ...         ...         ...         ...          ...          ...
    Bluff               6.7        6.8         6.9         7.0         7.0          7.1          7.1
    Oban                6.7        6.8         6.9         7.0         7.1          7.2          7.3
    ```
    """

    rp_strs = get_sorted_rp_strs(poes)
    site_names = [
        get_loc_id_and_name(loc.downsample(0.001).code)[1] for loc in locations
    ]
    df = pd.DataFrame(index=site_names, columns=rp_strs, dtype=DTYPE)
    for disagg in get_mean_mags(hazard_id, locations, [VS30], [IMT], poes, hazard_agg):
        rp = poe_to_rp(disagg["poe"])
        rp_str = rp_to_freqstr(rp)
        site_name = disagg["name"]
        if legacy:
            df.loc[site_name, rp_str] = np.round(np.round(disagg["mag"], 2), 1)
        else:
            df.loc[site_name, rp_str] = np.round(disagg["mag"], 1)

    df.index.name = "site_name"
    return df


def get_mean_mag(
    hazard_id: str,
    location: CodedLocation,
    poe: model.ProbabilityEnum,
    hazard_agg: model.AggregationEnum,
    legacy: bool = False,
) -> float:
    """
    Get a mean mantitudefor a single location and poe.

    Args:
        hazard_id: the toshi-hazard-post ID of the hazard model from which to get disaggregations.
        location: the location at which to calculate mean magnitude.
        poe: the annual probability of exceedence at which to calculate mean magnitude.
        hazard_agg: the hazard aggregate (e.g. mean or a fractile) at which to calculate mean magnitude.
        legacy: if True double rounds magnitude to match origional mean mag from v1 of the workflow.

    Returns:
        the mean magnitue

    The legacy calculation is necessary to match the origional mean magnitude dataframe becuase the orignal
    csv file had magnitudes rounded to 2 decimal places. When the final ouput is rounded to one decimal
    place, this results in rounding errors. For example:
    ```python
    >>> round(5.948071422587211, 1)
    5.9
    >>> round(round(5.948071422587211, 2), 1)
    6.0
    ```
    """

    disagg = next(
        get_mean_mags(hazard_id, [location], [VS30], [IMT], [poe], hazard_agg)
    )
    if legacy:
        return np.round(np.round(disagg["mag"], 2), 1)
    else:
        return np.round(disagg["mag"], 1)


if __name__ == "__main__":

    mean_mag_filepath = "mean_mag.csv"
    hazard_id = "NSHM_v1.0.4_mag"
    imts = ["PGA"]
    vs30s = [275]
    poes = [
        model.ProbabilityEnum._2_PCT_IN_50YRS,
        model.ProbabilityEnum._5_PCT_IN_50YRS,
        model.ProbabilityEnum._10_PCT_IN_50YRS,
        model.ProbabilityEnum._18_PCT_IN_50YRS,
        model.ProbabilityEnum._39_PCT_IN_50YRS,
        model.ProbabilityEnum._63_PCT_IN_50YRS,
        model.ProbabilityEnum._86_PCT_IN_50YRS,
    ]
    # grid_01 = set([CodedLocation(*pt, 0.001) for pt in load_grid('NZ_0_1_NB_1_1')])
    # locations = list(grid_01)
    locations = [
        CodedLocation(*lat_lon_from_id(_id), 0.001)
        for _id in LOCATION_LISTS["SRWG214"]["locations"]
    ]

    # hazard_agg = model.AggregationEnum._90
    hazard_agg = model.AggregationEnum.MEAN

    df = get_mean_mag_df(hazard_id, locations, poes, hazard_agg)
    df.to_csv(mean_mag_filepath)
