import pathlib

import pandas as pd
import pytest
from borb.pdf import Document

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable
from nzssdt_2023.publish.report import build_report_page, generate_table_rows


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename))
    return SatTable(df)


@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(
        RESOURCES_FOLDER, "pipeline", "v1", filename
    )  # not as per publish/report @ v1
    # df = pd.read_csv(csv_path)
    return DistMagTable(csv_path)


def test_table_rows(dm_table, sat_table):

    print(dm_table)
    d_and_m_df = dm_table.flatten()
    print(d_and_m_df)

    named_df = sat_table.named_location_df()
    grid_df = sat_table.grid_location_df()

    table_rows = list(generate_table_rows(named_df, d_and_m_df, apoe=25))[:5]
    print(table_rows)
    assert table_rows[0] == [
        "Kaitaia",
        6.2,
        "n/a",
        0.02,
        0.03,
        0.4,
        0.02,
        0.04,
        0.4,
        0.02,
        0.05,
        0.5,
        0.03,
        0.06,
        0.5,
        0.03,
        0.07,
        0.5,
        0.03,
        0.09,
        0.6,
    ]


def test_report_sat_table(sat_table, dm_table):

    named_df = sat_table.named_location_df()
    d_and_m_df = dm_table.flatten()

    report: Document = Document()
    table_rows = list(generate_table_rows(named_df, d_and_m_df, apoe=25))[:5]
    page = build_report_page("C1", apoe=("1", 25), rowdata=table_rows, table_part=1)
    report.add_page(page)

    assert report.get_page(0) == page
