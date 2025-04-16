"""
This module compiles the deliverable for Standards New Zealand from the reports and resources folders
"""

import csv
import zipfile
from pathlib import Path, PurePath
from typing import List

import pandas as pd

from nzssdt_2023.config import WORKING_FOLDER


def copy_files_to_deliverable(gns_files: List[Path], snz_files: List[Path]):
    """
    copy files directly to the deliverables folder

    Args:
        gns_files: list of paths in gns folder
        snz_files: list of paths in deliverables folder

    """

    for gns_file, snz_file in zip(gns_files, snz_files):

        if gns_file.suffix == ".pdf":
            snz_file.write_bytes(gns_file.read_bytes())
        else:
            snz_file.write_text(gns_file.read_text())


def copy_csv_reports_to_deliverable(
    gns_csv_files: List[Path], snz_csv_files: List[Path]
):
    """
    modify and re-encode the csv files for default Excel import then add them to the deliverables folder

    Args:
        gns_csv_files: list of csv paths in reports folder
        snz_csv_files: list of csv paths in deliverables folder

    """

    for gns_file, snz_file in zip(gns_csv_files, snz_csv_files):
        df = pd.read_csv(gns_file, keep_default_na=True)
        apoes = df["apoe"]
        df["apoe"] = [f" {apoe}" for apoe in apoes]

        # if table is for grid locations include individual lat/lon columns
        if "~" in df["location"][0]:
            latlons = list(df["location"])
            lats = [latlon.split("~")[0] for latlon in latlons]
            lons = [latlon.split("~")[1] for latlon in latlons]
            df.drop("location_ascii", axis=1, inplace=True)
            df.insert(1, "longitude", lons)
            df.insert(1, "latitude", lats)

        df.to_csv(
            snz_file,
            encoding="utf-8-sig",
            index=False,
            na_rep="n/a",
            quoting=csv.QUOTE_NONNUMERIC,
        )


def archive_zip_folder(source_path: Path, zip_path: Path):
    """
    zip the deliverables folder

    Args:
        source_path: path to source folder
        zip_path: path to zipped folder

    """

    # remove current zip folder, if it exists
    zip_path.unlink(missing_ok=True)

    # create temporary zip
    temp_path = Path(WORKING_FOLDER, PurePath(zip_path).name)
    with zipfile.ZipFile(temp_path, "w") as zip:
        for filename in Path(source_path).rglob("*"):
            zip.write(filename, arcname=str(Path(filename).relative_to(source_path)))

    temp_path.rename(zip_path)

    return zip_path


def create_deliverables_zipfile(
    snz_name_prefix: str,
    publication_year: int,
    deliverables_folder: Path,
    reports_folder: Path,
    resources_folder: Path,
    override: bool = False,
) -> Path:
    """
    identify the relevant reports and resources and includes them in a zipfile

    Args:
        snz_name_prefix: prefix for filenames
        publication_year: date suffix for filenames
        deliverables_folder: path to the deliverables folder for the version
        reports_folder: path to the reports folder for the version
        resources_folder: path to the resources folder for the version
        override: if True, rewrite all files

    Returns:
         zip_path: path to the zip file deliverable
    """

    zip_name = f"{snz_name_prefix}_files"
    zip_path = Path(deliverables_folder, zip_name + ".zip")

    # set relevant paths in gns repo
    gns_named_report_pdf = Path(reports_folder, "named_location_report.pdf")
    gns_grid_report_pdf = Path(reports_folder, "gridded_location_report.pdf")
    gns_pdf_files = [gns_grid_report_pdf, gns_named_report_pdf]

    gns_named_report_csv = Path(reports_folder, "named_location_report.csv")
    gns_grid_report_csv = Path(reports_folder, "gridded_location_report.csv")
    gns_csv_files = [gns_grid_report_csv, gns_named_report_csv]

    gns_named_json = Path(resources_folder, "named_locations_combo.json")
    gns_grid_json = Path(resources_folder, "grid_locations_combo.json")
    gns_polygons = Path(resources_folder, "urban_area_polygons.geojson")
    gns_grid_points = Path(resources_folder, "grid_points.geojson")
    gns_faults = Path(resources_folder, "major_faults.geojson")
    gns_geojsons = [gns_polygons, gns_grid_points, gns_faults]
    gns_jsons = [gns_named_json, gns_grid_json]

    # set relevant paths for snz deliverable
    snz_named_report_pdf = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-1_{publication_year}.pdf"
    )
    snz_grid_report_pdf = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-2_{publication_year}.pdf"
    )
    snz_pdf_files = [snz_grid_report_pdf, snz_named_report_pdf]

    snz_named_report_csv = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-1_{publication_year}.csv"
    )
    snz_grid_report_csv = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-2_{publication_year}.csv"
    )
    snz_csv_files = [snz_grid_report_csv, snz_named_report_csv]

    snz_named_json = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-1_{publication_year}.json"
    )
    snz_grid_json = Path(
        deliverables_folder, f"{snz_name_prefix}_Table3-2_{publication_year}.json"
    )
    snz_polygons = Path(
        deliverables_folder,
        f"{snz_name_prefix}_UrbanAreaPolygons_{publication_year}.geojson",
    )
    snz_grid_points = Path(
        deliverables_folder, f"{snz_name_prefix}_GridPoints_{publication_year}.geojson"
    )
    snz_faults = Path(
        deliverables_folder, f"{snz_name_prefix}_MajorFaults_{publication_year}.geojson"
    )
    snz_geojsons = [snz_polygons, snz_grid_points, snz_faults]
    snz_jsons = [snz_named_json, snz_grid_json]

    if (
        override
        | (not snz_named_report_pdf.exists())
        | (not snz_grid_report_pdf.exists())
        | (not snz_named_report_csv.exists())
        | (not snz_grid_report_pdf.exists())
        | (not snz_named_json.exists())
        | (not snz_grid_json.exists())
        | (not snz_polygons.exists())
        | (not snz_grid_points.exists())
        | (not snz_faults.exists())
    ):

        # create deliverables version folder
        if not deliverables_folder.is_dir():
            deliverables_folder.mkdir()

        # copy files for zip folder
        copy_files_to_deliverable(
            gns_pdf_files + gns_geojsons, snz_pdf_files + snz_geojsons
        )
        copy_csv_reports_to_deliverable(gns_csv_files, snz_csv_files)
        zip_path = archive_zip_folder(deliverables_folder, zip_path)

        # add jsons outside of the zipped folder
        copy_files_to_deliverable(gns_jsons, snz_jsons)

    return zip_path
