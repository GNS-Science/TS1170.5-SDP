"""
This module compiles the magnitude and distances values for the parameter table.

TODO:
 - optimise data structure to improve on mean-mag csv files
"""
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import pandas as pd

from nzssdt_2023.data_creation.sa_parameter_generation import replace_relevant_locations

if TYPE_CHECKING:
    import geopandas.typing as gpdt
    import pandas.typing as pdt

MODULE_FOLDER = Path(os.path.realpath(__file__)).parent


def calc_distance_to_faults(
    gdf: "gpdt.DataFrame", faults: "gpdt.DataFrame"
) -> "pdt.DataFrame":
    """Calculates the closest distance of polygons or points to a set of fault lines

    Args:
        gdf: geodataframe of locations (polygons or points)
        faults: geodataframe of fault lines

    Returns:
        df: dataframe of distance from each location to the closest fault
    """
    meter_epsg = 2193
    faults.to_crs(epsg=meter_epsg)
    gdf = gdf.to_crs(epsg=meter_epsg)

    gdf["distance"] = round(
        gdf.geometry.apply(lambda x: faults.distance(x).min()) / 1000.0
    )

    gdf["D"] = gdf["distance"].astype("int")
    gdf.loc[gdf["D"] >= 20, "D"] = ""

    wgs_epsg = 4326
    gdf = gdf.to_crs(epsg=wgs_epsg)

    gdf.index.names = [""]

    return gdf[["D"]]


def return_table_indices(df: "pdt.DataFrame") -> Tuple[List[str], List[str], List[str]]:
    """Returns the row and column indices of the parameter df

    Args:
        df: sa parameter table

    Returns:
        site_list: list of sites included in the sa tables
        APoEs    : list of APoEs included in the sa tables
        site_class_list: list of site classes included in the sa tables

    """
    site_list = list(df.index)

    columns = list(df.columns.levels)
    APoEs = list(columns[0])
    site_class_list = list(columns[1])

    return site_list, APoEs, site_class_list


def raw_mag_to_df(raw_df: "pdt.DataFrame", site_list: List[str], APoEs: List[str]):
    """compile magnitudes dataframe into a more manageable dataframe

    Args:
        raw_df: dataframe from the initial NSHM query of magnitudes
        site_list: list of sites included in the sa tables
        APoEs    : list of APoEs included in the sa tables

    Returns:
        df: dataframe with rows: sites and columns: APoEs


    TODO:
     - reorg CDC mean_mag to get this final df shape.

    """
    poe_duration = 50

    rps = [int(APoE.split("/")[1]) for APoE in APoEs]

    df = pd.DataFrame(index=site_list, columns=APoEs)

    for site in site_list:
        for rp in rps:
            apoe = 1 / rp
            poe_50 = np.round((100 * (1 - np.exp(-apoe * poe_duration))), 0).astype(
                "int"
            )

            APoE = f"APoE: 1/{rp}"
            site_idx = raw_df["site name"] == site
            poe_idx = raw_df["poe (% in 50 years)"] == poe_50
            df.loc[site, APoE] = (
                raw_df[site_idx & poe_idx]["mean magnitude"].values[0].round(1)
            )

    return df


def extract_m_values(
    site_list: List[str], APoEs: List[str]
) -> Tuple["pdt.DataFrame", "pdt.DataFrame"]:
    """Extracts the magnitudes from the input .csv folder into a manageable dataframe

    Args:
        site_list: list of sites of interest
        APoEs    : list of APoEs of interest

    Returns:
         M_mean: mean magnitudes for all sites and APoEs
         M_p90 : 90th %ile magnitudes for Auckland and APoEs
    """

    folder = Path(MODULE_FOLDER, "input_data")
    assert os.path.isdir(folder)

    raw_mean_named = pd.read_csv(Path(folder, "SRWG214_mean_mag.csv"))
    raw_mean_grid = pd.read_csv(Path(folder, "grid_mean_mag.csv"))
    raw_mean = pd.concat([raw_mean_named, raw_mean_grid])
    M_mean = raw_mag_to_df(raw_mean, site_list, APoEs)

    raw_p90 = pd.read_csv(Path(folder, "AKL_90pct_mean_mag.csv"))
    M_p90 = raw_mag_to_df(raw_p90, ["Auckland"], APoEs)

    return M_mean, M_p90


def compile_D_and_M_values(site_list: List[str], APoEs: List[str]) -> "pdt.DataFrame":
    """Compiles the D and M parameter tables

    Args:
        site_list: list of sites of interest
        APoEs    : list of APoEs of interest

    Returns:
        D_and_M: dataframe of the d and m tables
    """

    folder = Path(MODULE_FOLDER, "input_data")
    assert os.path.isdir(folder)

    D_values = pd.read_json(Path(folder, "D_values.json"))
    D_sites = [site for site in list(D_values.index) if site in site_list]

    M_mean, M_p90 = extract_m_values(site_list, APoEs)

    D_and_M = pd.DataFrame(index=site_list, columns=["D"] + APoEs)

    # include D values
    D_and_M.loc[D_sites, "D"] = D_values.loc[D_sites, "D"]

    # include M values
    for APoE in APoEs:
        # M value is >= the 90th %ile values for Auckland
        D_and_M.loc[site_list, APoE] = np.maximum(
            M_mean.loc[site_list, APoE], M_p90.loc["Auckland", APoE]
        )

    return D_and_M


def create_D_and_M_table(site_list: List[str], APoEs: List[str], filename: str):
    """Create and save the D and M parameter table

    Args:
        site_list:
        APoEs:
        filename:

    """

    D_and_M = compile_D_and_M_values(site_list, APoEs)

    D_and_M = replace_relevant_locations(D_and_M)

    filename = filename + ".csv"
    D_and_M.to_csv(filename)

    print(f"{filename} saved to \n\t{os.getcwd()}")
