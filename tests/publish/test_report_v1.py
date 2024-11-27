from borb.pdf import Document

from nzssdt_2023.publish.report import build_report_page, generate_table_rows


def test_table_rows_v1(dm_table_v1, sat_table_v1):

    print(dm_table_v1)
    d_and_m_df = dm_table_v1.flatten()
    print(d_and_m_df)

    named_df = sat_table_v1.named_location_df()
    # grid_df = sat_table_v1.grid_location_df()

    table_rows = list(generate_table_rows(named_df, d_and_m_df, apoe=25))[:5]
    print(table_rows)
    assert table_rows[0] == [
        "Auckland",
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


def test_report_sat_table_v1(sat_table_v1, dm_table_v1):

    named_df = sat_table_v1.named_location_df()
    d_and_m_df = dm_table_v1.flatten()

    report: Document = Document()
    table_rows = list(generate_table_rows(named_df, d_and_m_df, apoe=25))[:5]
    page = build_report_page("C1", apoe=("1", 25), rowdata=table_rows, table_part=1)
    report.add_page(page)

    assert report.get_page(0) == page
