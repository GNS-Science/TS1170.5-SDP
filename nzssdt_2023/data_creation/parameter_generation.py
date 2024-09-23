"""
This module derives the PGA, Sa,s, and Tc parameters from the NSHM hazard curves.
"""
import ast
import os
from typing import TYPE_CHECKING, List, Tuple

import h5py
import numpy as np
import pandas as pd

from nzssdt_2023.data_creation import NSHM_to_hdf5 as to_hdf5
from nzssdt_2023.data_creation import query_NSHM as q_haz
from nzssdt_2023.data_creation.extract_data import (
    extract_APoEs,
    extract_quantiles,
    extract_sites,
    extract_spectra,
    extract_vs30s,
)
from nzssdt_2023.data_creation.NSHM_to_hdf5 import acc_to_vel, g, period_from_imt
from nzssdt_2023.data_creation.query_NSHM import agg_list, imt_list, vs30_list

if TYPE_CHECKING:
    import numpy.typing as npt
    import pandas.typing as pdt

sc_dict = {
    "I": {
        "representative_vs30": 750,
        "label": "Site Soil Class I",
        "lower_bound": 750,
        "upper_bound": np.nan,
    },
    "II": {
        "representative_vs30": 525,
        "label": "Site Soil Class II",
        "lower_bound": 450,
        "upper_bound": 750,
    },
    "III": {
        "representative_vs30": 375,
        "label": "Site Soil Class III",
        "lower_bound": 300,
        "upper_bound": 450,
    },
    "IV": {
        "representative_vs30": 275,
        "label": "Site Soil Class IV",
        "lower_bound": 250,
        "upper_bound": 300,
    },
    "V": {
        "representative_vs30": 225,
        "label": "Site Soil Class V",
        "lower_bound": 200,
        "upper_bound": 250,
    },
    "VI": {
        "representative_vs30": 175,
        "label": "Site Soil Class VI",
        "lower_bound": 150,
        "upper_bound": 200,
    },
}

lower_bound_parameters = {"controlling_site": "Auckland", "controlling_percentile": 0.9}

location_replacements = {
    "Auckland": ["Manukau City"],
    "Tauranga": ["Mount Maunganui"],
    "Wellington": ["Wellington CBD"],
    "Lower Hutt": ["Wainuiomata", "Eastbourne"],
}


def acc_spectra_to_vel(acc_spectra: "npt.NDArray", imtls: dict) -> "npt.NDArray":
    """Convert uniform hazard spectra from acceleration to velocity

    Args:
        acc_spectra: acceleration spectra
        imtls: keys: intensity measures e.g., SA(1.0), values: list of intensity levels

    Returns:
        vel_spectra: velocity spectra

    """
    vel_spectra = np.zeros_like(acc_spectra)
    period_list = [period_from_imt(imt) for imt in list(imtls.keys())]

    for i_p, period in enumerate(period_list):
        vel_spectra[:, :, i_p, :, :] = acc_to_vel(acc_spectra[:, :, i_p, :, :], period)

    return vel_spectra


def calculate_parameter_arrays(
    data_file: str,
) -> Tuple["npt.NDArray", "npt.NDArray", "npt.NDArray", "npt.NDArray"]:
    """Calculate PGA, Sa,s, and Tc values for uniform hazard spectra in hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        PGA: peak ground acceleration
        Sas: short-period spectral acceleration (90% of maximum spectral acceleration)
        PSV: 95% of maximum spectral velocity
        Tc : spectral-acceleration-plateau corner period

    """
    with h5py.File(data_file, "r") as hf:
        imtls = ast.literal_eval(hf["metadata"].attrs["acc_imtls"])
        imt_list = list(imtls.keys())

    acc_spectra, imtls = extract_spectra(data_file)
    vel_spectra = acc_spectra_to_vel(acc_spectra, imtls)

    Sas = 0.9 * np.max(acc_spectra, axis=2)
    PSV = 0.95 * np.max(vel_spectra, axis=2)

    Tc = 2 * np.pi * PSV / (Sas * g)
    PGA = acc_spectra[:, :, imt_list.index("PGA"), :, :]

    return PGA, Sas, PSV, Tc


