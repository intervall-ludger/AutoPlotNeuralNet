from __future__ import annotations

from ..nodes import Node
from .base import Connection, Layout, caption_gap, clearing_gap


class SequentialLayout(Layout):
    """Single row of layers, left to right (FFN, CNN classifier)."""

    spacing: float = 2.0
    pool_spacing: float = 0.7
    # fuse narrow nodes (pooling) flush onto the preceding box, with no edge
    flush_narrow: bool = False

    def compute(self, nodes: list[Node], font_scale: float = 1.0) -> list[Connection]:
        connections: list[Connection] = []
        prev: Node | None = None
        for node in nodes:
            if prev is None:
                node._offset = "(0,0,0)"
                node._to = "(0,0,0)"
            elif self.flush_narrow and node.is_narrow:
                node._offset = "(0,0,0)"
                node._to = f"({prev.name}-east)"
            else:
                base = self.pool_spacing if node.is_narrow else self.spacing
                gap = max(clearing_gap(prev, base), caption_gap(prev, node, font_scale))
                node._offset = f"({gap},0,0)"
                node._to = f"({prev.name}-east)"
                connections.append(Connection(prev.name, node.name))
            prev = node
        return connections


class FlowLayout(SequentialLayout):
    """Sequential layout where pooling is fused flush onto its conv (FCN/VGG)."""

    flush_narrow = True
