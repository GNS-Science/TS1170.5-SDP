"""
This module create the deliverable for Standards New Zealand from the reports and resources folders
"""

from typing import List

import csv
import os
import shutil
from pathlib import Path

import pandas as pd


def copy_files_to_deliverable(gns_files: List[Path], snz_files: List[Path]):
    """
    copies the files directly to the deliverables folder

    Args:
        gns_files: list of paths in gns folder
        snz_files: list of paths in deliverables folder

    """

    for gns_file, snz_file in zip(gns_files, snz_files):
        shutil.copy(gns_file, snz_file)


def copy_csv_reports_to_deliverable(gns_csv_files: List[Path], snz_csv_files: List[Path]):
    """
    re-encodes the csv files for default Excel import and includes them in the deliverables folder

    Args:
        gns_csv_files: list of csv paths in reports folder
        snz_csv_files: list of csv paths in deliverables folder

    """

    for gns_file, snz_file in zip(gns_csv_files, snz_csv_files):
        df = pd.read_csv(gns_file, keep_default_na=True)
        apoes = df["apoe"]
        df["apoe"] = [f" {apoe}" for apoe in apoes]

        # if table is for grid locations include individual lat/lon columns
        if '~' in df['location'][0]:
            latlons = list(df['location'])
            lats = [latlon.split('~')[0] for latlon in latlons]
            lons = [latlon.split('~')[1] for latlon in latlons]
            df.drop('location_ascii', axis=1, inplace=True)
            df.insert(1, 'longitude', lons)
            df.insert(1, 'latitude', lats)


        df.to_csv(
            snz_file,
            encoding="utf-8-sig",
            index=False,
            na_rep="n/a",
            quoting=csv.QUOTE_NONNUMERIC,
        )


def zip_deliverable_files(zip_name: str, zip_path: Path):
    """

    Args:
        zip_name: base name of the zip folder
        zip_path: path to zip folder

    """

    version_folder = zip_path.parent
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # TODO: confirm whether I can stay in the version folder or have to return to the previous directory

    os.chdir(version_folder)
    shutil.make_archive(zip_name, "zip", version_folder, base_dir='./')



def create_deliverable_zipfile(
    snz_name_prefix: str,
    publication_year: int,
    ts_version: str,
    deliverables_folder: Path,
    reports_folder: Path,
    resources_folder: Path,
) -> str:
    """
    identifies the relevant reports and resources and includes them in a zipfile

    Args:
        snz_name_prefix: prefix for filenames
        publication_year: date suffix for filenames
        ts_version: relevant TS version
        deliverables_folder: path to the folder containing all versions' deliverables
        reports_folder: path to the folder containing all versions' reports
        resources_folder: path to the folder containing all versions' resources

    Returns:
         zip_path: path to the zip file deliverable
    """

    zip_name = f"{snz_name_prefix}_files"
    zip_path = Path(deliverables_folder, ts_version, zip_name + ".zip")

    # set relevant paths in gns repo
    gns_named_report_pdf = Path(reports_folder, ts_version, "named_location_report.pdf")
    gns_grid_report_pdf = Path(
        reports_folder, ts_version, "gridded_location_report.pdf"
    )
    gns_pdf_files = [gns_grid_report_pdf, gns_named_report_pdf]

    gns_named_report_csv = Path(reports_folder, ts_version, "named_location_report.csv")
    gns_grid_report_csv = Path(
        reports_folder, ts_version, "gridded_location_report.csv"
    )
    gns_csv_files = [gns_grid_report_csv, gns_named_report_csv]

    gns_named_json = Path(resources_folder, ts_version, "named_locations_combo.json")
    gns_grid_json = Path(resources_folder, ts_version, "grid_locations_combo.json")
    gns_polygons = Path(resources_folder, ts_version, "urban_area_polygons.geojson")
    gns_grid_points = Path(resources_folder, ts_version, "grid_points.geojson")
    gns_faults = Path(resources_folder, ts_version, "major_faults.geojson")
    gns_geojsons = [gns_polygons, gns_grid_points, gns_faults]
    gns_jsons = [gns_named_json, gns_grid_json]

    # set relevant paths for snz deliverable
    snz_named_report_pdf = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-1_{publication_year}.pdf",
    )
    snz_grid_report_pdf = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-2_{publication_year}.pdf",
    )
    snz_pdf_files = [snz_grid_report_pdf, snz_named_report_pdf]

    snz_named_report_csv = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-1_{publication_year}.csv",
    )
    snz_grid_report_csv = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-2_{publication_year}.csv",
    )
    snz_csv_files = [snz_grid_report_csv, snz_named_report_csv]

    snz_named_json = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-1_{publication_year}.json",
    )
    snz_grid_json = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_Table3-2_{publication_year}.json",
    )
    snz_polygons = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_UrbanAreaPolygons_{publication_year}.geojson",
    )
    snz_grid_points = Path(deliverables_folder, ts_version, f"{snz_name_prefix}_GridPoints_{publication_year}.geojson")
    snz_faults = Path(
        deliverables_folder,
        ts_version,
        f"{snz_name_prefix}_MajorFaults_{publication_year}.geojson",
    )
    snz_geojsons = [snz_polygons, snz_grid_points, snz_faults]
    snz_jsons = [snz_named_json, snz_grid_json]

    # create deliverables version folder
    version_folder = zip_path.parent
    if not os.path.exists(version_folder):
        os.makedirs(version_folder)

    # copy files for zip folder
    copy_files_to_deliverable(
        gns_pdf_files + gns_geojsons, snz_pdf_files + snz_geojsons
    )
    copy_csv_reports_to_deliverable(gns_csv_files, snz_csv_files)
    zip_deliverable_files(zip_name, zip_path)

    # add jsons outside of the zipped folder
    copy_files_to_deliverable(
        gns_jsons, snz_jsons
    )

    return str(zip_path)
