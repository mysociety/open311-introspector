import os
import sys
from pathlib import Path
from shutil import copy

import click


@click.group()
def main():
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
@click.argument("backend", type=click.Choice(("confirm",)))
@click.argument("council")
def new(backend, council, config_path: Path):
    click.echo(f"Creating new {backend} config for {council} in {config_path}")
    templates = Path(__file__).parent.parent / "templates"
    for filename in os.listdir(templates / backend):
        src = templates / backend / filename
        dst = config_path / filename.replace("{{ council }}", council)
        if dst.exists():
            click.echo(click.style(f"{dst} already exists", fg="red"))
            sys.exit(1)
        copy(src, dst)


@main.command()
def generate():
    click.echo("Updating config")
