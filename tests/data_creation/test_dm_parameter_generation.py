from pathlib import Path

import pandas as pd
import pandas.testing
from toshi_hazard_store.model import AggregationEnum

import nzssdt_2023.data_creation.dm_parameter_generation as dm_parameter_generation
from nzssdt_2023.data_creation.gis_data import build_d_value_dataframe
from nzssdt_2023.data_creation.constants import LOCATION_REPLACEMENTS

SITE_NAMES = ["Paihia", "Opua", "-46.200~166.600"]
FREQUENCIES = [
    "APoE: 1/25",
    "APoE: 1/100",
    "APoE: 1/500",
    "APoE: 1/1000",
    "APoE: 1/2500",
]
AGG = AggregationEnum.MEAN


# no cache, do I get the correct DataFrame?
def test_extract_m_values(mean_mags_fixture):
    df = dm_parameter_generation.extract_m_values(
        SITE_NAMES, FREQUENCIES, AGG, no_cache=True
    )
    pandas.testing.assert_index_equal(df.index, pd.Index(SITE_NAMES, name="site_name"))


# create a cache with a small number of sites. then run again with more sites. Do I get the correct DataFrame?
def test_extract_m_values_cache(mean_mags_fixture, workingfolder_fixture):
    cache_filepath = (
        Path(dm_parameter_generation.WORKING_FOLDER) / f"mag_agg-{AGG.name}.csv"
    )

    _ = dm_parameter_generation.extract_m_values(SITE_NAMES, FREQUENCIES, AGG)
    site_names = SITE_NAMES + ["-45.500~166.700", "Maraetai"]
    df_cache = pd.read_csv(cache_filepath, index_col=["site_name"])
    pandas.testing.assert_index_equal(
        df_cache.index, pd.Index(SITE_NAMES, name="site_name"), check_order=False
    )

    # create a chache. re-run w/ same locs. do I get correct df?
    df1 = dm_parameter_generation.extract_m_values(site_names, FREQUENCIES, AGG)
    pandas.testing.assert_index_equal(
        df1.index, pd.Index(site_names, name="site_name"), check_order=False
    )

    df_cache = pd.read_csv(cache_filepath, index_col=["site_name"])
    pandas.testing.assert_frame_equal(df_cache, df1, check_like=True)


# all locations are present in the cache, but new poes requested
def test_extract_m_values_poes1(mean_mags_fixture, workingfolder_fixture):

    _ = dm_parameter_generation.extract_m_values(SITE_NAMES, FREQUENCIES, AGG)
    frequencies = FREQUENCIES + ["APoE: 1/50", "APoE: 1/250"]
    df1 = dm_parameter_generation.extract_m_values(SITE_NAMES, frequencies, AGG)
    assert (df1.columns == frequencies).all()

    cache_filepath = (
        Path(dm_parameter_generation.WORKING_FOLDER) / f"mag_agg-{AGG.name}.csv"
    )
    df_cache = pd.read_csv(cache_filepath, index_col=["site_name"])
    print(df1)
    print(df_cache)


# new locations and new poes
def test_extract_m_values_poes2(mean_mags_fixture, workingfolder_fixture):

    _ = dm_parameter_generation.extract_m_values(SITE_NAMES, FREQUENCIES, AGG)
    site_names = SITE_NAMES + ["-45.500~166.700", "Maraetai"]
    frequencies = FREQUENCIES + ["APoE: 1/50", "APoE: 1/250"]
    df1 = dm_parameter_generation.extract_m_values(site_names, frequencies, AGG)
    pandas.testing.assert_index_equal(
        df1.index, pd.Index(site_names, name="site_name"), check_order=False
    )
    assert (df1.columns == frequencies).all()


# subset of locations and new poes
def test_extract_m_values_poes3(mean_mags_fixture, workingfolder_fixture):

    _ = dm_parameter_generation.extract_m_values(SITE_NAMES, FREQUENCIES, AGG)

    site_names = ["Paihia", "-46.200~166.600", "Maraetai"]
    frequencies = ["APoE: 1/100", "APoE: 1/500", "APoE: 1/50", "APoE: 1/250"]
    df = dm_parameter_generation.extract_m_values(site_names, frequencies, AGG)
    pandas.testing.assert_index_equal(
        df.index, pd.Index(site_names, name="site_name"), check_order=False
    )
    assert (df.columns == frequencies).all()
    assert not df.isnull().values.any()

    site_names = ["Opua", "Wellington"]
    frequencies = ["APoE: 1/50"]
    df = dm_parameter_generation.extract_m_values(site_names, frequencies, AGG)
    pandas.testing.assert_index_equal(
        df.index, pd.Index(site_names, name="site_name"), check_order=False
    )
    assert (df.columns == frequencies).all()
    assert not df.isnull().values.any()


# test generated D values against v1 fixture
def test_D_values_against_v1(dandm_v1):

    # remove v1 locations that don't have their own polygon
    replaced_locations = []
    for location in LOCATION_REPLACEMENTS:
        for replaced_location in LOCATION_REPLACEMENTS[location].replaced_locations:
            replaced_locations.append(replaced_location)
    dandm_v1.drop(replaced_locations, axis=0, inplace=True)

    # generate new D values
    D_values = build_d_value_dataframe()

    # Hamilton and Te Puke are flipped. Confirm that there is no difference in the index sets
    assert list(dandm_v1.index.difference(D_values.index)) == []
    assert list(D_values.index.difference(dandm_v1.index)) == []

    # confirm that the reordered D values are the same
    assert D_values.loc[dandm_v1.index,'D'].equals(dandm_v1['D'])

