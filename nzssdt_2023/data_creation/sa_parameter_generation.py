"""
This module derives the PGA, Sa,s, Tc, and Td parameters from the NSHM hazard curves.
"""
import h5py
import ast
import numpy as np
import pandas as pd

from nzssdt_2023.data_creation.NSHM_to_hdf5 import period_from_imt, acc_to_vel, g

from nzssdt_2023.data_creation.extract_hdf5 import extract_spectra, extract_vs30s, extract_sites, extract_APoEs

from typing import TYPE_CHECKING
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
) -> ("npt.NDArray", "npt.NDArray", "npt.NDArray", "npt.NDArray"):
    """Calculate PGA, Sa,s, Tc, and Td values for uniform hazard spectra in hdf5

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

    df = pd.DataFrame(index=index, columns=columns)

    for sc in sc_dict.keys():
        vs30 = sc_dict[sc]["representative_vs30"]
        i_vs30 = vs30_list.index(vs30)
        sc_label = sc_dict[sc]["label"]
        for APoE in APoEs:
            i_rp = hazard_rp_list.index(int(APoE.split("/")[1]))

            df.loc[:, (APoE, sc_label, "PGA")] = PGA[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Sas")] = Sas[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "PSV")] = PSV[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Tc")] = Tc[i_vs30, :, i_rp, i_stat]

    return df
