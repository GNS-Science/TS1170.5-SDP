import pytest

from nzssdt_2023.data_creation import constants
from nzssdt_2023.data_creation import dm_parameter_generation as dm_gen
from nzssdt_2023.publish import convert


def build_flat_sat_table(mini_sat_table):
    print(mini_sat_table)
    print()

    # parameters = [
    #     "PGA",
    #     "Sas",
    #     "Tc",
    #     "Td",
    #     "PSV", "PGA Floor", "Sas Floor", "PSV Floor", "Td Floor"]

    df2 = mini_sat_table.stack().stack().stack()  # .reset_index()
    df2 = df2.unstack(level=1).reset_index()

    df2.level_1 = df2.level_1.apply(lambda x: x.replace("Site Class ", ""))
    df2.level_2 = df2.level_2.apply(lambda x: int(x.replace("APoE: 1/", "")))

    return df2.rename(
        columns={
            "level_0": "Location",
            "level_1": "Site Class",
            "level_2": "APoE (1/n)",
        }
    )


@pytest.mark.skip("WIP - needs d&m fixture")
def test_dm_table_flatten(mini_sat_table):

    df2 = build_flat_sat_table(mini_sat_table)
    site_list = df2.Location.unique().tolist()

    print(site_list)
    dm_df = convert.DistMagTable(
        dm_gen.create_D_and_M_df(site_list, rp_list=constants.DEFAULT_RPS)
    ).flatten()

    print("flat d&m")
    print("========")
    print(dm_df)

    print("flat_sat")
    print("========")
    print(df2)

    dj = df2.merge(dm_df, how="left", on=["Location", "APoE (1/n)"])
    print(dj[dj.Location == "Wellington"][dj["APoE (1/n)"] == 500])

    assert 0


@pytest.mark.skip("WIP")
def test_sat_table_flatten(mini_sat_table):

    df2 = build_flat_sat_table(mini_sat_table)

    print(df2)
    assert 0

    # sat = convert.SatTable(mini_sat_table)
    # df = sat.flatten()
    # print(df)
    # assert 0
