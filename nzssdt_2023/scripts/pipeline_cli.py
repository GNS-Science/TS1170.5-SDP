"""One CLI to run the sequential pipeline steps and manage versions.

Version commands:

    ls: list the published versions
    info: get metadata about a given version

Pipeline commands:

    init: step 1 - create the version folder structure
    geom: step 2 - extract the crustal fault geometry, with D & M values from CFM
    nshm-json: step 3 - get nshm hazard curves and build json artefacts, OR
    nshm: step 3a  - get the NSHM model hazard curves, store HDF5 in working folder
    json: step 3b - build json artefacts from HDF5 and store to resources
    report: step 4 - build the reports, store csv and PDF to reports folder
    publish: step 5 - create or update a version manifest


"""

# import os
from pathlib import Path

import click
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.publish.convert import sat_table_json_path
from nzssdt_2023.publish.report_condensed_v2 import publish_gridded, publish_named

# from nzssdt_2023.build import build_version_one  # noqa: typing
from nzssdt_2023.versioning import VersionInfo, VersionManager, ensure_resource_folder

from .create_parameter_tables_combo import (
    build_json_tables,
    create_parameter_tables,
    get_hazard_curves,
    get_site_list,
    hf_filepath,
)

version_manager = VersionManager()


@click.group()
def cli():
    """A CLI to run the sequential pipeline steps and manage TS1170.5 versions"""


@cli.command("init")
@click.argument("version_id", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
def init(version_id, verbose):
    """Create the target resource folder for a new version

    STEP #1 -> This should be used before pipeline build steps are run.
    """
    if verbose:
        click.echo(f"init resource for version_id: {version_id}")

    ensure_resource_folder(version_id)


@cli.command("nshm")
@click.argument("nzshm-model", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_nshm(nzshm_model, verbose, site_limit):
    """Build the HDF5 from a given model version

    STEP 3A) requires that steps 1 & 2 have been run

    Usage:
        requires env configuration

        NZSHM22_HAZARD_STORE_LOCAL_CACHE=~/.cache/toshi_hazard_store
        NZSHM22_HAZARD_STORE_REGION=ap-southeast-2
        NZSHM22_HAZARD_STORE_STAGE=PROD
        AWS_PROFILE=toshi_batch_devops
    """
    if verbose:
        click.echo(
            f"Build the HDF5 from a given model : {nzshm_model} with  {site_limit} sites"
        )

    site_list = get_site_list(site_limit)
    get_hazard_curves(site_list=site_list, site_limit=site_limit, hazard_id=nzshm_model)


@cli.command("json")
@click.argument("version_id")
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--force", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_json(version_id, verbose, force, site_limit):
    """Build the json artefacts from HDF5 and store to resources

    STEP 3B) requires that steps 1, 2 & 3A have been run

    Usage:
        requires env configuration:

        WORKING_FOLDER=WORKING
    """
    site_list = get_site_list(site_limit)
    hf_path = hf_filepath(site_limit=site_limit)
    build_json_tables(hf_path, site_list, version_id, site_limit, overwrite_json=force)


@cli.command("nshm-json")
@click.argument("version_id")
@click.argument("nzshm-model", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_version_artefacts(version_id, nzshm_model, verbose, no_cache, site_limit):
    """Build the resource/v{n}/json tables from a given model version

    STEP 3) requires step 1 & 2 to already be run

    TODO: pass/handle the NSHM model version.

    Usage:
        requires env configuration

        NZSHM22_HAZARD_STORE_LOCAL_CACHE=~/.cache/toshi_hazard_store
        NZSHM22_HAZARD_STORE_REGION=ap-southeast-2
        NZSHM22_HAZARD_STORE_STAGE=PROD
        AWS_PROFILE=toshi_batch_devops
        WORKING_FOLDER=WORKING
    """
    if verbose:
        click.echo(f"build version: {version_id} for model {nzshm_model}")

    create_parameter_tables(
        version=version_id,
        hazard_id=nzshm_model,
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
    """build reports and csv from json tables

    STEP 4) requires step 1, 2 & 3 to already be run

    """
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


@cli.command("publish")
@click.argument("version_id", type=str)
@click.argument("nzshm-model", type=str)
@click.argument("description", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--update", "-U", is_flag=True, default=False)
def publish(version_id, nzshm_model, description, verbose, update):
    """Write version info to the version list"""
    vi = VersionInfo(version_id, nzshm_model, description)
    vi.collect_manifest()
    if update:
        version_manager.update(vi)
    else:
        version_manager.add(vi)
    if verbose:
        click.echo(f"Wrote new version: {vi}")


@cli.command("ls")
@click.option("--verbose", "-V", is_flag=True, default=False)
def list_versions(verbose):
    """List the available versions"""

    if verbose:
        click.echo("version_id, nzshm_model_version")
        for vi in version_manager.read_version_list().values():
            click.echo(f"{vi.version_id}, {vi.nzshm_model_version}")
    else:
        for vi in version_manager.read_version_list().values():
            click.echo(f"{vi.version_id}")


@cli.command("info")
@click.argument("version_id", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
def version_info(version_id, verbose):
    """Get detailed info for a given version_id"""
    vi = version_manager.get(version_id)
    click.echo(str(vi))


if __name__ == "__main__":
    cli()  # pragma: no cover
