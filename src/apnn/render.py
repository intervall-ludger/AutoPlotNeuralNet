import logging
import re
import shutil
import subprocess
from importlib.resources import as_file, files
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import Diagram

log = logging.getLogger(__name__)

# fonts read consistently when a diagram of this width (pt) renders at scale 1.0
_FONT_REF_WIDTH = 1150.0
_FONT_SCALE_MIN = 0.7
_FONT_SCALE_MAX = 1.8


def styles_dir() -> Path:
    with as_file(files("apnn") / "styles") as path:
        return Path(path)


def _check_tool(name: str, install_hint: str) -> str:
    tool = shutil.which(name)
    if tool is None:
        raise RuntimeError(f"'{name}' not found on PATH. {install_hint}")
    return tool


def _pdf_width(pdf_path: Path) -> float | None:
    """Page width in pt via pdfinfo; None if poppler is unavailable."""
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo is None:
        log.debug("pdfinfo not found; skipping auto font scaling")
        return None
    out = subprocess.run([pdfinfo, str(pdf_path)], capture_output=True, text=True)
    m = re.search(r"Page size:\s*([\d.]+)\s*x", out.stdout)
    return float(m.group(1)) if m else None


def _compile_pdf(pdflatex: str, out_dir: Path, name: str, tex_path: Path) -> Path:
    result = subprocess.run(
        # "./" keeps a name starting with '-' from being read as an option
        [pdflatex, "-interaction=nonstopmode", "-halt-on-error", f"./{name}.tex"],
        cwd=out_dir, capture_output=True, text=True,
    )
    pdf_path = out_dir / f"{name}.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        log.error("pdflatex failed:\n%s", result.stdout[-2000:])
        raise RuntimeError(f"pdflatex failed for {tex_path} (see {out_dir / (name + '.log')})")
    return pdf_path


def render(diagram: "Diagram", out_base: str | Path, fmt: str = "pdf", dpi: int = 150) -> Path:
    out_base = Path(out_base)
    out_dir = out_base.parent if out_base.parent != Path("") else Path(".")
    name = out_base.name
    out_dir.mkdir(parents=True, exist_ok=True)

    # ship the .sty/init next to the .tex so the output folder is self-contained
    shutil.copytree(styles_dir(), out_dir / "styles", dirs_exist_ok=True)

    auto_scale = diagram.needs_auto_scale()
    tex_path = out_dir / f"{name}.tex"
    tex_path.write_text(diagram.to_tex(styles_path="styles/"))
    log.info("wrote %s", tex_path)
    if fmt == "tex":
        return tex_path

    pdflatex = _check_tool(
        "pdflatex",
        "Install a LaTeX distribution (macOS: 'brew install --cask mactex-no-gui', "
        "Ubuntu: 'sudo apt-get install texlive-latex-extra').",
    )
    pdf_path = _compile_pdf(pdflatex, out_dir, name, tex_path)

    if auto_scale:
        width = _pdf_width(pdf_path)
        if width is not None:
            scale = round(min(max(width / _FONT_REF_WIDTH, _FONT_SCALE_MIN), _FONT_SCALE_MAX), 2)
            if abs(scale - 1.0) > 0.05:  # skip recompile for negligible changes
                log.info("auto font_scale=%.2f (width %.0fpt)", scale, width)
                tex_path.write_text(diagram.to_tex(styles_path="styles/", font_scale=scale))
                pdf_path = _compile_pdf(pdflatex, out_dir, name, tex_path)

    for ext in (".aux", ".log"):
        (out_dir / f"{name}{ext}").unlink(missing_ok=True)
    log.info("wrote %s", pdf_path)
    if fmt == "pdf":
        return pdf_path

    pdftoppm = _check_tool(
        "pdftoppm",
        "Install poppler (macOS: 'brew install poppler', Ubuntu: 'sudo apt-get install poppler-utils').",
    )
    subprocess.run(
        [pdftoppm, "-png", "-r", str(dpi), "-singlefile", f"./{name}.pdf", f"./{name}"],
        cwd=out_dir, check=True, capture_output=True, text=True,
    )
    png_path = out_dir / f"{name}.png"
    log.info("wrote %s", png_path)
    return png_path
