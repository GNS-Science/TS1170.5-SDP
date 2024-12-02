from typing import List
import pandas as pd

from io import BytesIO
from pathlib import Path
from borb.pdf import Document
from borb.pdf import PDF
from borb.toolkit import SimpleTextExtraction

from nzssdt_2023.publish import report_condensed_v2, report_v2

SOIL_CLASSES = ["I", "II", "III", "IV", "V", "VI"]
APOE_MAPPINGS = list(zip("abcdefg", [25, 50, 100, 250, 500, 1000, 2500]))

from nzssdt_2023.config import RESOURCES_FOLDER

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


def test_report_pdf_values(): # sat_named_table_v2, dm_table_v2):

    def dm_table_v2():
        filepath = Path(RESOURCES_FOLDER) / "v_cbc" / "d_and_m.json"
        return pd.read_json(filepath, orient="table")

    def sat_named_table_v2():
        filepath = Path(RESOURCES_FOLDER) / "v_cbc" / "named_locations.json"
        return pd.read_json(filepath, orient="table")

    named_df = sat_named_table_v2()
    d_and_m_df = dm_table_v2()

    report: Document = Document()

    for page in report_condensed_v2.build_pdf_report_pages(named_df, d_and_m_df, 'named'):
        print('added page')
        report.add_page(page)

    pdf_report = BytesIO()

    PDF.dumps(pdf_report, report)

    pdf_report.seek(0)

    print(pdf_report)

    read_pdf = SimpleTextExtraction()

    read_doc = PDF.loads(pdf_report, [read_pdf])

    assert read_doc is not None

    def validate_d_and_m(row, d_and_m_df):
        location = row[0]
        apoe = int(row[1].split('/')[1])
        rec = d_and_m_df.loc[location, apoe]
        assert row[2] == str(rec["M"])
        assert row[3] == report_condensed_v2.format_D(rec["D"], apoe)

    def validate_sa_values(row, location_df):
        location = row[0]
        apoe = int(row[1].split('/')[1])
        site_classes = location_df["Site Class"].unique().tolist()
        loc_df = location_df[location_df.Location == location]

        for idx, site_class in enumerate(site_classes):
            apoe_df = loc_df[
                    (loc_df["APoE (1/n)"] == apoe)
                    & (loc_df["Site Class"] == site_class)
                ]

            for sc_tup in apoe_df.itertuples():
                df_row = [
                    round(sc_tup.PGA, 2),
                    round(sc_tup.Sas, 2),
                    round(sc_tup.Tc, 2),
                    round(sc_tup.Td, 1),
                ]
                assert [float(x) for x in row[(idx*4)+4:(idx*4)+8]] == df_row
                assert row[(idx*4)+4:(idx*4)+8] == [str(x) for x in df_row]

    def validate_page(extracted:str, named_df, d_and_m_df):
        location_names = named_df.Location.unique()
        for idx, line in enumerate(extracted.splitlines()):
            print('l', idx)
            row = line.split(' ')
            if row[0] in location_names:
                validate_d_and_m(row, d_and_m_df)
                validate_sa_values(row, named_df)

    for idx in read_pdf.get_text():
        print('PDF page >>>', idx)
        validate_page(read_pdf.get_text()[idx], named_df, d_and_m_df)

    # assert 0
    ### Auckland 1/250 6.2 n/a 0.09 0.19 0.36 3.0 0.11 0.22 0.44 2.8 0.12 0.26 0.52 2.6 0.13 0.3 0.61 2.6 0.14 0.34 0.65 2.6 0.15 0.39 0.73 2.5

