from __future__ import annotations

from .config import DiagramConfig
from .layout import LAYOUTS, Connection, Layout
from .nodes import NODE_TYPES, Node
from .sizing import (SizingConfig, channels_to_width, resolution_to_size,
                     units_to_height)
from .theme import Theme, resolve_theme
from .tikz import document, emit

_LEGEND_GAP = 50
_LEGEND_GAP_WITH_SECTIONS = 90
_CAPTION_DROP = 1.5      # cm below the lowest box for the shared caption baseline
_BRACKET_YSHIFT = -88    # pt below the lowest box for section brackets (under captions)


class Diagram:
    def __init__(self, name: str = "diagram", layout: str | Layout = "sequential",
                 theme: Theme | None = None, sizing: SizingConfig | None = None,
                 legend: bool = True):
        self.name = name
        self.nodes: list[Node] = []
        self.sections: list[tuple[str, str, str]] = []
        self.manual_connections: list[Connection] = []
        self._theme = theme or Theme()
        self._sizing = sizing or SizingConfig()
        self.legend = legend
        if isinstance(layout, str):
            try:
                self._layout: Layout = LAYOUTS[layout]()
            except KeyError:
                raise ValueError(
                    f"Unknown layout '{layout}'. Available: {', '.join(sorted(LAYOUTS))}."
                )
        else:
            self._layout = layout

    def add(self, *nodes: Node) -> "Diagram":
        self.nodes.extend(nodes)
        return self

    def section(self, from_name: str, to_name: str, label: str) -> "Diagram":
        self.sections.append((from_name, to_name, label))
        return self

    def connect(self, from_name: str, to_name: str, style: str = "solid") -> "Diagram":
        self.manual_connections.append(Connection(from_name, to_name, style=style))
        return self

    @classmethod
    def from_config(cls, cfg: DiagramConfig) -> "Diagram":
        theme = resolve_theme(cfg.theme, cfg.colors)
        diagram = cls(name=cfg.name, layout=cfg.layout, theme=theme,
                      sizing=cfg.sizing, legend=cfg.legend)
        for layer_cfg in cfg.layers:
            try:
                node_cls = NODE_TYPES[layer_cfg.type]
            except KeyError:
                raise ValueError(
                    f"Unknown layer type '{layer_cfg.type}' (layer '{layer_cfg.name}'). "
                    f"Available: {', '.join(sorted(NODE_TYPES))}."
                )
            resolution = (tuple(layer_cfg.resolution)
                          if isinstance(layer_cfg.resolution, list) else layer_cfg.resolution)
            diagram.add(node_cls(
                name=layer_cfg.name, channels=layer_cfg.channels, resolution=resolution,
                caption=layer_cfg.caption, color=layer_cfg.color,
                band_color=layer_cfg.band_color, opacity=layer_cfg.opacity,
                height=layer_cfg.height, width=layer_cfg.width, depth=layer_cfg.depth,
                col=layer_cfg.col, label_pos=layer_cfg.label_pos,
            ))
        for section in cfg.sections:
            diagram.section(section.from_, section.to, section.label)
        for conn in cfg.connections:
            diagram.connect(conn.from_, conn.to, conn.style)
        return diagram

    def _apply_sizing(self) -> None:
        cfg = self._sizing
        for node in self.nodes:
            if cfg.mode == "units":
                height = units_to_height(node.channels, cfg)
                width = node.FIXED_WIDTH if node.FIXED_WIDTH is not None else cfg.unit_thickness
                depth = cfg.unit_thickness
            elif cfg.mode == "plate":
                # flat feature map: width=depth span the resolution, height is the
                # (thin) channel thickness
                spatial = resolution_to_size(node.resolution, cfg)
                width = depth = spatial
                height = channels_to_width(node.channels, cfg)
            else:
                height = depth = resolution_to_size(node.resolution, cfg)
                width = (node.FIXED_WIDTH if node.FIXED_WIDTH is not None
                         else channels_to_width(node.channels, cfg))
            node._height = node.height if node.height is not None else height
            node._depth = node.depth if node.depth is not None else depth
            node._width = node.width if node.width is not None else width

    def _lowest_node(self) -> str | None:
        # tallest box reaches lowest (boxes are centred on the flow line)
        if not self.nodes:
            return None
        return max(self.nodes, key=lambda n: n._height).name

    def _auto_legend(self) -> list[dict]:
        items: list[dict] = []
        seen: set[tuple] = set()
        for node in self.nodes:
            item = node.legend_item(self._theme)
            key = (item["fill"], item["label"])
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
        return items

    def to_tex(self, styles_path: str = "styles/") -> str:
        self._apply_sizing()
        auto_connections = self._layout.compute(self.nodes)

        parts = [document.to_head(styles_path), self._theme.colors_tex(), document.to_begin()]
        for node in self.nodes:
            parts.append(node.tikz(self._theme))
        for conn in auto_connections:
            parts.append(conn.tikz())
        for conn in self.manual_connections:
            parts.append(conn.tikz())

        # captions on a shared baseline below the lowest box
        baseline = self._lowest_node()
        if baseline:
            for node in self.nodes:
                if not node.SELF_LABEL and node.caption.strip():
                    parts.append(emit.to_caption(node.name, baseline, node.caption,
                                                 drop=_CAPTION_DROP))

        if self.sections:
            for from_name, to_name, label in self.sections:
                # brackets sit clearly below the captions
                parts.append(emit.to_bracket_group(from_name, to_name, label,
                                                    y_ref=baseline, yshift=_BRACKET_YSHIFT))

        if self.legend and self.nodes:
            items = self._auto_legend()
            gap = _LEGEND_GAP_WITH_SECTIONS if self.sections else _LEGEND_GAP
            parts.append(emit.to_legend(items, gap=gap))

        parts.append(document.to_end())
        return "".join(parts)
