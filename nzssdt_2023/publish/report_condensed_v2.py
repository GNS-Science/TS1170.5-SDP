"""
Build PDF and equivalent CSV table structures for version 2+ using the OLD format.

This module uses the `borb` library to produce the PDF document.

TODO:
 - [x] extra column Td to each soil/site class

methods:
 build_report_page

"""

import csv
from decimal import Decimal
from itertools import islice
from pathlib import Path
from typing import Iterator, List, Tuple, Union

import pandas as pd
from borb.pdf import (
    PDF,
    Alignment,
    ChunkOfText,
    Document,
    FixedColumnWidthTable,
    HeterogeneousParagraph,
    Page,
    PageLayout,
    Paragraph,
    SingleColumnLayout,
    TableCell,
    Watermark,
    HexColor
)
from borb.pdf.page.page_size import PageSize

from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER
from nzssdt_2023.data_creation import constants

MAX_PAGE_BLOCKS = 4  # each location block row has 7 apoe rows
SITE_CLASSES = list(constants.SITE_CLASSES.keys())  # check sorting
# APOE_MAPPINGS = list(zip("abcdefg", [25, 50, 100, 250, 500, 1000, 2500]))
APOE_MAPPINGS = list(
    zip(
        "abcdefghij"[: len(constants.DEFAULT_RPS)],
        sorted(constants.DEFAULT_RPS),
    )
)  # check content
VERTICAL_BUFFER = 40


