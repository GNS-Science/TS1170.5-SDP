"""
helper functions for producing an HDF5 file for the NZSSDT tables
"""
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import pandas as pd

from nzssdt_2023.data_creation import query_NSHM as q_haz
from nzssdt_2023.data_creation.constants import (
    AGG_LIST,
    DEFAULT_RPS,
    IMT_LIST,
    IMTL_LIST,
    VS30_LIST,
)

if TYPE_CHECKING:
    import numpy.typing as npt

import h5py
import numpy as np

g = 9.80665  # gravity in m/s^2


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

    return (acc * g) * (t / (2 * np.pi)) ** 2


def acc_to_vel(acc, t):
    """

    :param acc: float   intensity in acceleration [g]
    :param t: float     time in seconds

    :return: float      intensity in velocity [m/s]
    """

    return (acc * g) * (t / (2 * np.pi))


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


def calculate_hazard_design_intensities(
    data: Dict[str, Any],
    hazard_rps: Union[List[int], "npt.NDArray"],
    intensity_type="acc",
):
    """
    calculate design intensities based on an annual probability of exceedance (APoE)

    :param data: dictionary containing hazard curves and metadata for vs30, sites, intensity measures
    :param hazard_rps: list containing the desired return periods (1 / APoE)

    :return: np arrays for all intensities from the hazard curve realizations and stats (mean and quantiles)
    """

    hazard_rps = np.array(hazard_rps)
    imtls = data["metadata"][f"{intensity_type}_imtls"]
    hcurves_stats = np.array(data["hcurves"]["hcurves_stats"])

    [n_vs30, n_sites, n_imts, _, n_stats] = hcurves_stats.shape

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
    data: Dict[str, Any],
    hazard_rps: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Adds uniform hazard spectra to the data dictionary, based on the input hazard_rps

    Args:
        data: dictionary containing hazard curves and metadata for vs30, sites, intensity measures
        hazard_rps: list of return periods of interest (inverse of annual probability of exceedance, apoe)

    Returns:
        updated dictionary includes design intensities

    If hazard_rps is None (default) or empty, the default return periods, `constants.DEFAULT_RPS`, will be used.
    """

    hazard_rps = hazard_rps or DEFAULT_RPS

    imtls = data["metadata"]["acc_imtls"]
    data["metadata"]["disp_imtls"] = convert_imtls_to_disp(imtls)

    # get poe values
    print("Calculating APoE intensities.")
    data["hazard_design"] = {}
    data["hazard_design"]["hazard_rps"] = hazard_rps

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

    print(f"\nHazard curve data is saved as {hf_name}")


def query_NSHM_to_hdf5(
    hf_name: Path,
    hazard_id: str = "NSHM_v1.0.4",
    site_list: Optional[list[str]] = None,
    site_limit: int = 0,
):
    """Query the NSHM and save the results to an hdf5

    Args:
        hf_name: name of hdf5 file with hazard curve data
        hazard_id: NSHM model id
        site_list: list of sites to include in the sa parameter table
        site_limit: for building test fixtures

    Todo:
        - Chris BC, the default hazard_id should actually be part of your version control

    """

    sites = pd.concat(
        [
            q_haz.create_sites_df(
                named_sites=True, site_list=site_list, site_limit=site_limit
            ),
            q_haz.create_sites_df(
                named_sites=False, site_list=site_list, site_limit=site_limit
            ),
        ]
    )

    # query NSHM
    hcurves, _ = q_haz.retrieve_hazard_curves(
        sites, VS30_LIST, IMT_LIST, AGG_LIST, hazard_id
    )

    # prep hcurves dictionary
    data = create_hcurve_dictionary(
        sites, VS30_LIST, IMT_LIST, IMTL_LIST, AGG_LIST, hcurves
    )

    # add uhs spectra
    data = add_uniform_hazard_spectra(data)

    # save file
    save_hdf(hf_name, data)
