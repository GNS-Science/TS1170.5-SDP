"""
Build PDF and equivalent CSV table structures for version 2+ using the new table format.

This module uses the `borb` library to produce the PDF document.

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
    table_description,
    rowdata=List[List],
    table_part: int = 1,
    is_final: bool = False,
    print_footer: bool = False,
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
    if not is_final and WATERMARK_ENABLED:
        Watermark(
            text="DRAFT " + time.strftime("%Y-%m-%d %H:%M"),
            # font="Helvetica-bold",
            # font_size=Decimal(18),
            # angle_in_degrees=27.5,
            horizontal_alignment=Alignment.CENTERED,
            vertical_alignment=Alignment.MIDDLE,
            font_color=HexColor("070707"),
        ).paint(page, None)

    heading = f"Table {table_id} - Site demand parameters {table_description}"
    if table_part > 1:
        heading += " (continued)"
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
        column_widths=[Decimal(1.7), Decimal(0.8), Decimal(0.5), Decimal(0.5)]
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
                    "Location" if table_id == "3.1" else "Grid point (lat-lon)",
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
        print("@@@ row:", row)

        if row[0][1] == row[0][0]:
            location_str = row[0][0]
        else:
            location_str = (
                row[0][0] + ', "' + searchable_ascii_name(row[0][0], row[0][1]) + '"'
            )  # add 2nd chunk for searching anglicised names (no macrons)
        print(f"build_report_page location_str: {location_str}")
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

        for subrow in row[1]:
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
    if print_footer:
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

    for apoe in apoes:
        rec = location_df[
            (location_df["Site Class"] == "I") & (location_df["APoE (1/n)"] == apoe)
        ]  # get site_class I

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
        print("generate_location_block -> row", row, location)
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
    combo_table: pd.DataFrame, modify_locations: bool = False, location_limit: int = 0
) -> Iterator:
    count = 0
    for location in combo_table.Location.unique():

        count += 1
        yield (
            locations_tuple_padded(location, modify_locations),
            generate_location_block(combo_table, location),
        )

        if count % 10 == 0:
            print(f"row count: {count}")

        if location_limit and (count >= location_limit):
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


def build_pdf_report_pages(
    location_df: pd.DataFrame,
    report_name: str,
    table_description: str,
    is_final: bool = False,
    location_limit: int = 0,
    modify_locations: bool = True,
):
    print("build_pdf_report_pages", report_name)
    ### PDF
    table_rows = generate_table_rows(location_df, modify_locations, location_limit)
    for idx, chunk in enumerate(chunks(table_rows, MAX_PAGE_BLOCKS)):
        yield build_report_page(
            report_name,
            table_description,
            list(chunk),
            table_part=idx + 1,
            is_final=is_final,
        )


def publish_gridded(
    location_df: pd.DataFrame,
    output_folder: Path,
    produce_csv: bool = True,
    is_final: bool = False,
    location_limit: int = 0,
):
    publish_table(
        location_df,
        output_folder,
        table_title="3.2",
        table_description="by grid point",
        filename="gridded_location_report",
        produce_csv=produce_csv,
        is_final=is_final,
        location_limit=location_limit,
        modify_locations=False,
    )


def publish_named(
    location_df: pd.DataFrame,
    output_folder: Path,
    produce_csv: bool = True,
    is_final: bool = False,
    location_limit: int = 0,
):
    publish_table(
        location_df,
        output_folder,
        table_title="3.1",
        table_description="by location name",
        filename="named_location_report",
        produce_csv=produce_csv,
        is_final=is_final,
        location_limit=location_limit,
        modify_locations=True,
    )


def publish_table(
    location_df: pd.DataFrame,
    output_folder: Path,
    table_title: str,
    table_description: str,
    filename: str,
    produce_csv: bool = True,
    is_final: bool = False,
    location_limit: int = 0,
    modify_locations: bool = True,
):

    if not is_final:
        filename += "-DRAFT"

    print(f"report: {filename}")

    report: Document = Document()

    if produce_csv:
        csv_rows = generate_csv_rows(location_df, modify_locations=False)

        ### CSV
        with open(Path(output_folder, filename + ".csv"), "w") as out_csv:
            writer = csv.writer(out_csv, quoting=csv.QUOTE_NONNUMERIC)
            header = ["location", "location_ascii", "apoe", "M", "D"]
            for sss in SITE_CLASSES:
                for attr in ["PGA", "Sas", "Tc", "Td"]:
                    header.append(f"{sss}-{attr}")
            writer.writerow(header)
            for row in csv_rows:
                writer.writerow(row)

    # PDF
    for page in build_pdf_report_pages(
        location_df,
        table_title,
        table_description,
        is_final,
        location_limit,
        modify_locations,
    ):
        report.add_page(page)

    with open(Path(output_folder, filename + ".pdf"), "wb") as out_file_handle:
        PDF.dumps(out_file_handle, report)


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
    publish_named(
        named_df,
        OUTPUT_FOLDER,
        PRODUCE_CSV,  # CSV
        location_limit=LOCATION_LIMIT,
        is_final=False,
    )
    grid_df = combo_grid_table()
    publish_gridded(
        grid_df,
        OUTPUT_FOLDER,
        PRODUCE_CSV,  # CSV
        location_limit=LOCATION_LIMIT,
        is_final=False,
    )
