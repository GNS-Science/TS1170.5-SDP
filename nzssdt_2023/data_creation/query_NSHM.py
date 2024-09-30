"""
Functions to get hazard data from the NSHM hazard API.

"""
import datetime
import datetime as dt
import logging
from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np
import pandas as pd
from nzshm_common.grids import RegionGrid
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.query import get_hazard_curves

if TYPE_CHECKING:
    import numpy.typing as npt
    import pandas.typing as pdt

log = logging.getLogger(__name__)


def create_sites_df(
    named_sites: bool = True,
    site_list: Optional[List[str]] = None,
    cropped_grid: bool = False,
    grid_limits: Tuple[float, float, float, float] = (-np.inf, np.inf, -np.inf, np.inf),
) -> "pdt.DataFrame":
    """
    creates a pd dataframe of the sites of interest

    Args:
        named_sites: if True returns SRG sites, False returns lat/lon sites
        site_list:  specifies a subset of SRG sites
        cropped_grid:  True returns all lat/lon sites, False crops to grid_limits
        grid_limits: set outer bound coordinates of the grid [min_lat, max_lat, min_lon, max_lon]

    Returns:
        a dataframe idx: sites, cols: ['latlon', 'lat', 'lon']
    """

    # create a dataframe with named sites
    if named_sites:
        id_list = LOCATION_LISTS["SRWG214"]["locations"]

        # if no list is passed, include all named sites
        if site_list is None:
            site_list = [location_by_id(loc_id)["name"] for loc_id in id_list]

        # collect the ids for the relevant sites
        id_list = [
            loc_id for loc_id in id_list if location_by_id(loc_id)["name"] in site_list
        ]

        # create the df of named sites
        sites = pd.DataFrame(index=site_list, dtype="str")
        for loc_id in id_list:
            latlon = CodedLocation(
                location_by_id(loc_id)["latitude"],
                location_by_id(loc_id)["longitude"],
                0.001,
            ).code
            lat, lon = latlon.split("~")
            sites.loc[location_by_id(loc_id)["name"], ["latlon", "lat", "lon"]] = [
                latlon,
                lat,
                lon,
            ]

    # create a dataframe with latlon sites
    else:
        site_list_id = "NZ_0_1_NB_1_1"
        resample = 0.1
        grid = RegionGrid[site_list_id]
        grid_locs = grid.load()

        # remove empty location
        i_loc = grid_locs.index((-34.7, 172.7))
        grid_locs = grid_locs[0:i_loc] + grid_locs[i_loc + 1 :]

        site_list = []
        for gloc in grid_locs:
            loc = CodedLocation(*gloc, resolution=0.001)
            loc = loc.resample(float(resample)) if resample else loc
            site_list.append(loc.resample(0.001).code)

        # create the df of gridded locations
        sites = pd.DataFrame(index=site_list, dtype="str")
        for latlon in site_list:
            lat, lon = latlon.split("~")
            sites.loc[latlon, ["latlon", "lat", "lon"]] = [latlon, lat, lon]

        # remove sites based on latlon
        if cropped_grid:
            min_lat, max_lat, min_lon, max_lon = grid_limits
            sites["float_lat"] = [float(lat) for lat in sites["lat"]]
            sites = sites[
                (sites["float_lat"] >= min_lat) & (sites["float_lat"] <= max_lat)
            ].drop(["float_lat"], axis=1)
            sites["float_lon"] = [float(lon) for lon in sites["lon"]]
            sites = sites[
                (sites["float_lon"] >= min_lon) & (sites["float_lon"] <= max_lon)
            ].drop(["float_lon"], axis=1)

        sites.sort_values(["lat", "lon"], inplace=True)

    return sites


def retrieve_hazard_curves(
    sites: "pdt.DataFrame",
    vs30_list: List[int],
    imt_list: List[str],
    agg_list: List[str],
    hazard_id: str,
) -> Tuple["npt.NDArray", List[float]]:
    """
    retrieves the hazard curves for the sites, vs30s, imts, and aggs of interest

    Args:
        sites: idx: sites, cols: ['latlon', 'lat', 'lon']
        vs30_list:  vs30s of interest
        imt_list:   imts of interest
        agg_list:   agg types of interest (e.g., mean or "0.f" where f is a fractile
        hazard_id:  query the NSHM

    Returns:
        np.array   hazard curves indexed by [n_vs30s, n_sites, n_imts, n_imtls, n_aggs]
             list   intensities included
    """

    log.info(
        f"begin retrieve_hazard_curves for {len(sites)} sites; {len(vs30_list)} vs30;  {len(agg_list)} aggs;"
    )

    # call a location to get the imtls that are returned
    res = next(
        get_hazard_curves(
            sites["latlon"][:1], vs30_list[:1], [hazard_id], imt_list[:1], agg_list[:1]
        )
    )
    imtl_list = [float(val.lvl) for val in res.values]

    # initialize hcurves
    hcurves = -1 * np.ones(
        [len(vs30_list), len(sites), len(imt_list), len(imtl_list), len(agg_list)]
    )

    log.info("Querying hazard curves...")

    # cycle through all hazard parameters
    count = 0
    CHUNK = 1000
    expected_count = (
        len(sites["latlon"]) * len(vs30_list) * len(imt_list) * len(agg_list)
    )
    timings = []
    t0 = dt.datetime.now()
    for res in get_hazard_curves(
        sites["latlon"], vs30_list, [hazard_id], imt_list, agg_list
    ):
        count += 1
        delta = dt.datetime.now() - t0
        duration = delta.seconds + delta.microseconds / 1e6
        timings.append(duration)  # time.delta
        if count % CHUNK == 0:
            eta = dt.datetime.now() + dt.timedelta(
                seconds=(expected_count - count) * sum(timings[-10:]) / 10
            )
            log.info(
                f"retrieve_hazard_curves progress: {count} of {expected_count}. "
                f"Approx {(count/expected_count) * 100:.1f} % progress. "
                f"Last {CHUNK} curves took {sum(timings):.4f}s. "
                f"ETA: {eta}"
            )
            timings = []

        lat = res.lat
        lon = res.lon
        vs30 = res.vs30
        imt = res.imt
        agg = res.agg

        i_site = np.where(sites["latlon"] == f"{lat:.3f}~{lon:.3f}")
        i_vs30 = vs30_list.index(vs30)
        i_imt = imt_list.index(imt)
        i_agg = agg_list.index(agg)

        hcurves[i_vs30, i_site, i_imt, :, i_agg] = [val.val for val in res.values]
        t0 = dt.datetime.now()

    # # identify any missing data and produce a warning
    site_list = list(sites.index)

    if np.sum(hcurves < 0) != 0:
        vs30_idx, site_idx, imt_idx, imtl_idx, agg_idx = np.where(hcurves < 0)

        print("\nMissing NSHM data from:")
        print(f"\t{[vs30_list[idx] for idx in np.unique(vs30_idx)]}")
        if len(np.unique(site_idx)) > 5:
            print(
                f"\t{[site_list[idx] for idx in np.unique(site_idx)[:5]]} and more..."
            )
        else:
            print(f"\t{[site_list[idx] for idx in np.unique(site_idx)]}")
        print(f"\t{[imt_list[idx] for idx in np.unique(imt_idx)]}")
        print(f"\t{[agg_list[idx] for idx in np.unique(agg_idx)]}")

    return hcurves, imtl_list
