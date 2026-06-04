from __future__ import annotations

from dataclasses import dataclass

from ..nodes import Node
from ..tikz import emit

# Box.sty renders boxes at this scale; depth projects up-right by this factor.
BOX_SCALE = 0.2
DEPTH_PROJ = 0.385
# rough rendered width of one caption character at font_scale 1.0, in diagram units
_CHAR_WIDTH = 0.33


def clearing_gap(prev: Node, base_gap: float, margin: float = 0.8) -> float:
    """Horizontal gap that keeps the next box clear of prev's depth shadow."""
    shadow = prev._depth * BOX_SCALE * DEPTH_PROJ
    return round(max(base_gap, shadow + margin), 2)


def _caption_overhang(node: Node, font_scale: float) -> float:
    """How far a centred baseline caption sticks out past the box's own half-width."""
    if not node.uses_baseline_caption() or not node.caption.strip():
        return 0.0
    caption_half = len(node.caption.strip()) * _CHAR_WIDTH * font_scale / 2
    box_half = node._width * BOX_SCALE / 2
    return max(0.0, caption_half - box_half)


def caption_gap(prev: Node, node: Node, font_scale: float, margin: float = 0.4) -> float:
    """Gap so two neighbours' baseline captions clear each other."""
    return round(_caption_overhang(prev, font_scale) + _caption_overhang(node, font_scale) + margin, 2)


@dataclass
class Connection:
    from_name: str
    to_name: str
    style: str = "solid"  # solid | dashed | skip
    skip_pos: float = 1.5
    from_anchor: str = "east"
    to_anchor: str = "west"
    label: str = ""
    shift_x: float = 0.0

    def tikz(self) -> str:
        if self.style == "skip":
            return emit.to_skip(self.from_name, self.to_name, self.skip_pos)
        return emit.to_edge(self.from_name, self.from_anchor, self.to_name, self.to_anchor,
                            dashed=self.style == "dashed", label=self.label, shift_x=self.shift_x)


class Layout:
    # single-row layouts align all captions on one baseline; 2D layouts caption locally
    shared_caption_baseline: bool = True

    def compute(self, nodes: list[Node], font_scale: float = 1.0) -> list[Connection]:
        raise NotImplementedError
