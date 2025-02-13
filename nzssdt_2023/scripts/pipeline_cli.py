"""A CLI to run the sequential pipeline steps and manage versions.

Note:
  - All the time-consuming steps all accept a `site_limit` argument. This is used to run the step using
    a small chunk of the data - useful for sanity checking. Using the same value (e.g 50) and everything
    should 'just work'.
  - the pipeline_cli script can be run using `poetry run pipeline`.
Version commands:

    ls: list the published versions
    info: get metadata about a given version

Pipeline commands:

    01-initialise: setup the new version folders
    02-hazard: get NSHM hazard curves (as above, using chosen sites)
    03-tables: build sat & D_M dataframes & convert to *-combo.json for both named and
                gridded (again using chosen sites) **needs a geopandas_df (like geometry)**
    04-geometry:
       -  from CFM get major faults to geojson
       -  from nicks file and polygons into geojson form
    05-report: create reports & csv
       - NOTE here we'll usually validate with NZS/stakeholders e.g. making minor adjustments to formatting.
    06-publish: seal the new version

"""

from pathlib import Path

import click
import pandas as pd

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.publish.convert import sat_table_json_path
from nzssdt_2023.publish.report_condensed_v2 import publish_gridded, publish_named

# from nzssdt_2023.build import build_version_one  # noqa: typing
from nzssdt_2023.versioning import VersionInfo, VersionManager, ensure_resource_folders

from .pipeline_steps import (
    create_geojsons,
    create_parameter_tables,
    get_hazard_curves,
    get_site_list,
)

version_manager = VersionManager()


@click.group()
def cli():
    """A CLI to run the sequential pipeline steps and manage TS1170.5 versions"""


@cli.command("01-init")
@click.argument("version_id", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
def init(version_id, verbose):
    """Create the target resource folders for a new version

    This should be used before pipeline build steps are run.
    """
    if verbose:
        click.echo(f"init resource for version_id: {version_id}")

    ensure_resource_folders(version_id)


@cli.command("02-hazard")
@click.argument("nzshm-model", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_nshm(nzshm_model, verbose, site_limit):
    """Import the NSHM hazard curves from a given model version

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


@cli.command("03-tables")
@click.argument("version_id")
@click.argument("nzshm-model", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
@click.option("--site-limit", type=int, default=0)
def build_tables(version_id, nzshm_model, verbose, no_cache, site_limit):
    """Build the resource/v{n}/json tables from a given model version."""
    if verbose:
        click.echo(f"build version: {version_id} for model {nzshm_model}")

    create_parameter_tables(
        version=version_id,
        hazard_id=nzshm_model,
        site_limit=site_limit,
        no_cache=no_cache,
        overwrite_json=True,
    )


@cli.command("04-geometry")
@click.argument("version_id")
@click.option("--verbose", "-V", is_flag=True, default=False)
def build_geometry(version_id, verbose):
    """Build the geojson artefacts."""
    if verbose:
        click.echo("geojsons for version: %s" % version_id)

    create_geojsons(version_id, overwrite=True)


@cli.command("05-report")
@click.argument("version_id")
@click.option(
    "--final", is_flag=True, default=False, help="Final version has no DRAFT watermark"
)
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option(
    "--site-limit",
    type=int,
    default=0,
    help="For use when testing, uses input json with the same `site_limit`.",
)
@click.option(
    "--report-limit",
    type=int,
    default=0,
    help="Limit the number of locations in the report",
)
@click.option(
    "--table",
    "-f",
    type=click.Choice(["named", "gridded"]),
    default=["named", "gridded"],
    multiple=True,
    help="Choose the tables to build",
)
def build_reports(version_id, final, verbose, site_limit, report_limit, table):
    """Build PDF reports and csv files from json tables."""
    if verbose:
        click.echo("report for version: %s" % version_id)
        click.echo(f"table(s): {table}")

    output_folder = Path(RESOURCES_FOLDER).parent / "reports" / f"v{version_id}"
    version_folder = Path(RESOURCES_FOLDER).parent / "resources" / f"v{version_id}"

    # data paths
    named_path = sat_table_json_path(
        version_folder, named_sites=True, site_limit=site_limit, combo=True
    )
    gridded_path = sat_table_json_path(
        version_folder, named_sites=False, site_limit=site_limit, combo=True
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


@cli.command("06-publish")
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
    """List the available versions

    NB any unpublished versions will not be listed.
    """

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
