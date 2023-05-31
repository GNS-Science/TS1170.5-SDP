"""A simple Command Line Interface to manage the resources files."""

import os
import pathlib

import click
import nzshm_model

from .versioning import VersionInfo, standard_output_filename


@click.group()
def cli():
    """Main CLI for the NZ Seismic Site Demand Table 2023 (NZSSDT 2023)"""


@cli.command("lsv")
@click.option(
    "--resources_path",
    "-R",
    default=lambda: pathlib.Path(pathlib.Path(os.getcwd()).parent, "resources"),
)
def list_versions(resources_path):
    """List the available versions of NZSSDT 2023"""
    click.echo("Resources path: %s" % resources_path)


@cli.command("add")
@click.argument("input_path", type=click.Path(exists=True))
@click.argument("version_number", type=int)
@click.option(
    "--resources_path",
    "-R",
    default=lambda: pathlib.Path(pathlib.Path(os.getcwd()).parent, "resources"),
)
@click.option("--nzshm_model_version", "-N")
@click.option("--verbose", "-V", is_flag=True, default=False)
def append_version(
    resources_path, input_path, version_number, nzshm_model_version, verbose
):
    """Add a new published version of NZSSDT 2023"""
    if verbose:
        click.echo("Resources path: %s" % resources_path)
        click.echo("Input path: %s" % input_path)
        click.echo("Version: %s" % version_number)

    nm_ver = (
        nzshm_model.get_model_version(nzshm_model_version).version
        if nzshm_model_version
        else nzshm_model.CURRENT_VERSION
    )

    vi = VersionInfo(
        version_number=version_number,
        nzshm_model_version=nm_ver,
        input_filename=pathlib.Path(input_path).name,
        output_filename=standard_output_filename(version_number),
    )
    click.echo(vi)


if __name__ == "__main__":
    cli()  # pragma: no cover
