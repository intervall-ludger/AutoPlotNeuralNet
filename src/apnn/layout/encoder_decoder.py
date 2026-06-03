from __future__ import annotations

from ..nodes import Conv, Node, Upsample
from .base import BOX_SCALE, DEPTH_PROJ, Connection, Layout, clearing_gap


def _res_key(node: Node) -> int:
    r = node.resolution
    return r[0] if isinstance(r, (tuple, list)) else r


def _north_y(node: Node) -> float:
    return node._height * BOX_SCALE / 2


def _visual_top(node: Node) -> float:
    # top-front edge plus the depth shadow projecting upward
    return _north_y(node) + node._depth * BOX_SCALE * DEPTH_PROJ


class EncoderDecoderLayout(Layout):
    """U-Net style: single row with auto skip connections per resolution level."""

    spacing: float = 2.5
    pool_spacing: float = 0.6
    skip_margin: float = 1.0   # gap between an arc and the tallest box it crosses

    def compute(self, nodes: list[Node]) -> list[Connection]:
        connections: list[Connection] = []

        first_up = next((i for i, n in enumerate(nodes) if isinstance(n, Upsample)), None)

        encoder_by_res: dict[int, tuple[int, Node]] = {}
        if first_up is not None:
            for idx, node in enumerate(nodes[:first_up]):
                if isinstance(node, Conv):
                    encoder_by_res[_res_key(node)] = (idx, node)

        # place boxes; collect skip candidates (innermost first)
        skips: list[tuple[Node, Node, float]] = []
        prev: Node | None = None
        for i, node in enumerate(nodes):
            if prev is None:
                node._offset = "(0,0,0)"
                node._to = "(0,0,0)"
            else:
                base = self.pool_spacing if node.is_narrow else self.spacing
                gap = clearing_gap(prev, base)
                node._offset = f"({gap},0,0)"
                node._to = f"({prev.name}-east)"
                connections.append(Connection(prev.name, node.name))

            if first_up is not None and i > first_up and isinstance(node, Conv):
                match = encoder_by_res.get(_res_key(node))
                if match is not None and match[1].name != node.name:
                    enc_idx, encoder = match
                    clearance = max(_visual_top(s) for s in nodes[enc_idx:i + 1])
                    skips.append((encoder, node, clearance + self.skip_margin))

            prev = node

        # innermost arc (over the bottleneck) and outermost (layer 1) set the range;
        # the arcs in between are distributed evenly between those two heights
        n = len(skips)
        for k, (encoder, decoder, clearance) in enumerate(skips):
            if n == 1:
                arc_y = clearance
            else:
                arc_y = skips[0][2] + (skips[-1][2] - skips[0][2]) * k / (n - 1)
            arc_y = max(arc_y, clearance)  # never cut through the box
            skip_pos = round(arc_y - _north_y(encoder), 2)
            connections.append(Connection(
                encoder.name, decoder.name, style="skip", skip_pos=skip_pos))

        return connections
