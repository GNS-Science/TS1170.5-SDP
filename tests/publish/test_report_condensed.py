from io import BytesIO

from borb.pdf import PDF, Document
from borb.toolkit import SimpleTextExtraction

from nzssdt_2023.data_creation import constants
from nzssdt_2023.publish import report_condensed_v2, report_v2

SOIL_CLASSES = ["I", "II", "III", "IV", "V", "VI"]
APOE_MAPPINGS = list(zip("abcdefg", [25, 50, 100, 250, 500, 1000, 2500]))


def test_APOE_MAPPINGS_constant():
    print(report_v2.APOE_MAPPINGS)
    assert report_v2.APOE_MAPPINGS[0] == ("a", 25)
    assert report_v2.APOE_MAPPINGS[-1] == ("g", 2500)


def test_SITE_CLASSES_constant():
    print(report_v2.SITE_CLASSES)
    assert ["I", "II", "III", "IV", "V", "VI"] == report_v2.SITE_CLASSES


def test_generate_location_block(named_combo_table):

    rows = report_condensed_v2.generate_location_block(named_combo_table, "Haruru")
    res = next(rows)
    print(res)
    assert res[0] == "1/25", "first field is apoe: 25"


def test_generate_table_rows(named_combo_table):

    rows = report_condensed_v2.generate_table_rows(named_combo_table)
    res = next(rows)

    assert res[0][0] == "Kaitaia", "first location is Kaitaia"
    assert next(res[1]) == next(
        report_condensed_v2.generate_location_block(named_combo_table, "Kaitaia")
    ), "Kaitaia table entries"


# helper functions
def apoe_value(apoe_str: str):
    try:
        return int(apoe_str.split("/")[1])
    except IndexError:
        pass


def validate_d_and_m(row, d_and_m_df):
    location = row[0]
    apoe = apoe_value(row[1])
    print(d_and_m_df)
    print()
    print("validate_d_and_m", location, apoe, row)
    loc_df = d_and_m_df
    df0 = loc_df[
        (loc_df.Location == location)
        & (loc_df["APoE (1/n)"] == apoe)
        & (loc_df["Site Class"] == "I")
    ]

    print(df0)
    # rec = d_and_m_df.loc[location, apoe]
    assert row[2] == str(df0["M"].to_list()[0])
    assert row[3] == report_condensed_v2.format_D(df0["D"].to_list()[0], apoe)


def get_block_location(extracted, current_idx, location_names):
    #  Lookahead in the extracted text to find the location name of the table block
    # print(f'gbl cur_idx {current_idx} {location_names} ')
    for idx, line in enumerate(extracted.splitlines()):
        if idx <= current_idx:
            continue
        row = line.split(" ")
        # print(f"gbl idx: {idx} row: {row}")
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


def validate_page(extracted: str, combo_df):
    location_names = combo_df.Location.unique()

    current_location = get_block_location(extracted, 0, location_names)

    for idx, line in enumerate(extracted.splitlines()):
        row = line.split(" ")

        # standardise the row
        if not row[0] in location_names:  # prepend the location
            row = [current_location] + row

        if (not apoe_value(row[1])) or (row[0] == "page"):
            print("skipping non block row)")
            continue

        if apoe_value(row[1]) == constants.DEFAULT_RPS[0]:  # the first apoe
            print("get new current_location")
            current_location = get_block_location(extracted, idx, location_names)
            print("new current_location", current_location)
            if not current_location:
                # we're all done
                break
            row[0] = current_location

        print(row)

        validate_d_and_m(row, combo_df)
        validate_sa_values(row, combo_df)
        print(current_location, row[1])


def test_report_pdf_values_named(named_combo_table, monkeypatch):

    # Watermark fonts are broken on GHA
    monkeypatch.setattr(report_condensed_v2, "WATERMARK_ENABLED", False)

    report: Document = Document()

    for page in report_condensed_v2.build_pdf_report_pages(
        named_combo_table, "named", "by location name"
    ):
        print("added page")
        report.add_page(page)

    pdf_report = BytesIO()
    PDF.dumps(pdf_report, report)
    pdf_report.seek(0)
    read_pdf = SimpleTextExtraction()
    read_doc = PDF.loads(pdf_report, [read_pdf])

    assert read_doc is not None

    print("checking report values...")
    for idx in read_pdf.get_text():
        print("PDF page >>>", idx)
        validate_page(read_pdf.get_text()[idx], named_combo_table)


def test_report_pdf_values_gridded(grid_combo_table, monkeypatch):

    # Watermark fonts are broken on GHA
    monkeypatch.setattr(report_condensed_v2, "WATERMARK_ENABLED", False)

    report: Document = Document()

    for page in report_condensed_v2.build_pdf_report_pages(
        grid_combo_table, "gridded", "by grid point"
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
        validate_page(read_pdf.get_text()[idx], grid_combo_table)
