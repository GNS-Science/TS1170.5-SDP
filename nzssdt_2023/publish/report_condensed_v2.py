"""
Build PDF and equivalent CSV table structures for version 2+ using the OLD format.

This module uses the `borb` library to produce the PDF document.

TODO:
 - [x] extra column Td to each soil/site class

methods:
 build_report_page

"""

import csv
import time
from decimal import Decimal
from itertools import islice
from pathlib import Path
from typing import Iterator, List, Union

import pandas as pd
from borb.pdf import (
    PDF,
    Alignment,
    ChunkOfText,
    Document,
    FixedColumnWidthTable,
    HeterogeneousParagraph,
    HexColor,
    Page,
    PageLayout,
    Paragraph,
    SingleColumnLayout,
    TableCell,
    TrueTypeFont,
    Watermark,
)
from borb.pdf.page.page_size import PageSize
from nzshm_common.location import get_name_with_macrons

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.data_creation import constants

PRODUCE_CSV = True
LOCATION_LIMIT = 0
WATERMARK_ENABLED = True
MAX_PAGE_BLOCKS = 4  # each location block row has 7 apoe rows
SITE_CLASSES = list(constants.SITE_CLASSES.keys())  # check sorting
APOE_MAPPINGS = list(
    zip(
        "abcdefghij"[: len(constants.DEFAULT_RPS)],
        sorted(constants.DEFAULT_RPS),
    )
)

