"""A simple CLI to manage artefact versions of TS1170.5."""

import click

from nzssdt_2023.versioning import VersionInfo, VersionManager

version_manager = VersionManager()


@click.group()
def cli():
    """A CLI for managing versions of the NZ Seismic Site Demand Tables for TS1170.5"""


@cli.command("ls")
@click.option("--verbose", "-V", is_flag=True, default=False)
def list_versions(verbose):
    """List the available versions of NZSSDT 2023"""

    if verbose:
        click.echo("version_id, nzshm_model_version")
        for vi in version_manager.read_version_list().values():
            click.echo(f"{vi.version_id}, {vi.nzshm_model_version}")
    else:
        for vi in version_manager.read_version_list().values():
            click.echo(f"{vi.version_id}")


@cli.command("init")
@click.argument("version_id", type=str)
@click.option("--nzshm_model_version", "-N", default="NSHM_v1.0.4")
@click.option("--verbose", "-V", is_flag=True, default=False)
def init(version_id, nzshm_model_version, verbose):
    """Add a new published version of NZSSDT 2023"""
    if verbose:
        click.echo(
            f"version_id: {version_id}, nzshm_model_version: {nzshm_model_version}"
        )

    vi = VersionInfo(version_id=version_id, nzshm_model_version=nzshm_model_version)
    # current_versions = version_manager.read_version_list()
    # current_versions.append(vi)
    version_manager.add(vi)
    if verbose:
        click.echo(f"Wrote our new version {vi}")


@cli.command("info")
@click.argument("version_id", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
def version_info(version_id, verbose):
    """Get detailed info for a given version_id"""
    vi = version_manager.get(version_id)
    click.echo(vi)


if __name__ == "__main__":
    cli()  # pragma: no cover
