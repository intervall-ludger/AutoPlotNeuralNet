import logging
import sys
from importlib.resources import as_file, files
from pathlib import Path

import click
from pydantic import ValidationError

from .builder import Diagram
from .config import load_config
from .render import render

log = logging.getLogger("apnn")


def _templates_dir() -> Path:
    with as_file(files("apnn") / "templates") as path:
        return Path(path)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def main(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


@main.command("render")
@click.argument("config", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--out", default=None, help="Output path without extension (default: config stem).")
@click.option("--to", "fmt", type=click.Choice(["tex", "pdf", "png"]), default="pdf",
              help="Output format.")
@click.option("--dpi", type=click.IntRange(72, 600), default=150, show_default=True,
              help="PNG resolution.")
def render_cmd(config: str, out: str | None, fmt: str, dpi: int) -> None:
    """Render a YAML CONFIG into a TikZ diagram."""
    try:
        cfg = load_config(config)
        diagram = Diagram.from_config(cfg)
    except ValidationError as exc:
        click.echo(f"Invalid config '{config}':\n{exc}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"Error in '{config}': {exc}", err=True)
        sys.exit(1)

    out_base = out or Path(config).stem
    try:
        result = render(diagram, out_base, fmt=fmt, dpi=dpi)
    except RuntimeError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(f"Generated: {result}")


@main.command("list-templates")
def list_templates() -> None:
    """List the bundled config templates."""
    for path in sorted(_templates_dir().glob("*.yaml")):
        click.echo(path.stem)


@main.command()
@click.argument("template")
def new(template: str) -> None:
    """Print a bundled TEMPLATE config to stdout."""
    if not template.replace("_", "").replace("-", "").isalnum():
        click.echo(f"Invalid template name '{template}'.", err=True)
        sys.exit(1)
    path = _templates_dir() / f"{template}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in sorted(_templates_dir().glob("*.yaml")))
        click.echo(f"Unknown template '{template}'. Available: {available}.", err=True)
        sys.exit(1)
    click.echo(path.read_text())


if __name__ == "__main__":
    main()