def create_mean_sa_table(data_file: str) -> "pdt.DataFrame":
    """create preliminary table of spectral parameters, considering mean hazard spectra

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes

    """
    PGA, Sas, PSV, Tc = calculate_parameter_arrays(data_file)
    vs30_list = extract_vs30s(data_file)
    i_stat = 0  # hcurves index for stats in ['mean'] + quantiles

    site_list = list(extract_sites(data_file).index)
    index = site_list

    APoEs, hazard_rp_list = extract_APoEs(data_file)
    site_class_list = [f'{sc_dict[sc]["label"]}' for sc in sc_dict]
    parameters = ["PGA", "Sas", "PSV", "Tc"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])

    df = pd.DataFrame(index=index, columns=columns).astype(float)

    for sc in sc_dict.keys():
        sc_label = sc_dict[sc]["label"]
        vs30 = sc_dict[sc]["representative_vs30"]
        i_vs30 = vs30_list.index(vs30)

        for APoE in APoEs:
            i_rp = hazard_rp_list.index(int(APoE.split("/")[1]))

            df.loc[:, (APoE, sc_label, "PGA")] = PGA[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Sas")] = Sas[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "PSV")] = PSV[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Tc")] = Tc[i_vs30, :, i_rp, i_stat]

    return df


def update_lower_bound_sa(mean_df: "pdt.DataFrame", data_file: str) -> "pdt.DataFrame":
    """amend the table of mean spectral parameters to include the lower bound hazard

    Args:
        mean_df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes
        data_file: name of hazard hdf5 file

    Returns:
        df: mutli-index dataframe updated for the lower bound hazard

    """
    PGA, Sas, PSV, Tc = calculate_parameter_arrays(data_file)
    site_list = list(extract_sites(data_file).index)
    vs30_list = extract_vs30s(data_file)
    quantiles = extract_quantiles(data_file)

    APoEs, hazard_rp_list = extract_APoEs(data_file)
    site_class_list = [f'{sc_dict[sc]["label"]}' for sc in sc_dict]
    parameters = ["PGA Floor", "Sas Floor", "PSV Floor"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])
    index = site_list
    df = pd.concat([mean_df, pd.DataFrame(index=index, columns=columns)], axis=1)

    controlling_site = lower_bound_parameters["controlling_site"]
    i_site = site_list.index(controlling_site)
    i_stat = 1 + quantiles.index(lower_bound_parameters["controlling_percentile"])

    for sc in sc_dict.keys():
        sc_label = sc_dict[sc]["label"]
        vs30 = sc_dict[sc]["representative_vs30"]
        i_vs30 = vs30_list.index(vs30)

        for APoE in APoEs:
            i_rp = hazard_rp_list.index(int(APoE.split("/")[1]))

            # update the controlling site to use the qth %ile
            df.loc[controlling_site, (APoE, sc_label, "PGA")] = PGA[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "Sas")] = Sas[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "PSV")] = PSV[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "Tc")] = Tc[
                i_vs30, i_site, i_rp, i_stat
            ]

            # apply lower bound to all sites
            df.loc[:, (APoE, sc_label, "PGA")] = np.maximum(
                df.loc[:, (APoE, sc_label, "PGA")],
                df.loc[controlling_site, (APoE, sc_label, "PGA")],
            )
            df.loc[:, (APoE, sc_label, "Sas")] = np.maximum(
                df.loc[:, (APoE, sc_label, "Sas")],
                df.loc[controlling_site, (APoE, sc_label, "Sas")],
            )
            df.loc[:, (APoE, sc_label, "PSV")] = np.maximum(
                df.loc[:, (APoE, sc_label, "PSV")],
                df.loc[controlling_site, (APoE, sc_label, "PSV")],
            )

            # record locations that were controlled by the lower bound
            df.loc[:, (APoE, sc_label, "PGA Floor")] = ~(
                df.loc[:, (APoE, sc_label, "PGA")]
                > df.loc[controlling_site, (APoE, sc_label, "PGA")]
            )
            df.loc[:, (APoE, sc_label, "Sas Floor")] = ~(
                df.loc[:, (APoE, sc_label, "Sas")]
                > df.loc[controlling_site, (APoE, sc_label, "Sas")]
            )
            df.loc[:, (APoE, sc_label, "PSV Floor")] = ~(
                df.loc[:, (APoE, sc_label, "PSV")]
                > df.loc[controlling_site, (APoE, sc_label, "PSV")]
            )

            # set new Tc values
            df.loc[:, (APoE, sc_label, "Tc")] = (
                2
                * np.pi
                * df.loc[:, (APoE, sc_label, "PSV")]
                / (df.loc[:, (APoE, sc_label, "Sas")] * g)
            )

    return df


