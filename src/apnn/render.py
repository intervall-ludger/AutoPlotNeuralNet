import logging
import shutil
import subprocess
from importlib.resources import as_file, files
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import Diagram

log = logging.getLogger(__name__)


def styles_dir() -> Path:
    with as_file(files("apnn") / "styles") as path:
        return Path(path)


def _check_tool(name: str, install_hint: str) -> str:
    tool = shutil.which(name)
    if tool is None:
        raise RuntimeError(f"'{name}' not found on PATH. {install_hint}")
    return tool


def render(diagram: "Diagram", out_base: str | Path, fmt: str = "pdf", dpi: int = 150) -> Path:
    out_base = Path(out_base)
    out_dir = out_base.parent if out_base.parent != Path("") else Path(".")
    name = out_base.name
    out_dir.mkdir(parents=True, exist_ok=True)

    # ship the .sty/init next to the .tex so the output folder is self-contained
    styles_dst = out_dir / "styles"
    shutil.copytree(styles_dir(), styles_dst, dirs_exist_ok=True)

    tex = diagram.to_tex(styles_path="styles/")
    tex_path = out_dir / f"{name}.tex"
    tex_path.write_text(tex)
    log.info("wrote %s", tex_path)
    if fmt == "tex":
        return tex_path

    pdflatex = _check_tool(
        "pdflatex",
        "Install a LaTeX distribution (macOS: 'brew install --cask mactex-no-gui', "
        "Ubuntu: 'sudo apt-get install texlive-latex-extra').",
    )
    result = subprocess.run(
        [pdflatex, "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
        cwd=out_dir, capture_output=True, text=True,
    )
    pdf_path = out_dir / f"{name}.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        log.error("pdflatex failed:\n%s", result.stdout[-2000:])
        raise RuntimeError(f"pdflatex failed for {tex_path} (see {out_dir / (name + '.log')})")
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
        [pdftoppm, "-png", "-r", str(dpi), "-singlefile", f"{name}.pdf", name],
        cwd=out_dir, check=True, capture_output=True, text=True,
    )
    png_path = out_dir / f"{name}.png"
    log.info("wrote %s", png_path)
    return png_path
