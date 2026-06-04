from __future__ import annotations

from dataclasses import dataclass

from ..nodes import Node
from ..tikz import emit

# Box.sty renders boxes at this scale; depth projects up-right by this factor.
BOX_SCALE = 0.2
DEPTH_PROJ = 0.385


def clearing_gap(prev: Node, base_gap: float, margin: float = 0.8) -> float:
    """Horizontal gap that keeps the next box clear of prev's depth shadow."""
    shadow = prev._depth * BOX_SCALE * DEPTH_PROJ
    return round(max(base_gap, shadow + margin), 2)


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

    def compute(self, nodes: list[Node]) -> list[Connection]:
        raise NotImplementedError
