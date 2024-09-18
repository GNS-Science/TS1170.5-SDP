"""
Some developer oriented docs about this module.
"""
import numpy as np
import pandas as pd
from nzshm_common.grids import RegionGrid
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.query import get_hazard_curves

### parameters for NSHM query, as required for the TS Site Demand Parameter tables
###    note: sites is defined after create_sites_df is defined
hazard_id = "NSHM_v1.0.4"

agg_list = ["mean", "0.9"]
vs30_list = [150, 175, 225, 250, 275, 375, 400, 525, 750]
imt_list = [
    "PGA",
    "SA(0.1)",
    "SA(0.15)",
    "SA(0.2)",
    "SA(0.25)",
    "SA(0.3)",
    "SA(0.35)",
    "SA(0.4)",
    "SA(0.5)",
    "SA(0.6)",
    "SA(0.7)",
    "SA(0.8)",
    "SA(0.9)",
    "SA(1.0)",
    "SA(1.25)",
    "SA(1.5)",
    "SA(1.75)",
    "SA(2.0)",
    "SA(2.5)",
    "SA(3.0)",
    "SA(3.5)",
    "SA(4.0)",
    "SA(4.5)",
    "SA(5.0)",
    "SA(6.0)",
    "SA(7.5)",
    "SA(10.0)",
]


def create_sites_df(
    named_sites=True,
    site_list=None,
    cropped_grid=False,
    grid_limits=[-np.inf, np.inf, -np.inf, np.inf],
):
    """
    creates a pd dataframe of the sites of interest

    :param named_sites:  boolean       True returns SRG sites, False returns lat/lon sites
    :param site_list:    None or list  specifies a subset of SRG sites
    :param cropped_grid: boolean       True returns all lat/lon sites, False crops to grid_limits
    :param grid_limits:  list          [min_lat, max_lat, min_lon, max_lon]

    :return: sites:      pd dataframe  idx: sites, cols: ['latlon', 'lat', 'lon']
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
        site_list = "NZ_0_1_NB_1_1"
        resample = 0.1
        grid = RegionGrid[site_list]
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


sites = pd.concat([create_sites_df(), create_sites_df(named_sites=False)])


def retrieve_hazard_curves(sites, vs30_list, imt_list, agg_list, hazard_id):
    """
    retrieves the hazard curves for the sites, vs30s, imts, and aggs of interest

    :param sites: pd dataframe  idx: sites, cols: ['latlon', 'lat', 'lon']
    :param vs30_list: list  vs30s of interest
    :param imt_list:  list  imts of interest
    :param agg_list:  list  agg types of interest (e.g., mean or "0.f" where f is a fractile
    :param hazard_id: string required query the NSHM

    :return: np.array   hazard curves indexed by [n_vs30s, n_sites, n_imts, n_imtls, n_aggs]
             list   intensities included
    """

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

    print("Querying hazard curves...")

    # cycle through all hazard parameters
    for res in get_hazard_curves(
        sites["latlon"], vs30_list, [hazard_id], imt_list, agg_list
    ):
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
