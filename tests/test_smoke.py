import pytest
from apnn import Conv, Diagram, Input
from apnn.layout import LAYOUTS
from apnn.nodes import NODE_TYPES


@pytest.mark.parametrize("type_name", sorted(NODE_TYPES))
def test_node_type_renders(type_name):
    node_cls = NODE_TYPES[type_name]
    diagram = Diagram(name="t", layout="sequential")
    diagram.add(Input(name="inp", channels=8, resolution=16),
                node_cls(name="node", channels=8, resolution=16, caption="x"))
    assert "node" in diagram.to_tex()


@pytest.mark.parametrize("layout_name", sorted(LAYOUTS))
def test_layout_computes(layout_name):
    diagram = Diagram(name="t", layout=layout_name)
    diagram.add(Input(name="a", channels=8, resolution=16, x=0, y=0, col=0),
                Conv(name="b", channels=16, resolution=16, x=3, y=0, col=1))
    assert r"\begin{tikzpicture}" in diagram.to_tex()


def test_unknown_layout_raises():
    with pytest.raises(ValueError, match="Unknown layout"):
        Diagram(name="t", layout="does-not-exist")
