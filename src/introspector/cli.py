import os
import sys
from pathlib import Path
from shutil import copy

import click

from .generators.confirm import ConfirmGenerator


@click.group()
def main():
    """This utility creates and populates open311-adapter configurations"""
    pass


@main.command()
@click.option(
    "-c",
    "--config-path",
    default="configs",
    envvar="INTROSPECTOR_CONFIG_PATH",
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option("-f", "--force", type=bool, default=False, is_flag=True)
@click.argument("backend", type=click.Choice(("confirm",)))
@click.argument("council")
def new(backend: str, council: str, config_path: Path, force: bool):
    """Creates an empty configuration for a new integration"""
    templates = Path(__file__).parent.parent / "templates"
    for filename in os.listdir(templates / backend):
        src = templates / backend / filename
        dst = config_path / filename.replace("{{ council }}", council)
        if dst.exists():
            if not force:
                click.echo(click.style(f"{dst} already exists", fg="red"))
                sys.exit(1)
            else:
                dst.unlink()
        copy(src, dst)
    click.echo(f"Created new {backend} config for {council} in {config_path}")


@main.command()
@click.option(
    "-c",
    "--config-path",
    default="configs",
    envvar="INTROSPECTOR_CONFIG_PATH",
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option("-b", "--backend", default="confirm", type=click.Choice(("confirm",)))
@click.option(
    "-u",
    "--update",
    type=bool,
    default=False,
    is_flag=True,
    help="Update all values in config",
)
@click.argument("council")
def generate(council: str, config_path: Path, backend: str, update: bool):
    """Populates a configuration file with values"""
    click.echo(f"Updating {backend} config for {council} in {config_path}")
    cfg_file = config_path / f"council-{council}_{backend}.yml"
    if not cfg_file.exists():
        click.echo(click.style(f"{cfg_file} doesn't exist", fg="red"))
        sys.exit(1)
    generators = {"confirm": ConfirmGenerator}
    generator = generators[backend](cfg_file, update)
    generator.run()
