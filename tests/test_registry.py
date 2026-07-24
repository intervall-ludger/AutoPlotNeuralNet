import pytest
from apnn import Conv, DiagramConfig, Diagram, register_layout, register_node
from apnn.layout import LAYOUTS
from apnn.layout.sequential import SequentialLayout
from apnn.nodes import NODE_TYPES


def test_register_node_and_use():
    class Widget(Conv):  # reuse Conv's drawing, just a new registered name
        pass

    register_node("widget", Widget)
    try:
        cfg = DiagramConfig.model_validate({
            "name": "t",
            "layers": [
                {"type": "input", "name": "a", "channels": 4},
                {"type": "widget", "name": "w", "channels": 8, "caption": "w"},
            ],
        })
        assert "w" in Diagram.from_config(cfg).to_tex()
    finally:
        NODE_TYPES.pop("widget", None)


def test_register_node_rejects_non_node():
    with pytest.raises(TypeError):
        register_node("bad", str)


def test_register_layout_and_use():
    class Tight(SequentialLayout):
        spacing = 0.5

    register_layout("tight", Tight)
    try:
        cfg = DiagramConfig.model_validate({
            "name": "t",
            "layout": "tight",
            "layers": [
                {"type": "input", "name": "a", "channels": 4},
                {"type": "fc", "name": "b", "channels": 4},
            ],
        })
        assert r"\begin{tikzpicture}" in Diagram.from_config(cfg).to_tex()
    finally:
        LAYOUTS.pop("tight", None)


def test_register_layout_rejects_non_layout():
    with pytest.raises(TypeError):
        register_layout("bad", dict)
