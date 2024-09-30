import csv
import warnings
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List

import numpy as np
import pandas as pd
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store import model, query

if TYPE_CHECKING:
    import numpy.typing as npt

INV_TIME = 1.0
VS30 = 275
IMT = "PGA"


def lat_lon_from_id(id):
    return (location_by_id(id)["latitude"], location_by_id(id)["longitude"])


coded_locations_with_id = [
    CodedLocation(*lat_lon_from_id(_id), 0.001) for _id in LOCATION_LISTS["ALL"]["locations"]
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


def poe_to_rp_rounded(apoe: model.ProbabilityEnum) -> int:
    """
    Converts annual probability to a rounded retun period. The return periods are "conventional"
    return periods used by the hazard and risk community that are roughly equivlent to the
    (more exact) annual probabilities.

    Args:
        apoe: annual probability of exceedence

    Returns:
        the approximate retun period rounded to the nearest "conventional" number.
    """

    def sig_figs(num, s):
        d = int(np.ceil(np.log10(num)))
        p = s - d
        m = 10**p
        return np.round(num * m) / m

    rp = -1.0 / np.log(1 - apoe.value)
    # This is the dumbest thing ever. I should probably just use a lookup table. Not sure there
    # is an algo that always gives the "conventional" return periods from the apoe.
    if 470 < rp < 1000:
        return int(sig_figs(rp, s=1))
    return int(sig_figs(rp, s=2))


def get_mean_mag_df(
    hazard_id: str,
    locations: List[CodedLocation],
    poes: model.ProbabilityEnum,
    hazard_agg: model.AggregationEnum,
    legacy: bool=True,
) -> pd.DataFrame:
    """
    Get the mean mantitude table for the requested locations and annual probabilities.

    Args:
        hazard_id: the toshi-hazard-post ID of the hazard model from which to get disaggregations.
        locations: the locations at which to calculate mean magnitudes.
        poes: the annual probabilities of exceedences at which to calculate mean magnitudes.
        hazard_agg: the hazard aggregate (e.g. mean or a fractile) at which to calculate mean magnitudes.
        legacy: double rounds magnitudes to match origional mean mags from v1 of the workflow.

    Returns:
        the mean magnitues. The DataFrame index is the location name and the columns are frequencies.

    The legacy calculation is necessary to match the origional mean magnitude dataframe becuase the orignal
    csv file had magnitudes rounded to 2 decimal places. When the final ouput is rounded to one decimal
    place, this results in rounding errors. For example:
    >>> round(5.948071422587211, 1)
    5.9
    >>> round(round(5.948071422587211, 2), 1)
    6.0

    NB: "APoE in the column name is a misnomer as they are approximate return frequencies not probabilities.
    Magnitudes are rounded to the nearest decimal. The rounding error introduced in the origional workflow
    (incurred by rounding to the nearest 2 decimal places and then nearest 1) have been reproduced
    here to ensure output is stable.

    The format of the output DataFrame is:

                    APoE: 1/25 APoE: 1/50 APoE: 1/100 APoE: 1/250 APoE: 1/500 APoE: 1/1000 APoE: 1/2500
    Kaitaia             5.7        5.8         5.8         5.9         6.0          6.0          6.1
    Kerikeri            5.7        5.8         5.9         5.9         6.0          6.0          6.1
    ...                 ...        ...         ...         ...         ...          ...          ...
    Bluff               6.7        6.8         6.9         7.0         7.0          7.1          7.1
    Oban                6.7        6.8         6.9         7.0         7.1          7.2          7.3
    """

    def get_rp_str(rp: int):
        return f"APoE: 1/{rp}"

    return_periods = np.array([poe_to_rp_rounded(poe) for poe in poes])
    return_periods = np.sort(return_periods)
    rp_strs = [get_rp_str(rp) for rp in return_periods]
    site_names = [
        get_loc_id_and_name(loc.downsample(0.001).code)[1] for loc in locations
    ]
    df = pd.DataFrame(index=site_names, columns=rp_strs)
    for disagg in get_mean_mags(hazard_id, locations, [VS30], [IMT], poes, hazard_agg):
        rp = poe_to_rp_rounded(disagg["poe"])
        rp_str = get_rp_str(rp)
        site_name = disagg["name"]
        if legacy:
            df.loc[site_name, rp_str] = np.round(np.round(disagg["mag"], 2), 1)
        else:
            df.loc[site_name, rp_str] = np.round(disagg["mag"], 1)

    return df


def write_mean_mag_csv_file(
    hazard_id, locations, vs30s, imts, poes, hazard_agg, filepath
):
    warnings.warn("Please use get_mean_mag_df instead", DeprecationWarning)

    header = [
        "site code",
        "site name",
        "latitude",
        "longitude",
        "vs30",
        "poe (% in 50 years)",
        "imt",
        "imtl (g)",
        "mean magnitude",
    ]
    with open(filepath, "w") as meanmag_file:
        writer = csv.writer(meanmag_file)
        writer.writerow(header)
        for disagg in get_mean_mags(
            hazard_id, locations, vs30s, imts, poes, hazard_agg
        ):
            writer.writerow(
                [
                    disagg["location_id"],
                    disagg["name"],
                    disagg["lat"],
                    disagg["lon"],
                    disagg["vs30"],
                    disagg["poe"],
                    disagg["imt"],
                    disagg["imtl"],
                    disagg["mag"],
                ]
            )


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
