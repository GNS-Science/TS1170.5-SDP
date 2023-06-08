import pathlib

import pandas as pd
import pytest
from borb.pdf import PDF, Document

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.convert import DistMagTable, SatTable
from nzssdt_2023.report import build_report_page, chunks, generate_table_rows


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


@pytest.mark.skip("WIP")
def test_report_sat_table(sat_table, dm_table):

    report: Document = Document()

    table_rows = generate_table_rows(sat_table, dm_table)

    apoe = ("f", 1000)
    for idx, chunk in enumerate(chunks(table_rows, apoe[1]), 30):
        report.add_page(build_report_page("C1", apoe, list(chunk), table_part=idx + 1))

    with open(
        pathlib.Path(RESOURCES_FOLDER, "named_report.pdf"), "wb"
    ) as out_file_handle:
        PDF.dumps(out_file_handle, report)
