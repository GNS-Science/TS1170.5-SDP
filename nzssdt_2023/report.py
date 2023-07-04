import pathlib
import csv
from decimal import Decimal
from itertools import islice
from typing import Iterator, List, Tuple

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
)
from borb.pdf.page.page_size import PageSize

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable

MAX_PAGE_ROWS = 30
SOIL_CLASSES = ["I", "II", "III", "IV", "V", "VI"]
APOE_MAPPINGS = list(zip("abcdef", [25, 50, 100, 250, 500, 1000, 2500]))
VERTICAL_BUFFER = 40

def build_report_page(
    table_id: str = "C1",
    apoe: Tuple[str, int] = ("a", 25),
    rowdata=List[List],
    table_part: int = 1,
):

    # create Document (needed for borbs page layout engine )
    doc: Document = Document()

    # create Page
    PAGE_SIZE = PageSize.A4_LANDSCAPE
    page: Page = Page(width=PAGE_SIZE.value[0], height=PAGE_SIZE.value[1] + VERTICAL_BUFFER)
    layout: PageLayout = SingleColumnLayout(page)

    # add Page to Document
    doc.add_page(page)

    heading = f"TABLE {table_id}({apoe[0]}) part {table_part}: Site demand parameters for an annual"
    heading += f" probability of exceedance of 1/{apoe[1]}"
    layout.add(
        Paragraph(
            heading,
            font="Helvetica-bold",
            font_size=Decimal(10),
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
        for sss in SOIL_CLASSES:
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
                Paragraph(
                    "Location",
                    font="Helvetica-bold-oblique",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.LEFT,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "M",
                    font="Helvetica-bold-oblique",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        ).add(
            TableCell(
                Paragraph(
                    "D",
                    font="Helvetica-bold-oblique",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )
        )
        for sss in SOIL_CLASSES:
            table.add(
                Paragraph(
                    "PGA",
                    font="Helvetica-bold-oblique",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            ).add(
                HeterogeneousParagraph(
                    [
                        ChunkOfText("S", font="Helvetica-bold-oblique", font_size=Decimal(9)),
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
        table.add(
            Paragraph(
                row[0],
                font="Helvetica",
                font_size=Decimal(9),
                horizontal_alignment=Alignment.LEFT,
            )
        )

        for cell in row[1:]:
            table.add(
                Paragraph(
                    str(cell),
                    font="Helvetica",
                    font_size=Decimal(9),
                    horizontal_alignment=Alignment.CENTERED,
                )
            )

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
            vertical_alignment=Alignment.BOTTOM
        )
    )
    return page


def generate_table_rows(
    sat_table_flat: pd.DataFrame, dm_table_flat: pd.DataFrame, apoe: int
) -> Iterator:

    def format_D(value, apoe: int) -> str:
        """NB NaN in the source dataframe has different meanings, depending on the apoe..."""
        if pd.isna(value):
            return "n/a" if apoe < 500 else ">20"
        return int(value)
    
    for location in sat_table_flat.Location.unique():
        location_df = sat_table_flat[sat_table_flat.Location == location]
        rec = dm_table_flat.loc[location, apoe]
        d_str = format_D(rec["D"], apoe)
        for tup in location_df.itertuples():
            row = [location, rec["M"], d_str]
            for tup2 in location_df[location_df["APoE (1/n)"] == apoe].itertuples():
                row += [
                    round(tup2.PGA, 2),
                    round(tup2.Sas, 2),
                    round(tup2.Tc, 1),
                ]
        yield row


def chunks(items, chunk_size):
    iterator = iter(items)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk


if __name__ == "__main__":

    # TODO shift this into the CLI
    def sat_table():
        filename = "SaT-variables_v5_corrected-locations.pkl"
        df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename))
        return SatTable(df)

    def dm_table():
        filename = "D_and_M_with_floor.csv"
        csv_path = pathlib.Path(RESOURCES_FOLDER, "input", "v1", filename)
        return DistMagTable(csv_path)

    sat = sat_table()
    named_df = sat.named_location_df()
    grid_df = sat.grid_location_df()
    d_and_m_df = dm_table().flatten()

    report_grps = list(zip([1, 2], [named_df, grid_df]))
    report_names = ["", "named", "gridded"]

    for report_grp, location_df in report_grps:

        for apoe in APOE_MAPPINGS:

            filename = f"{report_names[report_grp]}_location_report_apoe({apoe[1]})"
            print(f"report: {filename}")

            report: Document = Document()

            table_rows = list(generate_table_rows(location_df, d_and_m_df, apoe[1]))

            ### CSV
            with open(
                pathlib.Path(RESOURCES_FOLDER, filename+".csv"), "w"
            ) as out_csv:            
                writer = csv.writer(out_csv, quoting=csv.QUOTE_NONNUMERIC)
                header = ["location", "M", "D"] 
                for sss in SOIL_CLASSES:
                    for attr in ['PGA', 'Sas', 'Tc']:
                        header.append(f'{sss}-{attr}')
                writer.writerow(header)
                for row in table_rows:
                    writer.writerow(row)
        
            ### PDF
            for idx, chunk in enumerate(chunks(table_rows, MAX_PAGE_ROWS)):
                report.add_page(
                    build_report_page(
                        f"C{report_grp}", apoe, list(chunk), table_part=idx + 1
                    )
                )

            with open(
                pathlib.Path(RESOURCES_FOLDER, filename+".pdf"), "wb"
            ) as out_file_handle:
                PDF.dumps(out_file_handle, report)
