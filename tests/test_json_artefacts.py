"""
Check the new dataframes, serialised are similar to v1
"""
# import pathlib
from io import StringIO

# from nzssdt_2023.config import RESOURCES_FOLDER
# from nzssdt_2023.data_creation import constants
import pandas as pd
import pytest

from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.publish.convert import DistMagTable

# from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen


def test_build_and_serialise_named_locations_json_serialisation():
    # this should use truncated sites list
    ...


def test_build_and_serialise_grid_locations():
    # this should use truncated list e.g. 5 locations
    ...


@pytest.mark.skip("WIP")
def test_sat_named_tables_version1_vs_2(sat_table_v1, sat_named_table_v2):
    print(sat_table_v1.named_location_df())
    # print(sat_table_v1.grid_location_df())

    print()
    print(sat_named_table_v2)
    assert 0


@pytest.mark.parametrize(
    "city",
    [
        "Auckland",
        "Christchurch",
        "Dunedin",
        "Wellington",
    ],
)
@pytest.mark.parametrize("apoe", constants.DEFAULT_RPS)
def test_d_and_m_tables_version1_vs_2(dm_table_v1, dm_table_v2, city, apoe):
    # D&M values shouldn't have changed between versions
    v1_flat = dm_table_v1.flatten()
    v2_flat = dm_table_v2  # v2 has been flattened before serialization

    _v1 = v1_flat.loc[(city, apoe)]
    _v2 = v2_flat.loc[(city, apoe)]
    assert _v1.all() == _v2.all()


def test_d_and_m_json_serialisation(mean_mags_fixture, workingfolder_fixture):
    # pick up https://github.com/GNS-Science/TS1170.5-SDP/issues/61

    site_list = ["Auckland", "Christchurch", "Dunedin", "Hamilton", "Wellington"]
    dm_df = dm_gen.create_D_and_M_df(site_list)
    flat_df = DistMagTable(dm_df).flatten().infer_objects()

    fsim = StringIO()

    flat_df.to_json(
        fsim,
        index=True,
        orient="table",
        indent=2,
    )

    fsim.seek(0)

    rehydrated = pd.read_json(fsim, orient="table")

    # check M & D are numeric dtypes
    assert rehydrated.M.dtype == "float"
    assert rehydrated.D.dtype == "float"

    print(dir(rehydrated.index))
    print(rehydrated.index)

    # check we have all the locations
    assert rehydrated.index.to_frame()["Location"].unique().tolist() == site_list

    # check we have all the APOES
    assert (
        rehydrated.index.to_frame()["APoE (1/n)"].unique().tolist()
        == constants.DEFAULT_RPS
    )

    # or ...
    # assert rehydrated.index.to_frame()['APoE (1/n)'].unique().tolist() == sorted(list(constants.RP_TO_POE.keys()))
