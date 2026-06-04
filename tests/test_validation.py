import pytest
from apnn import Conv, Diagram, Input
from apnn.config import DiagramConfig
from pydantic import ValidationError


def test_unknown_connection_ref_raises():
    diagram = Diagram(name="t")
    diagram.add(Input(name="a", channels=4))
    diagram.connect("a", "ghost")
    with pytest.raises(ValueError, match="unknown layer 'ghost'"):
        diagram.to_tex()


def test_unknown_section_ref_raises():
    diagram = Diagram(name="t")
    diagram.add(Input(name="a", channels=4))
    diagram.section("a", "ghost", "label")
    with pytest.raises(ValueError, match="unknown layer 'ghost'"):
        diagram.to_tex()


def test_bad_identifier_rejected():
    with pytest.raises(ValidationError):
        DiagramConfig.model_validate(
            {"name": "t", "layers": [{"type": "input", "name": "1bad"}]})


def test_label_macro_allowlist_rejects_input():
    with pytest.raises(ValidationError):
        DiagramConfig.model_validate({
            "name": "t",
            "layers": [{"type": "input", "name": "a"}],
            "connections": [{"from": "a", "to": "a", "label": r"\input{/etc/passwd}"}],
        })


def test_safe_math_label_allowed():
    cfg = DiagramConfig.model_validate({
        "name": "t",
        "layers": [{"type": "input", "name": "a"}, {"type": "fc", "name": "b", "channels": 4}],
        "connections": [{"from": "a", "to": "b", "label": r"$1\times1$"}],
    })
    assert cfg.connections[0].label == r"$1\times1$"


def test_channels_none_does_not_crash_sizing():
    # a node may omit channels (e.g. an auto-imported pool/fc); sizing must cope
    diagram = Diagram(name="t", layout="sequential")
    diagram.add(Input(name="a", channels=4), Conv(name="b", channels=None, caption="c"))
    assert "b" in diagram.to_tex()
