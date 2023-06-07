import pathlib

import pandas as pd
import numpy as np
import pytest

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import SatTable, DistMagTable

from decimal import Decimal
from typing import Tuple, Iterator, Iterable, List
from itertools import islice

from borb.pdf import SingleColumnLayout
from borb.pdf import PageLayout
from borb.pdf import FixedColumnWidthTable

# from borb.pdf import FlexibleColumnWidthTable
from borb.pdf import TableCell
from borb.pdf import Paragraph
from borb.pdf import HeterogeneousParagraph, ChunkOfText
from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import PDF
from borb.pdf import Alignment
from borb.pdf.page.page_size import PageSize


def build_report_page(table_id: str = "C1", apoe: Tuple[chr, int] = ("a", 25), rowdata=List[List], table_part: int = 1):
    # create Document
    doc: Document = Document()

    # create Page
    page: Page = Page()


    PAGE_SIZE = PageSize.A4_LANDSCAPE
    page: Page = Page(width=PAGE_SIZE.value[0], height=PAGE_SIZE.value[1])

    layout: PageLayout = SingleColumnLayout(page)

    # add Page to Document
    doc.add_page(page)

    SSS = ["I", "II", "III", "IV", "V", "VI"]
    # cotd = "continued"
    TITLE = f"TABLE {table_id}({apoe[0]}) part {table_part}: SITE DEMAND PARAMETERS FOR AN ANNUAL PROBABILITY OF EXCEEDANCE"
    TITLE += f" OF 1/{apoe[1]}"
    layout.add(
        Paragraph(
            TITLE,
            font="Helvetica",
            font_size=Decimal(12),
            horizontal_alignment=Alignment.CENTERED,
        )
    )

    # create a FixedColumnWidthTable
    table = FixedColumnWidthTable(
        number_of_columns=3 + (6 * 3),
        number_of_rows=2 + len(rowdata),
        # adjust the ratios of column widths for this FixedColumnWidthTable
        column_widths=[Decimal(3), Decimal(0.5), Decimal(0.5)]
        + 6 * [Decimal(0.5), Decimal(0.5), Decimal(0.5)],
    )

    def add_row_0(table: FixedColumnWidthTable):
        table.add(TableCell(Paragraph(""), column_span=3))
        for sss in SSS:
            table.add(
                TableCell(
                    Paragraph(
                        f"Site Class {sss}",
                        font="Helvetica-bold",
                        font_size=Decimal(9),
                        horizontal_alignment=Alignment.CENTERED,
                        vertical_alignment=Alignment.BOTTOM,
                    ),
                    column_span=3,
                )
            )
        return table

    def add_row_1(table: FixedColumnWidthTable):
        table.add(
            TableCell(
                Paragraph("Location", font="Helvetica-bold", font_size=Decimal(9), horizontal_alignment=Alignment.LEFT)
            )
        ).add(
            TableCell(
                Paragraph(
                    "M",
                    font="Helvetica-bold",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "D",
                    font="Helvetica-bold",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        )
        for sss in SSS:
            table.add(
                Paragraph(
                    "PGA",
                    font="Helvetica-bold",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            ).add(
                HeterogeneousParagraph(
                    [
                        ChunkOfText("S", font="Helvetica-bold", font_size=Decimal(9)),
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
                            font="Helvetica-bold",
                            font_size=Decimal(9),
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
            )
        return table

    # table header rows
    table = add_row_0(table)
    table = add_row_1(table)

    # data rows
    for row in rowdata:
        table.add(Paragraph(
                row[0],
                font_size=Decimal(9),
                horizontal_alignment=Alignment.LEFT,
            ))

        for cell in row[1:]:
            table.add(Paragraph(
                    cell,
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                ))

    table.set_padding_on_all_cells(Decimal(0.5), Decimal(0.5), Decimal(0.5), Decimal(0.5))
    layout.add(table)

    return page


@pytest.fixture(scope="module")
def sat_table():
    filename = "SaT-variables_v5_corrected-locations.pkl"
    df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename))
    return SatTable(df)


@pytest.fixture(scope="module")
def dm_table():
    filename = "D_and_M_with_floor.csv"
    csv_path = pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename)
    return DistMagTable(csv_path)


def table_rows(sat_table: SatTable, dm_table: DistMagTable, apoe: int) -> Iterator:
    df = sat_table.named_location_df()
    dmt = dm_table.flatten()

    count = 0
    for location in df.Location.unique():
        ldf = df[df.Location == location]
        rec = dmt.loc[location, apoe]
        _d = "n/a" if pd.isna(rec["D"]) else int(rec["D"])
        for tup in ldf.itertuples():
            row = [location, str(rec['M']),  str(_d)]
            for tup2 in ldf[ldf["APoE (1/n)"] == apoe].itertuples():
                row += [str(round(tup2.PGA, 2)), str(round(tup2.Sas, 2)), str(round(tup2.Tc, 1))]
        yield row
        count +=1



def chunks(items, chunk_size):
    iterator = iter(items)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk

# @pytest.mark.skip('WIP')
def test_report_sat_table(sat_table, dm_table):

    report: Document = Document()

    apoe = ('f', 1000)
    for idx, chunk in enumerate(chunks(table_rows(sat_table, dm_table, apoe[1]), 30)):
        print(f"process page {idx+1}")
        report.add_page(build_report_page("C1", apoe, list(chunk), table_part=idx+1))

    with open(
        pathlib.Path(RESOURCES_FOLDER, "named_report.pdf"), "wb"
    ) as out_file_handle:
        PDF.dumps(out_file_handle, report)
