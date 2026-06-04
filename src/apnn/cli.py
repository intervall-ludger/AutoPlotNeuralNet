import logging
import shutil
import sys
from importlib.resources import as_file, files
from pathlib import Path

import click
from pydantic import ValidationError

from .builder import Diagram
from .config import load_config
from .layout import LAYOUTS
from .nodes import NODE_TYPES
from .render import render, styles_dir

log = logging.getLogger("apnn")

_CHEATSHEET = r"""% ---- apnn hand-editing cheatsheet -------------------------------------------
% Box / RightBandedBox / Ball pics expose these named anchors on <name>:
%   -west -east -north -south -anchor
%   -northeast -northwest -southeast -southwest -near -neareast -nearwest
% Forward edge:  \draw[connection] (a-east) -- node{\midarrow} (b-west);
% New 3D box:    \pic[shift={(3,0,0)}] at (a-east)
%                  {Box={name=b, fill={rgb:yellow,5;red,2.5;white,5},
%                        height=30, width=2, depth=30, caption=conv}};
% Fonts: \fntlg \fntmd \fntsm    Edge colour macro: \edgecolor
% -----------------------------------------------------------------------------
"""

_NODE_DESCRIPTIONS = {
    "input": "Input feature map / image",
    "output": "Output feature map",
    "fc": "Fully connected / dense layer (banded box)",
    "softmax": "Softmax / classification head",
    "conv": "Convolution block (banded box)",
    "conv_block": "Two stacked convolutions",
    "pool": "Pooling (thin box)",
    "upsample": "Upsampling (thin box)",
    "deconv": "Up-convolution / transposed conv",
    "sum": "Element-wise sum (+ ball)",
    "concat": "Concatenation (‖ ball)",
    "norm": "Normalization layer (thin box)",
    "block": "Generic labelled box for custom diagrams",
}


def _templates_dir() -> Path:
    with as_file(files("apnn") / "templates") as path:
        return Path(path)


def _render_config(config_path: str | Path, out_base: str | Path, fmt: str, dpi: int) -> Path:
    return render(Diagram.from_config(load_config(config_path)), out_base, fmt=fmt, dpi=dpi)


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
    out_base = out or Path(config).stem
    try:
        result = _render_config(config, out_base, fmt, dpi)
    except ValidationError as exc:
        click.echo(f"Invalid config '{config}':\n{exc}", err=True)
        sys.exit(1)
    except (ValueError, RuntimeError) as exc:
        click.echo(f"Error rendering '{config}': {exc}", err=True)
        sys.exit(1)
    click.echo(f"Generated: {result}")


@main.command("validate")
@click.argument("config", type=click.Path(exists=True, dir_okay=False))
def validate_cmd(config: str) -> None:
    """Check a YAML CONFIG without rendering (no LaTeX needed)."""
    try:
        cfg = load_config(config)
        diagram = Diagram.from_config(cfg)
        diagram.to_tex()  # exercise sizing + layout so arithmetic errors surface here
    except ValidationError as exc:
        click.echo(f"Invalid config '{config}':\n{exc}", err=True)
        sys.exit(1)
    except (ValueError, KeyError) as exc:
        click.echo(f"Error in '{config}': {exc}", err=True)
        sys.exit(1)

    types = ", ".join(sorted({layer.type for layer in cfg.layers}))
    click.echo(f"OK: '{config}' is valid.")
    click.echo(f"  layout: {cfg.layout}, theme: {cfg.theme}")
    click.echo(f"  {len(cfg.layers)} layers ({types})")
    click.echo(f"  {len(cfg.connections)} manual connections, {len(cfg.sections)} sections")


@main.command("list-templates")
def list_templates() -> None:
    """List the bundled config templates."""
    for path in sorted(_templates_dir().glob("*.yaml")):
        click.echo(path.stem)


@main.command("list-node-types")
def list_node_types() -> None:
    """List the available layer types and what they draw."""
    for name in NODE_TYPES:
        click.echo(f"{name:<12} {_NODE_DESCRIPTIONS.get(name, '')}")


@main.command("list-layouts")
def list_layouts() -> None:
    """List the available layouts."""
    for name, cls in LAYOUTS.items():
        doc = (cls.__doc__ or "").strip().splitlines()[0] if cls.__doc__ else ""
        click.echo(f"{name:<16} {doc}")


