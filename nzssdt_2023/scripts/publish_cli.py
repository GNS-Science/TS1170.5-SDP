"""A simple Command Line Interface to manage the resources files."""

import os
from pathlib import Path

import click

from nzssdt_2023.build import build_version_one
from nzssdt_2023.versioning import read_version_list, write_version_list


@click.group()
def cli():
    """Main CLI for the NZ Seismic Site Demand Table 2023 (NZSSDT 2023)"""


@cli.command("lsv")
@click.option("--verbose", "-V", is_flag=True, default=False)
@click.option(
    "--resources_path",
    "-R",
    default=lambda: Path(Path(os.getcwd()).parent, "resources"),
)
def list_versions(resources_path, verbose):
    """List the available versions of NZSSDT 2023"""
    if verbose:
        click.echo("Resources path: %s" % resources_path)

    for version_info in read_version_list():
        click.echo(version_info)


@cli.command("add")
@click.argument("version_number", type=int)
@click.option("--nzshm_model_version", "-N", default="NSHM_v1.0.4")
@click.option("--verbose", "-V", is_flag=True, default=False)
def build_and_append_version(version_number, nzshm_model_version, verbose):
    """Add a new published version of NZSSDT 2023"""
    if verbose:
        click.echo("nzshm_model_version: %s" % nzshm_model_version)
        click.echo("build version: %s" % version_number)

    if version_number == 1:
        vi = build_version_one()

        # update the version list
        current_versions = read_version_list()
        current_versions.append(vi)
        write_version_list(current_versions)
        click.echo(f"Wrote our new version {vi}")
        return

    click.echo("did nothing, sorry")


if __name__ == "__main__":
    cli()  # pragma: no cover
