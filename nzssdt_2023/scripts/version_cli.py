"""A simple CLI to manage artefact versions of TS1170.5."""

import click

from nzssdt_2023.versioning import VersionInfo, VersionManager, ensure_resource_folder

version_manager = VersionManager()


@click.group()
def cli():
    """A CLI for managing version metadata for the resource artefacts
    of the NZ Seismic Site Demand Tables for TS1170.5
    """


@cli.command("init")
@click.argument("version_id", type=str)
@click.option("--verbose", "-V", is_flag=True, default=False)
def init(version_id, verbose):
    """Create the resource folder for a new version

    This should be used before pipeline build steps are run.
    """
    if verbose:
        click.echo(f"init resource for version_id: {version_id}")

    ensure_resource_folder(version_id)


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
    """List the available versions of NZSSDT 2023"""

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
