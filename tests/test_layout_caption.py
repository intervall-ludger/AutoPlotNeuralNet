from apnn import Conv, Diagram, Input
from apnn.layout.base import caption_gap


def _conv(caption: str, width: float = 2.0) -> Conv:
    node = Conv(name="n", channels=8, caption=caption)
    node._width = width  # the sizing pass normally fills this
    return node


def test_long_caption_widens_gap():
    short = _conv("c")
    long = _conv("a very long caption indeed")
    assert caption_gap(long, long, 1.0) > caption_gap(short, short, 1.0)


def test_font_scale_increases_gap():
    node = _conv("layer caption")
    assert caption_gap(node, node, 2.0) > caption_gap(node, node, 1.0)


def _second_node_gap(caption: str) -> float:
    diagram = Diagram(name="t", layout="sequential")
    diagram.add(Input(name="a", channels=8, resolution=16),
                Conv(name="b", channels=8, resolution=16, caption=caption))
    diagram.to_tex()
    return float(diagram.nodes[1]._offset.strip("()").split(",")[0])


def test_sequential_pushes_apart_for_long_caption():
    assert _second_node_gap("x" * 30) > _second_node_gap("x")


def test_legend_dedups_by_label():
    diagram = Diagram(name="t", layout="sequential")
    diagram.add(Conv(name="a", channels=8),
                Conv(name="b", channels=8, color="rgb:blue,5;white,5"))
    labels = [item["label"] for item in diagram._auto_legend()]
    assert labels.count("Convolution") == 1
