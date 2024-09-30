"""
This module derives the PGA, Sa,s, and Tc parameters from the NSHM hazard curves.
"""
import ast
import logging
import pathlib
from typing import TYPE_CHECKING, List, NamedTuple, Optional, Tuple

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

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy.typing as npt
    import pandas.typing as pdt


class SiteClass(NamedTuple):
    site_class: str
    representative_vs30: int
    label: str
    lower_bound: float
    upper_bound: float


SITE_CLASSES: dict[str, SiteClass] = {
    "I": SiteClass("I", 750, "Site Soil Class I", 750, np.nan),
    "II": SiteClass("II", 525, "Site Soil Class II", 450, 750),
    "III": SiteClass("III", 375, "Site Soil Class III", 300, 450),
    "IV": SiteClass("IV", 275, "Site Soil Class IV", 250, 300),
    "V": SiteClass("V", 225, "Site Soil Class V", 200, 250),
    "VI": SiteClass("VI", 175, "Site Soil Class VI", 150, 200),
}

lower_bound_parameters: dict[str, str | float] = {
    "controlling_site": "Auckland",
    "controlling_percentile": 0.9,
}


class LocationReplacement(NamedTuple):
    preferred_location: str
    replaced_locations: list[str]


LOCATION_REPLACEMENTS: dict[str, LocationReplacement] = {
    "Auckland": LocationReplacement("Auckland", ["Manukau City"]),
    "Tauranga": LocationReplacement("Tauranga", ["Mount Maunganui"]),
    "Wellington": LocationReplacement("Wellington", ["Wellington CBD"]),
    "Lower Hutt": LocationReplacement("Lower Hutt", ["Wainuiomata", "Eastbourne"]),
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
    data_file: str | pathlib.Path,
) -> Tuple["npt.NDArray", "npt.NDArray", "npt.NDArray", "npt.NDArray"]:
    """Calculate PGA, Sa,s, and Tc values for uniform hazard spectra in hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        PGA: peak ground acceleration
        Sas: short-period spectral acceleration (90% of maximum spectral acceleration)
        PSV: 95% of maximum spectral velocity
        Tc : spectral-acceleration-plateau corner period

    Todo:
        * add Td calculation (needs equation, how to do lower-bound adjustment)

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


def create_mean_sa_table(data_file: pathlib.Path) -> "pdt.DataFrame":
    """create preliminary table of spectral parameters, considering mean hazard spectra

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes

    Todo:
        * add Td

    """
    PGA, Sas, PSV, Tc = calculate_parameter_arrays(data_file)
    vs30_list = extract_vs30s(data_file)
    i_stat = 0  # hcurves index for stats in ['mean'] + quantiles

    site_list = list(extract_sites(data_file).index)
    index = site_list

    APoEs, hazard_rp_list = extract_APoEs(data_file)
    site_class_list = [f"{SITE_CLASSES[sc].label}" for sc in SITE_CLASSES]
    parameters = ["PGA", "Sas", "PSV", "Tc"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])

    df = pd.DataFrame(index=index, columns=columns).astype(float)

    log.info("create_mean_sa_table() processesing site classes")
    for sc in SITE_CLASSES.keys():
        sc_label = SITE_CLASSES[sc].label
        vs30 = int(SITE_CLASSES[sc].representative_vs30)

        log.info(f"site class {sc} label: {sc_label} vs30: {vs30}")

        i_vs30 = vs30_list.index(vs30)

        for APoE in APoEs:
            i_rp = hazard_rp_list.index(int(APoE.split("/")[1]))

            df.loc[:, (APoE, sc_label, "PGA")] = PGA[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Sas")] = Sas[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "PSV")] = PSV[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Tc")] = Tc[i_vs30, :, i_rp, i_stat]

    return df


def update_lower_bound_sa(
    mean_df: "pdt.DataFrame", data_file: str | pathlib.Path
) -> "pdt.DataFrame":
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
    site_class_list = [f"{SITE_CLASSES[sc].label}" for sc in SITE_CLASSES]
    parameters = ["PGA Floor", "Sas Floor", "PSV Floor"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])
    index = site_list
    df = pd.concat([mean_df, pd.DataFrame(index=index, columns=columns)], axis=1)

    controlling_site = lower_bound_parameters["controlling_site"]
    i_site = site_list.index(controlling_site)
    i_stat = 1 + quantiles.index(
        float(lower_bound_parameters["controlling_percentile"])
    )

    for sc in SITE_CLASSES.keys():
        sc_label = SITE_CLASSES[sc].label
        vs30 = SITE_CLASSES[sc].representative_vs30
        i_vs30 = vs30_list.index(int(vs30))

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

    Todo:
        * round Sas before calculating Tc
        * round to n significant digits instead of n decimal places

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


def remove_irrelevant_location_replacements(
    site_list: List[str], location_replacements: dict[str, LocationReplacement]
) -> dict[str, LocationReplacement]:
    """

    Args:
        site_list: list of sites included in the sa tables
        location_replacements: list of the location replacements

    Returns:
        location_replacements: a new dictionary of replacements

    """
    new_location_replacements = {}

    for key in location_replacements.keys():
        if key in site_list:
            replace_list = location_replacements[key].replaced_locations
            new_location_replacements[key] = LocationReplacement(
                key, [site for site in replace_list if site in site_list]
            )

    return new_location_replacements


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
    location_replacements = remove_irrelevant_location_replacements(
        site_list, LOCATION_REPLACEMENTS
    )

    if print_locations:
        check_replaced_locations = []
        for location in location_replacements:
            check_replaced_locations.append(location)
            for replaced_location in location_replacements[location].replaced_locations:
                check_replaced_locations.append(replaced_location)
        print("\n\noriginal values for replaced locations:")
        print(df.loc[check_replaced_locations, :])

    for location in location_replacements:
        for replaced_location in location_replacements[location].replaced_locations:
            df.loc[replaced_location, :] = df.loc[location, :]

    if print_locations:
        print("\n\nnew values for replaced locations:")
        print(df.loc[check_replaced_locations, :])

    return df


def save_table_to_pkl(
    df: "pdt.DataFrame", sa_name: pathlib.Path, save_floor_flags: bool = False
):
    """Save the sa parameter table dataframe to a pickle file

    Args:
        df: mutli-index dataframe of sa parameters for all locations, APoEs, and site classes
        sa_name: .pkl filename
        save_floor_flags: True saves a .pkl that includes metadata on the lower bound hazard

    TODO:
     - to json direct rather than to_pickle (or gherkin)
    """
    df = df.copy(deep=True)

    # TODO: maybe this should be a separate function?
    if save_floor_flags:
        floor_filename = str(sa_name).replace(".pkl", "_with-floor-flags.pkl")
        df.to_pickle(floor_filename)

    APoEs = list(df.columns.levels[0])
    sc_labels = list(df.columns.levels[1])

    for APoE in APoEs:
        for sc in sc_labels:
            for parameter in ["PGA Floor", "PSV", "PSV Floor", "Sas Floor"]:
                df.drop((APoE, sc, parameter), axis=1, inplace=True)

    # filename = sa_name + ".pkl"
    df.to_pickle(sa_name)

    # print(f"Sa parameter .pkl file(s) saved in \n\t{os.getcwd()}")


def create_sa_pkl(
    hf_name: pathlib.Path,
    sa_name: pathlib.Path,
    hazard_id: Optional[str] = None,
    site_list: Optional[list[str]] = None,
    save_floor_flags: bool = False,
):
    """Generate sa parameter tables and save as .pkl file

    Args:
        hf_name: name of intermediate hdf5 file with hazard curve data
        sa_name: name of .pkl file
        hazard_id: NSHM model id
        site_list: list of sites to include in the sa parameter table
        save_floor_flags: True saves a .pkl that includes metadata on the lower bound hazard

    Todo:
        * add option to pass alternate return periods to to_hdf5.add_uniform_hazard_spectra

    """
    hazard_id = hazard_id or q_haz.hazard_id

    if site_list is None:
        sites = pd.concat(
            [q_haz.create_sites_df(), q_haz.create_sites_df(named_sites=False)]
        )
    else:
        sites = q_haz.create_sites_df(site_list=site_list)

    log.info(f"begin create_sa_pkl for {len(sites)}")

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
    save_table_to_pkl(df, sa_name, save_floor_flags)
