# import pathlib

# import pandas as pd
# import pytest
# from borb.pdf import Document

# from nzssdt_2023.config import RESOURCES_FOLDER
# from nzssdt_2023.convert import DistMagTable, SatTable
from nzssdt_2023.publish import report_condensed

SOIL_CLASSES = ["I", "II", "III", "IV", "V", "VI"]
APOE_MAPPINGS = list(zip("abcdefg", [25, 50, 100, 250, 500, 1000, 2500]))


def test_APOE_MAPPINGS_constant():
    print(report_condensed.APOE_MAPPINGS)
    assert report_condensed.APOE_MAPPINGS[0] == ("a", 25)
    assert report_condensed.APOE_MAPPINGS[-1] == ("i", 10000)


def test_SITE_CLASSES_constant():
    print(report_condensed.SITE_CLASSES)
    assert ["I", "II", "III", "IV", "V", "VI"] == report_condensed.SITE_CLASSES


def test_generate_table_rows():
    ...


def test_build_page_n():
    ...


# @pytest.fixture(scope="module")
# def sat_table():
#     filename = "SaT-variables_v5_corrected-locations.pkl"
#     df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename))
#     return SatTable(df)
#
#
# @pytest.fixture(scope="module")
# def dm_table():
#     filename = "D_and_M_with_floor.csv"
#     csv_path = pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1", filename)
#     return DistMagTable(csv_path)
#
#


# def test_report_sat_table(sat_table, dm_table):
#
#     named_df = sat_table.named_location_df()
#     d_and_m_df = dm_table.flatten()
#
#     report: Document = Document()
#     table_rows = list(generate_table_rows(named_df, d_and_m_df, apoe=25))[:5]
#     page = build_report_page("C1", apoe=("1", 25), rowdata=table_rows, table_part=1)
#     report.add_page(page)
#
#     assert report.get_page(0) == page