medium_font = TrueTypeFont.true_type_font_from_file(
    open(Path(RESOURCES_FOLDER) / "fonts/static/OpenSans-Medium.ttf", "rb").read()
)


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
        width=PAGE_SIZE.value[0],
        height=PAGE_SIZE.value[1],
    )
    layout: PageLayout = SingleColumnLayout(page)

    # add Page to Document
    doc.add_page(page)

    # add watermark
    if WATERMARK_ENABLED:
        Watermark(
            text="DRAFT " + time.strftime("%Y-%m-%d %H:%M"),
            # font="Helvetica-bold",
            # font_size=Decimal(18),
            # angle_in_degrees=27.5,
            horizontal_alignment=Alignment.CENTERED,
            vertical_alignment=Alignment.MIDDLE,
            font_color=HexColor("070707"),
        ).paint(page, None)

    heading = f"TABLE {table_id} part {table_part}: Site demand parameters"
    # heading += f" probability of exceedance of 1/{apoe[1]}"
    layout.add(
        Paragraph(
            heading,
            font="Helvetica-bold",
            font_size=Decimal(10),
            horizontal_alignment=Alignment.LEFT,
        )
    )

    # create a FixedColumnWidthTable
    # print(f"len(rowdata): {len(rowdata)}")
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

    def searchable_ascii_name(macronised, non_maconrised):
        """return just the macronised substituions for searching"""
        macronised_words = macronised.split(" ")
        non_macronised_words = non_maconrised.split(" ")
        assert len(macronised_words) == len(non_macronised_words)

        res = []
        for idx, word in enumerate(macronised_words):
            if word == non_macronised_words[idx]:
                continue
            else:
                res.append(non_macronised_words[idx])
        # print("searchable name:", " ".join(res))
        return " ".join(res)

    def add_row_1(table: FixedColumnWidthTable):
        table.add(
            TableCell(
                Paragraph(
                    "Location",
                    font="Helvetica-bold",
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.LEFT,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "APoE",
                    font="Helvetica-bold",
                    font_size=Decimal(8),
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
                            "a,s",
                            font="Helvetica-bold",
                            font_size=Decimal(8),
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
                            font_size=Decimal(8),
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
                            font_size=Decimal(8),
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
        # row[0] is location
        # print("@@@ row:", row)

        if row[0][1] == row[0][0]:
            location_str = row[0][0]
        else:
            location_str = (
                row[0][0] + ', "' + searchable_ascii_name(row[0][0], row[0][1]) + '"'
            )  # add 2nd chunk for searching anglicised names (no macrons)
        table.add(
            TableCell(
                Paragraph(
                    location_str,
                    # font="Helvetica",
                    font=medium_font,
                    font_size=Decimal(8),
                    horizontal_alignment=Alignment.LEFT,
                    vertical_alignment=Alignment.MIDDLE,
                ),
                row_span=len(constants.DEFAULT_RPS),
            )
        )
        ###
        #
        #  This was an attempt to do transparent text.
        #  It works except for values [`Waihi Bowentown`  `Ōakura (New Plymouth District)`]
        #
        # else:
        #  1st Chunk is visible Macronnised names
        #     # chunks = [
        #     #                 ChunkOfText(
        #     #                     row[0][0] + " " +  searchable_ascii_name(row[0][0], row[0][1]),
        #     #                     # font="Helvetica",
        #     #                     font=medium_font,
        #     #                     font_size=Decimal(8),
        #     #                     # font_color=HexColor("ffffff"),
        #     #                     # font_transparency=100
        #     #                 ),
        #  2nd chunk for searching anglicised names (no macrons)
        #     #                 # ChunkOfText("  " + searchable_ascii_name(row[0][0], row[0][1]),
        #     #                 #     font_size=Decimal(3),
        #     #                 #     font=medium_font,
        #     #                 #     font_color=HexColor("fefefe"),
        #     #                 # ),
        #     #                 # ChunkOfText(
        #     #                 #     ,   (can't rotate yet)
        #     #                 #     # font="Helvetica",
        #     #                 #     font=medium_font,
        #     #                 #     font_size=Decimal(8),
        #     #                 #     font_color=HexColor("ffffff"),
        #     #                 # ),
        #     #             ]
        #     # # chunks = reversed(chunks)
        #     # table.add(
        #     #     TableCell(
        #     #         HeterogeneousParagraph(
        #     #             chunks,
        #     #             horizontal_alignment=Alignment.LEFT,
        #     #             vertical_alignment=Alignment.MIDDLE,
        #     #         ),
        #     #         # Paragraph(row[0][0],
        #     #         #     font=medium_font,
        #     #         #     font_size=Decimal(8),
        #     #         # ),
        #     #         row_span=len(constants.DEFAULT_RPS),
        #     #     )
        #     # )

        # print(row[1])

        for subrow in row[1]:
            # print(f"**** {len(subrow)} {subrow}")
            for cell in subrow:
                try:
                    table.add(
                        TableCell(
                            Paragraph(
                                str(cell),
                                font="Helvetica",
                                font_size=Decimal(8),
                                horizontal_alignment=Alignment.CENTERED,
                                vertical_alignment=Alignment.MIDDLE,
                            ),
                            # padding_top=Decimal(2.0),
                            # border_width=Decimal(0.5),
                            # preferred_height=Decimal(50)
                        )
                    )
                except Exception:
                    print(f"bang! `{cell}`")

    table.set_padding_on_all_cells(
        padding_top=Decimal(2.5),
        padding_right=Decimal(1.5),
        padding_bottom=Decimal(1.0),
        padding_left=Decimal(1.5),
    )
    table.set_border_width_on_all_cells(border_width=Decimal(0.5))
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
    return str(value)


def generate_location_block(combo_table: pd.DataFrame, location: str) -> Iterator:
    """build a location block, with one row per apoe"""
    location_df = combo_table[combo_table.Location == location]
    site_classes = location_df["Site Class"].unique().tolist()
    apoes = location_df["APoE (1/n)"].unique().tolist()

    # print(location_df)
    # print(location_df.index)

    for apoe in apoes:
        rec = location_df[
            (location_df["Site Class"] == "I") & (location_df["APoE (1/n)"] == apoe)
        ]  # get site_class I
        # print(rec[])
        # assert 0
        d_str = format_D(rec["D"].to_list()[0], apoe)
        row = [f"1/{apoe}", rec["M"].to_list()[0], d_str]
        for site_class in site_classes:
            apoe_df = location_df[
                (location_df["APoE (1/n)"] == apoe)
                & (location_df["Site Class"] == site_class)
            ]
            for sc_tup in apoe_df.itertuples():
                row += [
                    round(sc_tup.PGA, 2),
                    round(sc_tup.Sas, 2),
                    round(sc_tup.Tc, 2),
                    round(sc_tup.Td, 1),
                ]
        # print("generate_location_block -> row", row)
        yield (row)


def locations_tuple_padded(location: str, modify_locations: bool):
    if not modify_locations:
        return get_name_with_macrons(location), location

    # spaces allow wrapping to work, # non-macronised for searching
    return (
        get_name_with_macrons(location).replace("-", " - "),
        location.replace("-", " - "),
    )


def generate_table_rows(
    combo_table: pd.DataFrame,
    modify_locations: bool = False,
) -> Iterator:
    count = 0

    # print("generate_table_rows", combo_table.Location.unique())
    for location in combo_table.Location.unique():
        # location = location.replace("-", " - ")

        count += 1
        # if not (location == "Wellington"):
        #     continue
        # if count < 46:
        #     continue
        # if count in [47, 86]:  #47 `Waihi Bowentown` BOOM, 85 `Ōakura (New Plymouth District)`
        #     continue
        # print("loc", location)
        yield (
            locations_tuple_padded(location, modify_locations),
            generate_location_block(combo_table, location),
        )

        if count % 10 == 0:
            print(f"row count: {count}")

        if LOCATION_LIMIT and (count >= LOCATION_LIMIT):
            break


def generate_csv_rows(
    combo_table: pd.DataFrame,
    modify_locations: bool = False,
) -> Iterator:
    count = 0
    for location in combo_table.Location.unique():
        for block in generate_location_block(combo_table, location):
            yield list(locations_tuple_padded(location, modify_locations)) + block
        count += 1


def chunks(items, chunk_size):
    iterator = iter(items)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk


def build_pdf_report_pages(location_df: pd.DataFrame, report_name: str):
    print("build_pdf_report_pages", report_name, report_name == "named")
    ### PDF
    table_rows = generate_table_rows(location_df, report_name == "named")
    for idx, chunk in enumerate(chunks(table_rows, MAX_PAGE_BLOCKS)):
        yield build_report_page(
            f"{report_name}",
            list(chunk),
            table_part=idx + 1,
        )


if __name__ == "__main__":

    OUTPUT_FOLDER = Path(RESOURCES_FOLDER).parent / "reports" / "v_cbc"

    # TODO shift this into the CLI
    def combo_named_table():
        filepath = (
            Path(RESOURCES_FOLDER) / "v_cbc" / "first_10_named_locations_combo.json"
        )
        return pd.read_json(filepath, orient="table")

    def combo_grid_table():
        filepath = (
            Path(RESOURCES_FOLDER) / "v_cbc" / "first_10_grid_locations_combo.json"
        )
        return pd.read_json(filepath, orient="table")

    named_df = combo_named_table()
    grid_df = combo_grid_table()

    report_grps = list(zip([0, 1], [named_df, grid_df]))
    report_grp_titles = ["3.4", "3.5"]
    report_names = ["named", "gridded"]

    for report_grp, location_df in report_grps:

        filename = f"{report_names[report_grp]}_location_report_v2-DRAFT"
        print(f"report: {filename}")

        report: Document = Document()

        if PRODUCE_CSV:
            csv_rows = generate_csv_rows(
                location_df, report_names[report_grp] == "named"
            )

            ### CSV
            with open(Path(OUTPUT_FOLDER, filename + ".csv"), "w") as out_csv:
                writer = csv.writer(out_csv, quoting=csv.QUOTE_NONNUMERIC)
                header = ["location", "location_ascii", "apoe", "M", "D"]
                for sss in SITE_CLASSES:
                    for attr in ["PGA", "Sas", "Tc", "Td"]:
                        header.append(f"{sss}-{attr}")
                writer.writerow(header)
                for row in csv_rows:
                    writer.writerow(row)

        for page in build_pdf_report_pages(location_df, report_names[report_grp]):
            report.add_page(page)

        with open(Path(OUTPUT_FOLDER, filename + ".pdf"), "wb") as out_file_handle:
            PDF.dumps(out_file_handle, report)
