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

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATION_LISTS
from nzshm_common.grids import load_grid
from toshi_hazard_store.model import ProbabilityEnum, AggregationEnum


from nzssdt_2023.data_creation.sa_parameter_generation import replace_relevant_locations
from nzssdt_2023.mean_magnitudes import get_mean_mag_df, lat_lon_from_id

if TYPE_CHECKING:
    import geopandas.typing as gpdt
    import pandas.typing as pdt

from nzssdt_2023.config import RESOURCES_FOLDER, DISAGG_HAZARD_ID, LOCATION_LIST, LOCATION_GRID, AKL_LOCATION_ID


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
    site_list: List[str],
    APoEs: List[str],
    recalculate: bool=False,
) -> Tuple["pdt.DataFrame", "pdt.DataFrame"]:
    """Extracts the magnitudes from the input .csv folder into a manageable dataframe

    Args:
        site_list: list of sites of interest
        APoEs    : list of APoEs of interest
        recalculate: if True, forces recalculation of mean mags, othwise use existing files, if available

    Returns:
         M_mean: mean magnitudes for all sites and APoEs
         M_p90 : 90th %ile magnitudes for Auckland and APoEs
        
    If the mean mag csv files are available in RESOURCES_FOLDER/pipeline/v1/input_data they will be used unless
    recalulate is True. If they are not found, they will be calculated by get_mean_mag_df
    """

    srwg_locations = [CodedLocation(*lat_lon_from_id(_id), 0.001) for _id in LOCATION_LISTS[LOCATION_LIST]["locations"]]
    grid_locations = [CodedLocation(*loc, 0.001) for loc in load_grid(LOCATION_GRID)]
    akl_locations = [CodedLocation(*lat_lon_from_id(AKL_LOCATION_ID), 0.001)]
    poes = [
        ProbabilityEnum._2_PCT_IN_50YRS,
        ProbabilityEnum._5_PCT_IN_50YRS,
        ProbabilityEnum._10_PCT_IN_50YRS,
        ProbabilityEnum._18_PCT_IN_50YRS,
        ProbabilityEnum._39_PCT_IN_50YRS,
        ProbabilityEnum._63_PCT_IN_50YRS,
        ProbabilityEnum._86_PCT_IN_50YRS,
    ]

    folder = Path(RESOURCES_FOLDER, "pipeline/v1/input_data")
    assert os.path.isdir(folder)

    srwg_214_filepath = Path(folder, "SRWG214_mean_mag.csv")
    grid_filepath = Path(folder, "grid_mean_mag.csv")
    akl_filepath = Path(folder, "AKL_90pct_mean_mag.csv")
    if not(srwg_214_filepath.exists() or recalculate):
        m_mean_named = pd.read_csv(srwg_214_filepath)
    else:
        m_mean_named = get_mean_mag_df(DISAGG_HAZARD_ID, srwg_locations, poes, AggregationEnum.MEAN)
        m_mean_named.to_csv(srwg_214_filepath)

    if not(grid_filepath.exists() or recalculate):
        m_mean_grid = pd.read_csv(grid_filepath)
    else:
        m_mean_grid = get_mean_mag_df(DISAGG_HAZARD_ID, grid_locations, poes, AggregationEnum.MEAN)
        m_mean_grid.to_csv(grid_filepath)

    m_mean = pd.concat([m_mean_named, m_mean_grid])

    if not(akl_filepath.exists() or recalculate):
        m_p90_akl = pd.read_csv(akl_filepath)
    else:
        m_p90_akl = get_mean_mag_df(DISAGG_HAZARD_ID, akl_locations, poes, AggregationEnum._90)
        m_p90_akl.to_csv(akl_filepath)

    return m_mean, m_p90_akl


def create_D_and_M_table(site_list: List[str], APoEs: List[str], recalculate: bool=False):
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
