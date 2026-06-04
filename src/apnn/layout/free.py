from __future__ import annotations

from ..nodes import Node
from .base import Connection, Layout


class FreeLayout(Layout):
    """Explicit placement: each node sits at its own (x, y); edges are manual."""

    shared_caption_baseline: bool = False

    def compute(self, nodes: list[Node], font_scale: float = 1.0) -> list[Connection]:
        for node in nodes:
            x = node.x if node.x is not None else 0.0
            y = node.y if node.y is not None else 0.0
            node._offset = "(0,0,0)"  # no relative shift; absolute position via _to
            node._to = f"({x},{y},0)"
        return []
