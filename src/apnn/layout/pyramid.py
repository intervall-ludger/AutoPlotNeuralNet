from __future__ import annotations

from ..nodes import Node
from .base import BOX_SCALE, Connection, Layout


def _res_key(node: Node) -> int:
    r = node.resolution
    return r[0] if isinstance(r, (tuple, list)) else r


class PyramidLayout(Layout):
    """FPN / RetinaNet: stacks of flat feature-map plates, one per column.

    Column convention: col 0 = backbone, col 1 = feature pyramid, col 2 = subnets.
    Plates are centred on their column and stacked by resolution (largest at the
    bottom), forming a pyramid; the bottom-up arrows run straight up the centre.
    Levels align across columns so lateral connections run horizontally.
    """

    col_spacing: float = 7.0
    level_step: float = 1.5   # vertical gap between stacked plates

    def compute(self, nodes: list[Node]) -> list[Connection]:
        levels = sorted({_res_key(n) for n in nodes}, reverse=True)  # largest = bottom
        y_of = {r: i * self.level_step for i, r in enumerate(levels)}

        for node in nodes:
            x = node.col * self.col_spacing - node._width * BOX_SCALE / 2  # centre on column
            node._offset = f"({x:.2f},{y_of[_res_key(node)]:.2f},0)"
            node._to = "(0,0,0)"

        columns: dict[int, list[Node]] = {}
        for node in nodes:
            columns.setdefault(node.col, []).append(node)

        def by_level(items: list[Node]) -> list[Node]:
            return sorted(items, key=lambda n: y_of[_res_key(n)])

        connections: list[Connection] = []
        backbone = by_level(columns.get(0, []))
        pyramid = by_level(columns.get(1, []))
        backbone_by_res = {_res_key(n): n for n in backbone}
        subnet_by_res = {_res_key(n): n for n in columns.get(2, [])}

        # bottom-up arrows straight up the centre of each pyramid
        for stack in (backbone, pyramid):
            for lower, upper in zip(stack, stack[1:]):
                connections.append(Connection(lower.name, upper.name,
                                              from_anchor="north", to_anchor="south"))
        # lateral backbone -> pyramid (same resolution)
        for node in pyramid:
            src = backbone_by_res.get(_res_key(node))
            if src is not None:
                connections.append(Connection(src.name, node.name, label=r"$1\!\times\!1$"))
        # pyramid -> subnet (same resolution)
        for node in pyramid:
            sub = subnet_by_res.get(_res_key(node))
            if sub is not None:
                connections.append(Connection(node.name, sub.name))

        return connections
