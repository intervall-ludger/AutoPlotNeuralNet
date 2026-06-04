from pathlib import Path

import apnn
import pytest
from apnn import Diagram, load_config

TEMPLATES = sorted((Path(apnn.__file__).parent / "templates").glob("*.yaml"))


def test_templates_present():
    assert TEMPLATES, "no bundled templates found"


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.stem)
def test_template_renders_to_tex(template):
    cfg = load_config(template)
    tex = Diagram.from_config(cfg).to_tex()
    assert r"\begin{tikzpicture}" in tex
    assert r"\end{tikzpicture}" in tex
    for layer in cfg.layers:
        assert layer.name in tex, f"layer '{layer.name}' missing from output"
