from __future__ import annotations

from ..nodes import Node
from .base import Connection, Layout, clearing_gap


class SequentialLayout(Layout):
    """Single row of layers, left to right (FFN, CNN classifier)."""

    spacing: float = 2.0
    pool_spacing: float = 0.7

    def compute(self, nodes: list[Node]) -> list[Connection]:
        connections: list[Connection] = []
        prev: Node | None = None
        for node in nodes:
            if prev is None:
                node._offset = "(0,0,0)"
                node._to = "(0,0,0)"
            else:
                base = self.pool_spacing if node.is_narrow else self.spacing
                gap = clearing_gap(prev, base)
                node._offset = f"({gap},0,0)"
                node._to = f"({prev.name}-east)"
                connections.append(Connection(prev.name, node.name))
            prev = node
        return connections
