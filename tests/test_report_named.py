import pathlib

import pandas as pd
import pytest

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import SatTable, DistMagTable

#!chapter_003/src/snippet_010.py
from decimal import Decimal
from typing import Tuple

from borb.pdf import SingleColumnLayout
from borb.pdf import PageLayout
from borb.pdf import FixedColumnWidthTable
# from borb.pdf import FlexibleColumnWidthTable
from borb.pdf import TableCell
from borb.pdf import Paragraph
from borb.pdf import  HeterogeneousParagraph, ChunkOfText
from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import PDF
from borb.pdf import Alignment
from borb.pdf.page.page_size import PageSize

def build_report_doc(table_id:str = "C1", apoe: Tuple[chr, int] = ('a', 25)):

    PAGE_SIZE = PageSize.A4_LANDSCAPE
    doc: Document = Document()
    page: Page = Page(width=PAGE_SIZE.value[0], height=PAGE_SIZE.value[1])
    doc.add_page(page)
    layout: PageLayout = SingleColumnLayout(page)

    SSS = ["I", "II", "III", "IV", "V", "VI"]
    TITLE = f"TABLE {table_id}({apoe[0]}): SITE DEMAND PARAMETERS FOR AN PROBABILITY OF EXCEEDANCE OF 1 in {apoe[1]} YEARS"
    layout.add(Paragraph(TITLE, font="Helvetica", font_size=Decimal(12), horizontal_alignment=Alignment.CENTERED))

    # create a FixedColumnWidthTable
    table = FixedColumnWidthTable(
            number_of_columns=3+(6*3),
            number_of_rows=10,
            # adjust the ratios of column widths for this FixedColumnWidthTable
            column_widths=[Decimal(3), Decimal(0.5), Decimal(0.5)] + 6 * [Decimal(0.5), Decimal(0.5), Decimal(0.5)],
        )

    def add_row_0(table: FixedColumnWidthTable):
        table.add(TableCell(Paragraph(""), column_span=3))
        for sss in SSS:
            table.add(TableCell(Paragraph(f"Site Soil Class {sss}", font="Helvetica-bold", font_size=Decimal(9),
                horizontal_alignment=Alignment.CENTERED, vertical_alignment=Alignment.BOTTOM), column_span=3))
        return table

    def add_row_1(table: FixedColumnWidthTable):
        table.add(TableCell(Paragraph("Location", font="Helvetica-bold", font_size=Decimal(9))))\
            .add(TableCell(Paragraph("M", font="Helvetica-bold", font_size=Decimal(9), horizontal_alignment=Alignment.CENTERED)))\
            .add(TableCell(Paragraph("D", font="Helvetica-bold", font_size=Decimal(9), horizontal_alignment=Alignment.CENTERED)))
        for sss in SSS:
            table.add(Paragraph(f"PGA", font="Helvetica-bold", font_size=Decimal(9), horizontal_alignment=Alignment.CENTERED))\
                .add(HeterogeneousParagraph([
                    ChunkOfText(f"S", font="Helvetica-bold", font_size=Decimal(9)),
                    ChunkOfText("as", font="Helvetica-bold", font_size=Decimal(7), vertical_alignment=Alignment.BOTTOM)],
                    horizontal_alignment=Alignment.CENTERED))\
                .add(HeterogeneousParagraph([
                    ChunkOfText(f"T", font="Helvetica-bold", font_size=Decimal(9),),
                    ChunkOfText("c", font="Helvetica-bold", font_size=Decimal(7), vertical_alignment=Alignment.BOTTOM)],
                    horizontal_alignment=Alignment.CENTERED))
        return table

    table = add_row_0(table)
    table = add_row_1(table)

    table.set_padding_on_all_cells(Decimal(4), Decimal(1), Decimal(1), Decimal(1))

    layout.add(table)

    return doc


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


def table_rows(sat_table, dm_table):
    df = sat_table.named_location_df()
    print(df)
    print()
    dmt = dm_table.flatten()

    for location in df.Location.unique():
        ldf = df[df.Location==location]
        print(ldf)
        # APoE loop
        for tup in ldf.itertuples():

            # dm = dmt[(dmt.Location == loc) & (dnt['APoE (1/n)'] == tup._3)]
            rec = dmt.loc[location, tup._3]
            print('D', str(rec['D']), 'M', rec["M"])

            # if expected[0] is np.NaN:
            #     assert isinstance(rec["D"], type(np.NaN))

            print(tup.Location, tup._2, tup._3, tup.PGA, tup.Sas, tup.Tc )
            # Site Soil Class loop
            # for sss in ["I'", "II", "III", "IV", "V"]:
            for apoe in [25, 50, 100, 250, 500, 1000, 2500]:
                for tup2 in ldf[ldf['APoE (1/n)'] == apoe].itertuples():
                    print(tup2)
                    print(tup2.Location, tup2._2, tup2._3, tup2.PGA, tup2.Sas, tup2.Tc )
            # assert 0


# @pytest.mark.skip('WIP')
def test_report_sat_table(sat_table, dm_table):

    report = build_report_doc()
    with open(pathlib.Path(RESOURCES_FOLDER, "named_report.pdf"), "wb") as out_file_handle:
        PDF.dumps(out_file_handle, report)

