import csv
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable

import numpy as np
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store import model, query

if TYPE_CHECKING:
    import numpy.typing as npt

INV_TIME = 1.0


def lat_lon(id):
    return (location_by_id(id)["latitude"], location_by_id(id)["longitude"])


coded_locations_with_id = [
    CodedLocation(*lat_lon(_id), 0.001) for _id in LOCATION_LISTS["ALL"]["locations"]
]
location_codes_with_id = [loc.code for loc in coded_locations_with_id]


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
        if disagg.nloc_001 in location_codes_with_id:
            location_id = LOCATION_LISTS["ALL"]["locations"][
                location_codes_with_id.index(disagg.nloc_001)
            ]
            name = location_by_id(location_id)["name"]
        else:
            location_id = disagg.nloc_001
            name = disagg.nloc_001
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


def write_mean_mag_file(hazard_id, locations, vs30s, imts, poes, hazard_agg, filepath):

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
        # model.ProbabilityEnum._5_PCT_IN_50YRS,
        # model.ProbabilityEnum._10_PCT_IN_50YRS,
        # model.ProbabilityEnum._18_PCT_IN_50YRS,
        # model.ProbabilityEnum._39_PCT_IN_50YRS,
        # model.ProbabilityEnum._63_PCT_IN_50YRS,
        # model.ProbabilityEnum._86_PCT_IN_50YRS,
    ]
    # grid_01 = set([CodedLocation(*pt, 0.001) for pt in load_grid('NZ_0_1_NB_1_1')])
    # locations = list(grid_01)
    locations = [
        CodedLocation(*lat_lon(_id), 0.001)
        for _id in LOCATION_LISTS["SRWG214"]["locations"][0:10]
    ]

    # hazard_agg = model.AggregationEnum._90
    hazard_agg = model.AggregationEnum.MEAN

    write_mean_mag_file(
        hazard_id, locations, vs30s, imts, poes, hazard_agg, mean_mag_filepath
    )
