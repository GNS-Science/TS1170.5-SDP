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
