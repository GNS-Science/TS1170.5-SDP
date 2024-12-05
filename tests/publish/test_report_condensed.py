from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from borb.pdf import PDF, Document
from borb.toolkit import SimpleTextExtraction

from nzssdt_2023 import config
from nzssdt_2023.data_creation import constants
from nzssdt_2023.publish import report_condensed_v2, report_v2

# from pathlib import Path


FIXTURES = Path(__file__).parent.parent / "fixtures"

SOIL_CLASSES = ["I", "II", "III", "IV", "V", "VI"]
APOE_MAPPINGS = list(zip("abcdefg", [25, 50, 100, 250, 500, 1000, 2500]))


def test_APOE_MAPPINGS_constant():
    print(report_v2.APOE_MAPPINGS)
    assert report_v2.APOE_MAPPINGS[0] == ("a", 25)
    assert report_v2.APOE_MAPPINGS[-1] == ("g", 2500)


def test_SITE_CLASSES_constant():
    print(report_v2.SITE_CLASSES)
    assert ["I", "II", "III", "IV", "V", "VI"] == report_v2.SITE_CLASSES


def test_generate_location_block(sat_named_table_v2, dm_table_v2):
    named_df = sat_named_table_v2
    d_and_m_df = dm_table_v2

    rows = report_condensed_v2.generate_location_block(named_df, d_and_m_df, "Haruru")
    res = next(rows)
    print(res)
    assert res[0] == "1/25", "first field is apoe: 25"


def test_generate_table_rows(sat_named_table_v2, dm_table_v2):
    named_df = sat_named_table_v2
    d_and_m_df = dm_table_v2

    rows = report_condensed_v2.generate_table_rows(named_df, d_and_m_df)
    res = next(rows)

    assert res[0][0] == "Kaitaia", "first location is Katiaia"
    assert next(res[1]) == next(
        report_condensed_v2.generate_location_block(named_df, d_and_m_df, "Kaitaia")
    ), "Kaitaia table entries"


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

# helper functions
def apoe_value(apoe_str: str):
    try:
        return int(apoe_str.split("/")[1])
    except IndexError:
        pass


def validate_d_and_m(row, d_and_m_df):
    location = row[0]
    apoe = apoe_value(row[1])
    rec = d_and_m_df.loc[location, apoe]
    assert row[2] == str(rec["M"])
    assert row[3] == report_condensed_v2.format_D(rec["D"], apoe)


def get_block_location(extracted, current_idx, location_names):
    #  Lookahead in the extracted text to find the locatio name of the table block
    for idx, line in enumerate(extracted.splitlines()):
        if idx <= current_idx:
            continue
        row = line.split(" ")
        if not row[0] in location_names:
            continue
        return row[0]


def validate_sa_values(row, location_df):
    location = row[0]
    apoe = apoe_value(row[1])
    site_classes = location_df["Site Class"].unique().tolist()
    loc_df = location_df[location_df.Location == location]

    for idx, site_class in enumerate(site_classes):
        apoe_df = loc_df[
            (loc_df["APoE (1/n)"] == apoe) & (loc_df["Site Class"] == site_class)
        ]

        for sc_tup in apoe_df.itertuples():
            df_row = [
                round(sc_tup.PGA, 2),
                round(sc_tup.Sas, 2),
                round(sc_tup.Tc, 2),
                round(sc_tup.Td, 1),
            ]
            assert [float(x) for x in row[(idx * 4) + 4 : (idx * 4) + 8]] == df_row
            assert row[(idx * 4) + 4 : (idx * 4) + 8] == [str(x) for x in df_row]


def validate_page(extracted: str, named_df, d_and_m_df):
    location_names = named_df.Location.unique()

    current_location = get_block_location(extracted, 0, location_names)

    for idx, line in enumerate(extracted.splitlines()):
        row = line.split(" ")

        # standardise the row
        if not row[0] in location_names:  # prepend the location
            row = [current_location] + row

        if not apoe_value(row[1]):
            print("skipping non block row)")
            continue

        if apoe_value(row[1]) == constants.DEFAULT_RPS[0]:  # the first apoe
            print("get new current_location")
            current_location = get_block_location(extracted, idx, location_names)
            row[0] = current_location
            print("new current_location", current_location)

        print(row)

        validate_d_and_m(row, d_and_m_df)
        validate_sa_values(row, named_df)
        print(current_location, row[1])


@pytest.fixture(scope="module")
def dm_table_v2_mini():
    filepath = FIXTURES / "v2_json" / "d_and_m_mini.json"
    return pd.read_json(filepath, orient="table")


@pytest.fixture(scope="module")
def sat_named_table_v2_mini():
    filepath = FIXTURES / "v2_json" / "named_locations_mini.json"
    return pd.read_json(filepath, orient="table")


@pytest.fixture(scope="module")
def dm_table_first_10():
    filepath = FIXTURES / "v2_json" / "first_10_d_and_m.json"
    return pd.read_json(filepath, orient="table")


@pytest.fixture(scope="module")
def sa_table_grid_10():
    filepath = FIXTURES / "v2_json" / "first_10_grid_locations.json"
    return pd.read_json(filepath, orient="table")


@pytest.fixture(scope="module")
def sa_table_named_10():
    filepath = (
        FIXTURES / "v2_json" / "first_10_named_locations.json"
    )
    return pd.read_json(filepath, orient="table")


def test_report_pdf_values_named(
    sat_named_table_v2_mini, dm_table_v2_mini, monkeypatch
):

    # Watermark fonts are broken on GHA
    monkeypatch.setattr(report_condensed_v2, "WATERMARK_ENABLED", False)

    named_df = sat_named_table_v2_mini
    d_and_m_df = dm_table_v2_mini

    report: Document = Document()

    for page in report_condensed_v2.build_pdf_report_pages(
        named_df, d_and_m_df, "named"
    ):
        print("added page")
        report.add_page(page)

    pdf_report = BytesIO()
    PDF.dumps(pdf_report, report)
    pdf_report.seek(0)
    read_pdf = SimpleTextExtraction()
    read_doc = PDF.loads(pdf_report, [read_pdf])

    assert read_doc is not None

    for idx in read_pdf.get_text():
        print("PDF page >>>", idx)
        validate_page(read_pdf.get_text()[idx], named_df, d_and_m_df)


def test_report_pdf_values_gridded(dm_table_first_10, sa_table_grid_10, monkeypatch):

    # Watermark fonts are broken on GHA
    monkeypatch.setattr(report_condensed_v2, "WATERMARK_ENABLED", False)

    gridded_df = sa_table_grid_10
    d_and_m_df = dm_table_first_10

    report: Document = Document()

    for page in report_condensed_v2.build_pdf_report_pages(
        gridded_df, d_and_m_df, "gridded"
    ):
        print("added page")
        report.add_page(page)

    pdf_report = BytesIO()
    PDF.dumps(pdf_report, report)
    pdf_report.seek(0)
    read_pdf = SimpleTextExtraction()
    read_doc = PDF.loads(pdf_report, [read_pdf])

    assert read_doc is not None

    for idx in read_pdf.get_text():
        print("PDF page >>>", idx)
        validate_page(read_pdf.get_text()[idx], gridded_df, d_and_m_df)
