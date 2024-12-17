"""A simple Command Line Interface to manage the resources files."""

# import os
from pathlib import Path

import click
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.publish.convert import sat_table_json_path
from nzssdt_2023.publish.report_condensed_v2 import publish_gridded, publish_named

# from nzssdt_2023.build import build_version_one  # noqa: typing
from nzssdt_2023.versioning import VersionManager

from .create_parameter_tables_combo import create_parameter_tables

version_manager = VersionManager()


@click.group()
def cli():
    """The main CLI for the building the table components"""


@cli.command("build")
@click.argument("version_id")
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_version_artefacts(version_id, verbose, no_cache, site_limit):
    """Build the resource/v{n}/json tables from a given model version

    TODO: pass/handle the NSHM model version.
    TODO: split into component part for more convenient testing
        part 1) geojson + D&M
        part 2) retrive hazard curves from the model and build HDF5 cache
        part 3) create json combo tables
        part 4) run reports (see report below)

    Usage:
        requires env configuration

        NZSHM22_HAZARD_STORE_LOCAL_CACHE=~/.cache/toshi_hazard_store
        NZSHM22_HAZARD_STORE_REGION=ap-southeast-2
        NZSHM22_HAZARD_STORE_STAGE=PROD
        AWS_PROFILE=toshi_batch_devops
        WORKING_FOLDER=WORKING
    """
    if verbose:
        click.echo("build version: %s" % version_id)

    create_parameter_tables(
        version=version_id,
        site_limit=site_limit,
        no_cache=no_cache,
        overwrite_json=True,
    )


@cli.command("report")
@click.argument("version_id")
@click.option("--final", is_flag=True, default=False)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--json-limit", type=int, default=0)
@click.option("--report-limit", type=int, default=0)
@click.option(
    "--table",
    "-f",
    type=click.Choice(["named", "gridded"]),
    default=["named", "gridded"],
    multiple=True,
)
def build_reports(version_id, final, verbose, json_limit, report_limit, table):
    """build reports and csv from json tables"""
    if verbose:
        click.echo("report for version: %s" % version_id)
        click.echo(f"table(s): {table}")

    output_folder = Path(RESOURCES_FOLDER).parent / "reports" / f"v{version_id}"
    version_folder = Path(RESOURCES_FOLDER).parent / "resources" / f"v{version_id}"

    # data paths
    named_path = sat_table_json_path(
        version_folder, named_sites=True, site_limit=json_limit, combo=True
    )
    gridded_path = sat_table_json_path(
        version_folder, named_sites=False, site_limit=json_limit, combo=True
    )

    if "named" in table:
        named_df = pd.read_json(named_path, orient="table")
        publish_named(
            named_df,
            output_folder,
            True,  # CSV
            location_limit=report_limit,
            is_final=final,
        )

    if "gridded" in table:
        grid_df = pd.read_json(gridded_path, orient="table")
        publish_gridded(
            grid_df,
            output_folder,
            True,  # CSV
            location_limit=report_limit,
            is_final=final,
        )


if __name__ == "__main__":
    cli()  # pragma: no cover
