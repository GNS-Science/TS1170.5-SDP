"""
This module extracts the data and metadata in the hdf5 containing the NSHM data.
"""
import ast
import pathlib
from typing import TYPE_CHECKING, List, Tuple

import h5py
import pandas as pd

if TYPE_CHECKING:
    import numpy.typing as npt
    import pandas.typing as pdt


def extract_spectra(data_file: str | pathlib.Path) -> Tuple["npt.NDArray", dict]:
    """Extract the uniform hazard spectra from the hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        acc_spectra: acceleration spectra
        imtls: keys: intensity measures e.g., SA(1.0), values: list of intensity levels

    """
    with h5py.File(data_file, "r") as hf:
        imtls = ast.literal_eval(hf["metadata"].attrs["acc_imtls"])
        acc_spectra = hf["hazard_design"]["acc"]["stats_im_hazard"][:]

    return acc_spectra, imtls


def extract_vs30s(data_file: str | pathlib.Path) -> List[int]:
    """Extract the vs30 values from the hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        vs30_list: list of vs30s included in hdf5

    """
    with h5py.File(data_file, "r") as hf:
        vs30_list = list(hf["metadata"].attrs["vs30s"])

    return vs30_list


def extract_quantiles(data_file: str | pathlib.Path) -> List[float]:
    """Extract hazard quantiles from the hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        quantiles: list of quantiles

    """
    with h5py.File(data_file, "r") as hf:
        quantiles = list(hf["metadata"].attrs["quantiles"])

    return quantiles


def extract_sites(data_file: str | pathlib.Path) -> "pdt.DataFrame":
    """Extract sites from the hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        sites: dataframe of sites with lat/lons

    """
    with h5py.File(data_file, "r") as hf:
        sites = pd.DataFrame(ast.literal_eval(hf["metadata"].attrs["sites"]))

    return sites


def extract_APoEs(data_file: str | pathlib.Path) -> Tuple[List[str], List[int]]:
    """Extract uniform hazard spectra annual probabilities of exceedance from the hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        APoEs: list of APoE strings
        hazard_rp_list: list of return periods

    """
    with h5py.File(data_file, "r") as hf:
        hazard_rp_list = list(hf["hazard_design"].attrs["hazard_rps"])
    APoEs = [f"APoE: 1/{hazard_rp}" for hazard_rp in hazard_rp_list]

    return APoEs, hazard_rp_list
