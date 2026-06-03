from dataclasses import dataclass, field

from .latex import escape_text
from .theme import Theme
from .tikz import emit


@dataclass
class Node:
    name: str
    channels: int = 1
    resolution: int | tuple[int, ...] = 1
    caption: str = " "
    color: str | None = None
    band_color: str | None = None
    opacity: float | None = None

    # explicit size overrides (else derived from sizing config)
    height: float | None = None
    width: float | None = None
    depth: float | None = None
    col: int = 0  # column index for 2D layouts
    label_pos: str = "on"  # block label placement: on | right | below

    # filled in by the sizing pass
    _height: float = field(default=0.0, repr=False)
    _width: float = field(default=0.0, repr=False)
    _depth: float = field(default=0.0, repr=False)
    # filled in by the layout pass
    _offset: str = field(default="(0,0,0)", repr=False)
    _to: str = field(default="(0,0,0)", repr=False)

    DEFAULT_OPACITY = 0.7
    # None -> width is derived from channels; a value -> fixed default width
    FIXED_WIDTH = None
    # narrow nodes (pooling/upsampling) get tighter spacing from layouts
    is_narrow = False
    # True -> the node draws its own label; the shared caption baseline skips it
    SELF_LABEL = False

    def _res_label(self) -> str:
        r = self.resolution
        if isinstance(r, (tuple, list)):
            return "$" + r"\times ".join(str(x) for x in r) + "$"
        return "" if r in (0, 1) else str(r)

    def _opacity(self) -> float:
        return self.opacity if self.opacity is not None else self.DEFAULT_OPACITY

    def tikz(self, theme: Theme) -> str:
        raise NotImplementedError

    def legend_item(self, theme: Theme) -> dict:
        raise NotImplementedError


class Input(Node):
    def tikz(self, theme: Theme) -> str:
        return emit.to_box(
            name=self.name, fill=self.color or theme.input_layer,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel=self.channels, zlabel=self._res_label(),
            caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.input_layer, "label": "Input"}


class Output(Node):
    def tikz(self, theme: Theme) -> str:
        return emit.to_box(
            name=self.name, fill=self.color or theme.output_layer,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel=self.channels, zlabel=self._res_label(),
            caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.output_layer, "label": "Output"}


class FC(Node):
    def tikz(self, theme: Theme) -> str:
        half = round(self._width / 2, 2)
        return emit.to_banded_box(
            name=self.name, fill=self.color or theme.fc,
            bandfill=self.band_color or theme.fc_band,
            offset=self._offset, to=self._to,
            width=half, bandwidth=half, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel=self.channels, caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.fc, "bandfill": self.band_color or theme.fc_band,
                "banded": True, "label": "Fully Connected"}


class Softmax(Node):
    DEFAULT_OPACITY = 0.8
    FIXED_WIDTH = 1.5

    def tikz(self, theme: Theme) -> str:
        return emit.to_box(
            name=self.name, fill=self.color or theme.softmax,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel=self.channels, caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.softmax, "label": "Softmax"}


class Conv(Node):
    def tikz(self, theme: Theme) -> str:
        # two equal slabs (conv + conv/relu), like a classic conv block
        return emit.to_banded_box(
            name=self.name, fill=self.color or theme.conv,
            bandfill=self.band_color or theme.conv_band,
            offset=self._offset, to=self._to,
            width=self._width, bandwidth=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel=self.channels, zlabel=self._res_label(),
            caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.conv, "bandfill": self.band_color or theme.conv_band,
                "banded": True, "label": "Convolution"}


class ConvBlock(Conv):
    """Two stacked convolutions, drawn like Conv (banded box)."""


class Block(Node):
    """Generic labelled box for custom / 2D diagrams (e.g. FPN levels, subnets)."""

    SELF_LABEL = True

    def tikz(self, theme: Theme) -> str:
        out = emit.to_box(
            name=self.name, fill=self.color or theme.conv,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), xlabel="", caption=" ",
        )
        if self.caption.strip():
            label = escape_text(self.caption)
            if self.label_pos == "right":
                spec = r"[anchor=west, font=\fntsm] at ([xshift=4pt]" + self.name + "-east)"
            elif self.label_pos == "below":
                spec = r"[anchor=north west, font=\fntsm] at (" + self.name + "-southeast)"
            else:  # centred on the plate; all plates of a column share this x
                spec = r"[font=\fntsm] at (" + self.name + "-anchor)"
            out += r"\node" + spec + " {" + label + "};" "\n"
        return out

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.conv, "label": self.caption.strip() or "Block"}


class Pool(Node):
    DEFAULT_OPACITY = 0.5
    FIXED_WIDTH = 1.0
    is_narrow = True

    def tikz(self, theme: Theme) -> str:
        return emit.to_box(
            name=self.name, fill=self.color or theme.pool,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.pool, "label": "Pooling"}


class Upsample(Node):
    DEFAULT_OPACITY = 0.5
    FIXED_WIDTH = 1.0
    is_narrow = True

    def tikz(self, theme: Theme) -> str:
        return emit.to_box(
            name=self.name, fill=self.color or theme.upsample,
            offset=self._offset, to=self._to,
            width=self._width, height=self._height, depth=self._depth,
            opacity=self._opacity(), caption=self.caption,
        )

    def legend_item(self, theme: Theme) -> dict:
        return {"fill": self.color or theme.upsample, "label": "Upsample"}


NODE_TYPES: dict[str, type[Node]] = {
    "input": Input,
    "output": Output,
    "fc": FC,
    "softmax": Softmax,
    "conv": Conv,
    "conv_block": ConvBlock,
    "pool": Pool,
    "upsample": Upsample,
    "block": Block,
}