def round_sa_parameters(df: "pdt.DataFrame") -> "pdt.DataFrame":
    """set the correct number of decimal places for the spectral parameters

    Args:
        df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes

    Returns:
        df: mutli-index dataframe updated for the correct number of decimal places


    """
    # round sa parameters for final table
    for parameter in ["PGA", "Sas", "Tc"]:
        if parameter == "Tc":
            digits = 1
        else:
            digits = 2
        df.loc[:, (slice(None), slice(None), parameter)] = df.loc[
            :, (slice(None), slice(None), parameter)
        ].round(digits)

    # calculate the inferred PSV
    digits = 2
    APoEs = list(df.columns.levels[0])
    sc_labels = list(df.columns.levels[1])
    for sc_label in sc_labels:
        for APoE in APoEs:
            df.loc[:, (APoE, sc_label, "PSV")] = (
                df.loc[:, (APoE, sc_label, "Sas")]
                * g
                * df.loc[:, (APoE, sc_label, "Tc")]
                / (2 * np.pi)
            )
            df.loc[:, (APoE, sc_label, "PSV")] = df.loc[
                :, (APoE, sc_label, "PSV")
            ].round(digits)

    return df


def remove_irrelevant_location_replacements(site_list: List[str]):
    """

    Args:
        site_list: list of sites included in the sa tables

    Returns:
        location_replacements: updated dictionary of replaments

    """

    key_list = list(location_replacements.keys())
    for key in key_list:
        replace_list = location_replacements[key]
        location_replacements[key] = [
            site for site in replace_list if site in site_list
        ]

        if key not in site_list:
            del location_replacements[key]

    return location_replacements


def replace_relevant_locations(
    df: "pdt.DataFrame", print_locations: bool = False
) -> "pdt.DataFrame":
    """replace parameters for locations that are tied to other locations

    Args:
        df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes
        print_locations: if True, print relevant locations before and after replacements

    Returns:
        df: mutli-index dataframe with replaced locations

    """
    site_list = list(df.index)
    location_replacements = remove_irrelevant_location_replacements(site_list)

    if print_locations:
        check_replaced_locations = []
        for location in location_replacements:
            check_replaced_locations.append(location)
            for replaced_location in location_replacements[location]:
                check_replaced_locations.append(replaced_location)
        print(df.loc[check_replaced_locations, :])

    for location in location_replacements:
        for replaced_location in location_replacements[location]:
            df.loc[replaced_location, :] = df.loc[location, :]

    if print_locations:
        print(df.loc[check_replaced_locations, :])

    return df


def save_table_to_pkl(
    df: "pdt.DataFrame", sa_name: str, save_floor_flags: bool = False
):
    """Save the sa parameter table dataframe to a pickle file

    Args:
        df: mutli-index dataframe of sa parameters for all locations, APoEs, and site classes
        sa_name: .pkl filename
        save_floor_flags: True saves a .pkl that includes metadata on the lower bound hazard

    """
    df = df.copy(deep=True)

    if save_floor_flags:
        filename = sa_name + "_with-floor-flags.pkl"
        df.to_pickle(filename)

    APoEs = list(df.columns.levels[0])
    sc_labels = list(df.columns.levels[1])

    for APoE in APoEs:
        for sc in sc_labels:
            for parameter in ["PGA Floor", "PSV", "PSV Floor", "Sas Floor"]:
                df.drop((APoE, sc, parameter), axis=1, inplace=True)

    filename = sa_name + ".pkl"
    df.to_pickle(filename)

    print(f"Sa parameter .pkl file(s) saved in \n\t{os.getcwd()}")


def create_sa_pkl(hf_name: str, sa_name: str, hazard_param: dict = None):
    """Generate sa parameter tables and save as .pkl file

    Args:
        hf_name: name of intermediate hdf5 file with hazard curve data
        sa_name: name of .pkl file
        hazard_param: optional dictionary containing NSHM version and list of locations

    """

    if hazard_param is not None:
        hazard_id = hazard_param["hazard_id"]
        site_list = hazard_param["site_list"]
        sites = q_haz.create_sites_df(site_list=site_list)

    # query NSHM
    hcurves, imtl_list = q_haz.retrieve_hazard_curves(
        sites, vs30_list, imt_list, agg_list, hazard_id
    )

    # prep and save hcurves to hdf5
    data = to_hdf5.create_hcurve_dictionary(
        sites, vs30_list, imt_list, imtl_list, agg_list, hcurves
    )

    data = to_hdf5.add_uniform_hazard_spectra(data)
    to_hdf5.save_hdf(hf_name, data)

    # create sa table
    df = create_mean_sa_table(hf_name)
    df = update_lower_bound_sa(df, hf_name)
    df = round_sa_parameters(df)
    df = replace_relevant_locations(df)
    save_table_to_pkl(df, sa_name)
