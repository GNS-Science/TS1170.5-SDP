"""A simple Command Line Interface to manage artefact versions of TS1170.5."""

import os
from pathlib import Path

import click

from nzssdt_2023.versioning import VersionInfo, VersionManager

version_manager = VersionManager()


@click.group()
def cli():
    """CLI for managing versions of the NZ Seismic Site Demand Tables for TS1170.5"""


@cli.command("ls")
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

    for version_info in version_manager.read_version_list():
        click.echo(version_info)


@cli.command("init")
@click.argument("version_id", type=str)
@click.option("--nzshm_model_version", "-N", default="NSHM_v1.0.4")
@click.option("--verbose", "-V", is_flag=True, default=False)
def build_and_append_version(version_id, nzshm_model_version, verbose):
    """Add a new published version of NZSSDT 2023"""
    if verbose:
        click.echo(
            f"version_id: {version_id}, nzshm_model_version: {nzshm_model_version}"
        )

    vi = VersionInfo(version_id=version_id, nzshm_model_version=nzshm_model_version)
    current_versions = version_manager.read_version_list()
    current_versions.append(vi)
    version_manager.write_version_list(current_versions)
    if verbose:
        click.echo(f"Wrote our new version {vi}")


if __name__ == "__main__":
    cli()  # pragma: no cover
