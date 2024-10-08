"""
This module compiles the magnitude and distances values for the parameter table.

TODO:
    - `extract_m_values` uses/builds entire mean mag tables independent of what locations and PoEs
        are requested in function args.
    - Consolidate the mean mag csv files into one cache rather than 3 separate files. Any locations/poes
        not available can be looked up and added to the cache.
"""
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import pandas as pd
from toshi_hazard_store.model import AggregationEnum

from nzssdt_2023.data_creation.mean_magnitudes import get_mean_mag_df, read_mean_mag_df
from nzssdt_2023.data_creation.sa_parameter_generation import replace_relevant_locations

from .constants import (
    AKL_LOCATIONS,
    AKL_MEAN_MAG_P90_FILEPATH,
    GRID_LOCATIONS,
    GRID_MEAN_MAG_FILEPATH,
    POES,
    SRWG_214_MEAN_MAG_FILEPATH,
    SRWG_LOCATIONS,
)

if TYPE_CHECKING:
    import geopandas.typing as gpdt
    import pandas.typing as pdt

from nzssdt_2023.config import DISAGG_HAZARD_ID, RESOURCES_FOLDER


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

    df = pd.DataFrame(index=site_list, columns=APoEs, dtype=float)

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
    site_list: List[str],
    APoEs: List[str],
    recalculate: bool = False,
) -> Tuple["pdt.DataFrame", "pdt.DataFrame"]:
    """Extracts the magnitudes from the input .csv folder into a manageable dataframe

    Args:
        site_list: list of sites of interest
        APoEs    : list of APoEs of interest
        recalculate: if True, forces recalculation of mean mags, othwise use existing files, if available

    Returns:
         M_mean: mean magnitudes for all sites and APoEs
         M_p90 : 90th %ile magnitudes for Auckland and APoEs

    If the mean mag csv files are available in the WORKING_FOLDER they will be used unless recalulate is True.
    If they are not found, they will be calculated by get_mean_mag_df.
    """

    if not SRWG_214_MEAN_MAG_FILEPATH.exists() or recalculate:
        m_mean_named = get_mean_mag_df(
            DISAGG_HAZARD_ID, SRWG_LOCATIONS, POES, AggregationEnum.MEAN
        )
        m_mean_named.to_csv(SRWG_214_MEAN_MAG_FILEPATH)
    else:
        m_mean_named = read_mean_mag_df(SRWG_214_MEAN_MAG_FILEPATH)

    if not GRID_MEAN_MAG_FILEPATH.exists() or recalculate:
        m_mean_grid = get_mean_mag_df(
            DISAGG_HAZARD_ID, GRID_LOCATIONS, POES, AggregationEnum.MEAN
        )
        m_mean_grid.to_csv(GRID_MEAN_MAG_FILEPATH)
    else:
        m_mean_grid = read_mean_mag_df(GRID_MEAN_MAG_FILEPATH)

    m_mean = pd.concat([m_mean_named, m_mean_grid])

    if not AKL_MEAN_MAG_P90_FILEPATH.exists() or recalculate:
        m_p90_akl = get_mean_mag_df(
            DISAGG_HAZARD_ID, AKL_LOCATIONS, POES, AggregationEnum._90
        )
        m_p90_akl.to_csv(AKL_MEAN_MAG_P90_FILEPATH)
    else:
        m_p90_akl = read_mean_mag_df(AKL_MEAN_MAG_P90_FILEPATH)

    m_mean = m_mean.loc[site_list, APoEs]
    m_p90_akl = m_p90_akl.loc[["Auckland"], APoEs]

    return m_mean, m_p90_akl


def create_D_and_M_table(
    site_list: List[str], APoEs: List[str], recalculate: bool = False
):
    """Compiles the D and M parameter tables

    Args:
        site_list: list of sites of interest
        APoEs    : list of APoEs of interest
        recalculate: if True, forces recalculation of mean mags, othwise use existing files, if available

    Returns:
        D_and_M: dataframe of the d and m tables
    """

    folder = Path(RESOURCES_FOLDER, "pipeline", "v1", "input_data")
    assert os.path.isdir(folder)

    D_values = pd.read_json(Path(folder, "D_values.json"))
    D_sites = [site for site in list(D_values.index) if site in site_list]

    M_mean, M_p90 = extract_m_values(site_list, APoEs, recalculate)

    D_and_M = pd.DataFrame(index=site_list, columns=["D"] + APoEs)

    # include D values
    D_and_M.loc[D_sites, "D"] = D_values.loc[D_sites, "D"]

    # include M values
    for APoE in APoEs:
        # M value is >= the 90th %ile values for Auckland
        D_and_M.loc[site_list, APoE] = np.maximum(
            M_mean.loc[site_list, APoE], M_p90.loc["Auckland", APoE]
        )

    D_and_M = replace_relevant_locations(D_and_M)
    return D_and_M