def _resolve_template(template: str) -> Path:
    if not template.replace("_", "").replace("-", "").isalnum():
        click.echo(f"Invalid template name '{template}'.", err=True)
        sys.exit(1)
    path = _templates_dir() / f"{template}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in sorted(_templates_dir().glob("*.yaml")))
        click.echo(f"Unknown template '{template}'. Available: {available}.", err=True)
        sys.exit(1)
    return path


@main.command("export-styles")
@click.argument("dest", type=click.Path(file_okay=False), default="styles")
def export_styles(dest: str) -> None:
    """Copy the TikZ style files into DEST for use in a hand-written .tex."""
    dest_path = Path(dest)
    shutil.copytree(styles_dir(), dest_path, dirs_exist_ok=True)
    click.echo(f"Wrote styles to {dest_path}/")
    click.echo("Add to your .tex preamble:")
    click.echo(r"  \usepackage{import}")
    click.echo(rf"  \subimport{{{dest_path}/}}{{init}}")


@main.command("scaffold-tex")
@click.argument("template")
@click.option("-o", "--out", default=None, help="Output path without extension.")
def scaffold_tex(template: str, out: str | None) -> None:
    """Emit a hand-editable standalone .tex (+ styles) seeded from TEMPLATE."""
    path = _resolve_template(template)
    try:
        diagram = Diagram.from_config(load_config(path))
    except (ValidationError, ValueError) as exc:
        click.echo(f"Error in template '{template}': {exc}", err=True)
        sys.exit(1)
    tex_path = render(diagram, out or f"{template}_scaffold", fmt="tex")
    text = tex_path.read_text().replace(
        r"\begin{tikzpicture}", r"\begin{tikzpicture}" + "\n" + _CHEATSHEET, 1)
    tex_path.write_text(text)
    click.echo(f"Wrote {tex_path} (edit it, then: pdflatex {tex_path.name})")


@main.command()
@click.argument("template")
def new(template: str) -> None:
    """Print a bundled TEMPLATE config to stdout."""
    click.echo(_resolve_template(template).read_text())


@main.command("from-torch")
@click.argument("model", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--out", default=None, help="Output YAML path (default: <model>.yaml).")
@click.option("--input", "input_shape", default="1,3,224,224", show_default=True,
              help="Example input shape, comma-separated.")
@click.option("--arch", default=None,
              help="torchvision arch (e.g. resnet50) to rebuild a weights-only .pt.")
@click.option("--name", default=None, help="Diagram name (default: arch or file stem).")
@click.option("--to", "fmt", type=click.Choice(["tex", "pdf", "png"]), default=None,
              help="Also render the generated config in one step.")
@click.option("--dpi", type=click.IntRange(72, 600), default=150, show_default=True,
              help="PNG resolution when --to png.")
@click.option("--unsafe-load", is_flag=True,
              help="Allow full pickle deserialization of a whole saved model (only for trusted files).")
def from_torch(model: str, out: str | None, input_shape: str, arch: str | None,
               name: str | None, fmt: str | None, dpi: int, unsafe_load: bool) -> None:
    """Build a config from a PyTorch MODEL (.pt). Needs the 'torch' extra."""
    try:
        shape = tuple(int(d) for d in input_shape.split(","))
    except ValueError:
        click.echo(f"Invalid --input '{input_shape}'; use e.g. 1,3,224,224.", err=True)
        sys.exit(1)
    try:
        from .torch_import import config_from_torch
        yaml_text = config_from_torch(model, shape, arch=arch, name=name,
                                      unsafe_load=unsafe_load)
    except ImportError as exc:
        click.echo(
            f"PyTorch/torchvision required ({exc}). Install with: "
            "pip install 'autoplotneuralnet[torch] @ git+https://github.com/"
            "intervall-ludger/AutoPlotNeuralNet.git' (or: pip install torch torchvision).",
            err=True)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        click.echo(f"Could not import '{model}': {exc}", err=True)
        sys.exit(1)

    out_path = Path(out) if out else Path(model).with_suffix(".yaml")
    out_path.write_text(yaml_text)
    click.echo(f"Wrote {out_path}")
    if fmt is None:
        click.echo(f"Now render it:  apnn render {out_path} --to png")
        return
    try:
        result = _render_config(out_path, out_path.with_suffix(""), fmt, dpi)
    except (ValidationError, ValueError, RuntimeError) as exc:
        click.echo(f"Wrote config but rendering failed: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Generated: {result}")


if __name__ == "__main__":
    main()
