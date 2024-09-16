import os
import re

import h5py
import numpy as np
import pandas as pd
from nzshm_common.grids import RegionGrid
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from toshi_hazard_store.query import get_hazard_curves

### parameters for NSHM query
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


def period_from_imt(imt):
    """
    retrieves period in seconds from the intensity measure type

    :param imt: string  intensity measure type

    :return: float  period
    """

    if imt in ["PGA", "PGD"]:
        period = 0
    else:
        period = float(re.split(r"\(|\)", imt)[1])

    return period


def acc_to_disp(acc, t):
    """

    :param acc: float   intensity in acceleration [g]
    :param t: float     time in seconds

    :return: float      intensity in displacement [m]
    """

    g = 9.80665  # gravity in m/s^2

    return (acc * g) * (t / (2 * np.pi)) ** 2


def convert_imtls_to_disp(acc_imtls):
    """
    converts the acceleration intensity measure types and levels to spectral displacements

    :param acc_imtls: dictionary   keys: acc intensity measure names, values: intensity levels

    :return: dictionary   keys: disp intensity measure names, values: intensity levels
    """

    disp_imtls = {}
    for acc_imt in acc_imtls.keys():
        period = period_from_imt(acc_imt)
        disp_imt = acc_imt.replace("A", "D")

        disp_imtls[disp_imt] = acc_to_disp(
            np.array(acc_imtls[acc_imt]), period
        ).tolist()

    return disp_imtls


def calculate_hazard_design_intensities(data, hazard_rps, intensity_type="acc"):
    """
    calculate design intensities based on an annual probability of exceedance (APoE)

    :param data: dictionary containing hazard curves and metadata for vs30, sites, intensity measures
    :param hazard_rps: np array containing the desired return periods (1 / APoE)

    :return: np arrays for all intensities from the hazard curve realizations and stats (mean and quantiles)
    """

    # vs30s = data['metadata']['vs30s']
    imtls = data["metadata"][f"{intensity_type}_imtls"]
    hcurves_stats = np.array(data["hcurves"]["hcurves_stats"])

    [n_vs30, n_sites, n_imts, n_imtls, n_stats] = hcurves_stats.shape

    n_rps = len(hazard_rps)

    stats_im_hazard = np.zeros([n_vs30, n_sites, n_imts, n_rps, n_stats])

    for i_vs30 in range(n_vs30):
        for i_site in range(n_sites):
            for i_imt, imt in enumerate(imtls.keys()):

                # loop over the median and any quantiles
                for i_stat in range(n_stats):
                    # the interpolation is done as a linear interpolation in logspace
                    # all inputs are converted to the natural log and the output is converted back via the exponent
                    stats_im_hazard[i_vs30, i_site, i_imt, :, i_stat] = np.exp(
                        np.interp(
                            np.log(1 / hazard_rps),
                            np.log(
                                np.flip(hcurves_stats[i_vs30, i_site, i_imt, :, i_stat])
                            ),
                            np.log(np.flip(imtls[imt])),
                        )
                    )

    return stats_im_hazard


def add_uniform_hazard_spectra(
    data, hazard_rps=np.array([25, 50, 100, 250, 500, 1000, 2500])
):
    """
    Adds uniform hazard spectra to the data dictionary, based on the input hazard_rps

    :param data: dictionary containing hazard curves and metadata for vs30, sites, intensity measures
    :param hazard_rps: np.array  list of return periods of interest (inverse of annual probability of exceedance, apoe)

    :return: updated dictionary includes design intensities
    """

    imtls = data["metadata"]["acc_imtls"]
    data["metadata"]["disp_imtls"] = convert_imtls_to_disp(imtls)

    # get poe values
    print("Calculating APoE intensities.")
    data["hazard_design"] = {}
    data["hazard_design"]["hazard_rps"] = hazard_rps.tolist()

    for intensity_type in ["acc", "disp"]:
        data["hazard_design"][intensity_type] = {}
        data["hazard_design"][intensity_type][
            "stats_im_hazard"
        ] = calculate_hazard_design_intensities(data, hazard_rps, intensity_type)

    return data


def create_hcurve_dictionary(sites, vs30_list, imt_list, imtl_list, agg_list, hcurves):
    """
    compile hazard data into a dictionary

    :param sites: pd dataframe  idx: sites, cols: ['latlon', 'lat', 'lon']
    :param vs30_list: list  vs30s of interest
    :param imt_list:  list  imts of interest
    :param imtl_list: list  intensity levels
    :param agg_list:  list  agg types of interest (e.g., mean or "0.f" where f is a fractile
    :param hcurves:

    :return: dictionary   hazard curves including metadata
    """

    # create dictionary
    data = {}

    # prep metadata
    imtls = {}
    for imt in imt_list:
        imtls[imt] = imtl_list

    data["metadata"] = {}
    data["metadata"]["quantiles"] = [float(q) for q in agg_list if q != "mean"]
    data["metadata"]["acc_imtls"] = imtls
    data["metadata"]["disp_imtls"] = convert_imtls_to_disp(imtls)
    data["metadata"]["sites"] = sites
    data["metadata"]["vs30s"] = vs30_list

    # add hcurves
    data["hcurves"] = {}
    data["hcurves"]["hcurves_stats"] = hcurves

    return data


def save_hdf(hf_name, data):
    """
    Saves the data dictionary as an hdf5 file for later use.

    :param hf_name: name of the hdf5 file
    :param data: dictionary containing hazard curves and metadata for
                     vs30, sites, intensity measures, and design intensities
    """
    with h5py.File(hf_name, "w") as hf:

        # add metadata
        grp = hf.create_group("metadata")
        grp.attrs["vs30s"] = data["metadata"]["vs30s"]
        grp.attrs["quantiles"] = data["metadata"]["quantiles"]
        grp.attrs["acc_imtls"] = str(data["metadata"]["acc_imtls"])
        grp.attrs["disp_imtls"] = str(data["metadata"]["disp_imtls"])
        grp.attrs["sites"] = str(data["metadata"]["sites"].to_dict())

        # add hazard curves
        grp = hf.create_group("hcurves")
        for dset_name in ["hcurves_stats"]:
            dset = grp.create_dataset(
                dset_name, np.array(data["hcurves"][dset_name]).shape
            )
            dset[:] = np.array(data["hcurves"][dset_name])

        # add poe values
        if "hazard_design" in data.keys():
            grp = hf.create_group("hazard_design")
            grp.attrs["hazard_rps"] = data["hazard_design"]["hazard_rps"]
            for intensity_type in ["acc", "disp"]:
                subgrp = grp.create_group(intensity_type)
                for dset_name in ["stats_im_hazard"]:
                    dset = subgrp.create_dataset(
                        dset_name,
                        np.array(
                            data["hazard_design"][intensity_type][dset_name]
                        ).shape,
                    )
                    dset[:] = np.array(data["hazard_design"][intensity_type][dset_name])

    print(f"\nHazard curve data is saved in {hf_name},\n\tin {os.getcwd()}")
