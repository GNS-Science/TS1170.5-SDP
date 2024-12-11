"""A simple Command Line Interface to manage the resources files."""

# import os
from pathlib import Path

import click
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.publish.convert import sat_table_json_path
from nzssdt_2023.publish.report_condensed_v2 import publish_reports

# from nzssdt_2023.build import build_version_one  # noqa: typing
from nzssdt_2023.versioning import VersionManager

from .create_parameter_tables_combo import create_parameter_tables

version_manager = VersionManager()


@click.group()
def cli():
    """Main CLI for the NZ Seismic Site Demand Table 2023 (NZSSDT 2023)"""


# @cli.command("add")
# @click.argument("version_id")
# @click.option("--nzshm_model_version", "-N", default="NSHM_v1.0.4")
# @click.option("--verbose", "-V", is_flag=True, default=False)
# def build_and_append_version(version_id, nzshm_model_version, verbose):
#     """Add a new published version of NZSSDT 2023"""
#     if verbose:
#         click.echo("nzshm_model_version: %s" % nzshm_model_version)
#         click.echo("build version: %s" % version_id)

#     # TODO: more than just v1 !!
#     if version_id == 1:
#         vi = build_version_one()

#         # update the version list
#         current_versions = version_manager.read_version_list()
#         current_versions.append(vi)
#         version_manager.write_version_list(current_versions)
#         click.echo(f"Wrote our new version {vi}")
#         return

#     click.echo("did nothing, sorry")


@cli.command("build")
@click.argument("version_id")
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_version_artefacts(version_id, verbose, no_cache, site_limit):
    """build json tables

    Notes:
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
def build_reports(version_id, final, verbose, json_limit, report_limit):
    """build reports and csv from json tables"""
    if verbose:
        click.echo("report for version: %s" % version_id)

    output_folder = Path(RESOURCES_FOLDER).parent / "reports" / f"v_{version_id}"
    version_folder = Path(RESOURCES_FOLDER).parent / "resources" / f"v_{version_id}"

    # data paths
    named_path = sat_table_json_path(
        version_folder, named_sites=True, site_limit=json_limit, combo=True
    )
    gridded_path = sat_table_json_path(
        version_folder, named_sites=False, site_limit=json_limit, combo=True
    )

    named_df = pd.read_json(named_path, orient="table")
    grid_df = pd.read_json(gridded_path, orient="table")

    publish_reports(
        named_df,
        grid_df,
        output_folder,
        True,
        location_limit=report_limit,
        is_final=final,
    )


if __name__ == "__main__":
    cli()  # pragma: no cover