def build_report_page(
    table_id: str,
    rowdata=List[List],
    table_part: int = 1,
):

    # create Document (needed for borbs page layout engine )
    doc: Document = Document()

    # create Page
    PAGE_SIZE = PageSize.A4_LANDSCAPE
    page: Page = Page(
        width=PAGE_SIZE.value[0] + VERTICAL_BUFFER, height=PAGE_SIZE.value[1] + VERTICAL_BUFFER
    )
    layout: PageLayout = SingleColumnLayout(page)

    # add Page to Document
    doc.add_page(page)

    # add watermark
    Watermark(
        text="DRAFT 2024-11-22",
        # font="Helvetica-bold",
        font_size=Decimal(30),
        angle_in_degrees= 27.5,
        horizontal_alignment = Alignment.CENTERED,
        vertical_alignment = Alignment.MIDDLE,
        font_color=HexColor("070707")).paint(
            page, None
    )


    heading = f"TABLE {table_id} part {table_part}: Site demand parameters"
    # heading += f" probability of exceedance of 1/{apoe[1]}"
    layout.add(
        Paragraph(
            heading,
            font="Helvetica-bold",
            font_size=Decimal(10),
            horizontal_alignment=Alignment.CENTERED,
        )
    )

    # create a FixedColumnWidthTable
    print(f"len(rowdata): {len(rowdata)}")
    table = FixedColumnWidthTable(
        number_of_columns=4 + (6 * 4),  # 4 intro, + 4 parameters per siteclass = 28
        number_of_rows=2 + (len(rowdata) * len(constants.DEFAULT_RPS)),
        # adjust the ratios of column widths for this FixedColumnWidthTable
        column_widths=[Decimal(1.75), Decimal(0.75), Decimal(0.5), Decimal(0.5)]
        + 6 * [Decimal(0.5), Decimal(0.5), Decimal(0.5), Decimal(0.5)],
    )

    def add_row_0(table: FixedColumnWidthTable):
        table.add(TableCell(Paragraph(""), column_span=4))
        for sss in SITE_CLASSES:
            table.add(
                TableCell(
                    Paragraph(
                        f"Site Class {sss}",
                        font="Helvetica-bold",
                        font_size=Decimal(9),
                        horizontal_alignment=Alignment.CENTERED,
                        vertical_alignment=Alignment.BOTTOM,
                    ),
                    column_span=4,
                )
            )
        return table

    def add_row_1(table: FixedColumnWidthTable):
        table.add(
            TableCell(
                Paragraph(
                    "Site",
                    font="Helvetica-bold",
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.LEFT,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "APOE",
                    font="Helvetica-bold",
                    font_size=Decimal(7),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "M",
                    font="Helvetica-bold",
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "D",
                    font="Helvetica-bold",
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        )
        for sss in SITE_CLASSES:
            table.add(
                Paragraph(
                    "PGA",
                    font="Helvetica-bold-oblique",
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.CENTERED,
                )
            ).add(
                HeterogeneousParagraph(
                    [
                        ChunkOfText(
                            "S", font="Helvetica-bold-oblique", font_size=Decimal(8)
                        ),
                        ChunkOfText(
                            "as",
                            font="Helvetica-bold",
                            font_size=Decimal(7),
                            vertical_alignment=Alignment.BOTTOM,
                        ),
                    ],
                    horizontal_alignment=Alignment.CENTERED,
                )
            ).add(
                HeterogeneousParagraph(
                    [
                        ChunkOfText(
                            "T",
                            font="Helvetica-bold-oblique",
                            font_size=Decimal(8),
                        ),
                        ChunkOfText(
                            "c",
                            font="Helvetica-bold",
                            font_size=Decimal(7),
                            vertical_alignment=Alignment.BOTTOM,
                        ),
                    ],
                    horizontal_alignment=Alignment.CENTERED,
                )
            ).add(
                HeterogeneousParagraph(
                    [
                        ChunkOfText(
                            "T",
                            font="Helvetica-bold-oblique",
                            font_size=Decimal(8),
                        ),
                        ChunkOfText(
                            "d",
                            font="Helvetica-bold",
                            font_size=Decimal(7),
                            vertical_alignment=Alignment.BOTTOM,
                        ),
                    ],
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        return table

    # table header rows
    table = add_row_0(table)
    table = add_row_1(table)

    # data rows
    for row in rowdata:
        #row[0] is location
        table.add(
            TableCell(
                Paragraph(
                    row[0],  # can't rotate yet
                    font="Helvetica",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.LEFT,
                    vertical_alignment=Alignment.TOP,
                )
                ,row_span = len(constants.DEFAULT_RPS)
            )
        )

        for subrow in row[1]:
            print(f"**** {len(subrow)} {subrow}")
            for cell in subrow:
                try:
                    table.add(
                        Paragraph(
                                str(cell),
                                font="Helvetica",
                                font_size=Decimal(8),
                                horizontal_alignment=Alignment.CENTERED,
                        )
                    )
                except Exception:
                    print(f"bang! `{cell}`")

    table.set_padding_on_all_cells(
        Decimal(0.5), Decimal(0.5), Decimal(0.5), Decimal(0.5)
    )
    layout.add(table)

    # page footer
    layout.add(
        Paragraph(
            f"page {table_part}",
            font="Helvetica",
            font_size=Decimal(9),
            horizontal_alignment=Alignment.CENTERED,
            vertical_alignment=Alignment.BOTTOM,
        )
    )


    return page


def format_D(value, apoe: int) -> Union[str, int]:
    """NB NaN in the source dataframe has different meanings, depending on the apoe..."""
    if pd.isna(value):
        return "n/a" if apoe < 500 else ">20"
    return int(value)

def generate_location_block(sat_table_flat: pd.DataFrame, dm_table_flat: pd.DataFrame, location: str) -> Iterator:
    """build a location block, wiht one row per apoe"""
    location_df = sat_table_flat[sat_table_flat.Location == location]
    site_classes = location_df['Site Class'].unique().tolist()
    apoes = location_df["APoE (1/n)"].unique().tolist()
    for apoe in apoes:
        rec = dm_table_flat.loc[location, apoe]
        d_str = format_D(rec["D"], apoe)
        row = [f"1/{apoe}", rec["M"], d_str]
        for site_class in site_classes:
            apoe_df = location_df[(location_df["APoE (1/n)"] == apoe) & (location_df["Site Class"] == site_class)]
            for sc_tup in apoe_df.itertuples():
                row += [
                        round(sc_tup.PGA, 2),
                        round(sc_tup.Sas, 2),
                        round(sc_tup.Tc, 1),
                        round(sc_tup.Td, 1),
                    ]
        yield(row)

def generate_table_rows(
    sat_table_flat: pd.DataFrame, dm_table_flat: pd.DataFrame
) -> Iterator:
    count = 0
    for location in sat_table_flat.Location.unique():
        yield (
            location.replace('-', ' - '),  # spaces allow wrapping to work
            generate_location_block(sat_table_flat, dm_table_flat, location)
        )
        count +=1
        if count == 4:
            break

def chunks(items, chunk_size):
    iterator = iter(items)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk


if __name__ == "__main__":

    OUTPUT_FOLDER = Path(RESOURCES_FOLDER).parent / "reports" / "v_cbc"

    # TODO shift this into the CLI

    def dm_table_v2():
        filepath = Path(RESOURCES_FOLDER) / "v_cbc" / "d_and_m.json"
        return pd.read_json(filepath, orient="table")

    def sat_named_table_v2():
        filepath = Path(RESOURCES_FOLDER) / "v_cbc" / "named_locations.json"
        return pd.read_json(filepath, orient="table")

    def sat_grid_table_v2():
        filepath = Path(RESOURCES_FOLDER) / "v_cbc" / "grid_locations.json"
        return pd.read_json(filepath, orient="table")

    # sat = sat_table()
    named_df = sat_named_table_v2()
    grid_df = sat_grid_table_v2()
    d_and_m_df = dm_table_v2()

    report_grps = list(zip([0, 1], [named_df, grid_df]))
    report_grp_titles = ["3.4", "3.5"]
    report_names = ["named", "gridded"]

    for report_grp, location_df in report_grps:

        print(report_grp)
        print()
        # for apoe in APOE_MAPPINGS:

        filename = f"{report_names[report_grp]}_location_report_v2-DRAFT"
        print(f"report: {filename}")

        report: Document = Document()

        table_rows = list(generate_table_rows(location_df, d_and_m_df))

        # ### CSV
        # with open(Path(OUTPUT_FOLDER, filename + ".csv"), "w") as out_csv:
        #     writer = csv.writer(out_csv, quoting=csv.QUOTE_NONNUMERIC)
        #     header = ["location", "M", "D"]
        #     for sss in SITE_CLASSES:
        #         for attr in ["PGA", "Sas", "Tc"]:
        #             header.append(f"{sss}-{attr}")
        #     writer.writerow(header)
        #     for row in table_rows:
        #         writer.writerow(row)

        ### PDF
        for idx, chunk in enumerate(chunks(table_rows, MAX_PAGE_BLOCKS)):
            report.add_page(
                build_report_page(
                    f"{report_grp_titles[report_grp]}",
                    list(chunk),
                    table_part=idx + 1,
                )
            )

        report.add_page(
                build_report_page(
                    f"{report_grp_titles[report_grp]}",
                    [],
                    table_part=1,
                )
            )

        with open(Path(OUTPUT_FOLDER, filename + ".pdf"), "wb") as out_file_handle:
            PDF.dumps(out_file_handle, report)

        assert 0
