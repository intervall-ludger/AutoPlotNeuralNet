from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .latex import is_color, is_identifier
from .sizing import SizingConfig

# Edge labels are raw LaTeX so math works. Rather than blocklist dangerous
# commands (fragile: \write18, \expandafter, ^^-notation all slip through), we
# allowlist a fixed set of safe math/text macros and reject every other control
# sequence and the ^^ character escape.
_SAFE_LABEL_MACROS = {
    "times", "cdot", "cdots", "ldots", "dots", "div", "pm", "mp", "ast", "star",
    "circ", "bullet", "oplus", "ominus", "otimes", "oslash", "odot", "to", "gets",
    "mapsto", "rightarrow", "leftarrow", "leftrightarrow", "Rightarrow",
    "Leftarrow", "uparrow", "downarrow", "frac", "sqrt", "sum", "prod", "int",
    "partial", "nabla", "infty", "approx", "sim", "simeq", "cong", "neq", "leq",
    "geq", "ll", "gg", "equiv", "propto", "parallel", "Vert", "vert", "langle",
    "rangle", "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta",
    "eta", "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi",
    "rho", "sigma", "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi",
    "Omega", "hat", "bar", "vec", "tilde", "dot", "ddot", "mathrm", "mathbf",
    "mathbb", "mathcal", "text", "textbf", "textit", "quad", "qquad",
    ",", "!", ";", ":",  # thin-space / spacing macros
}
_LABEL_MACRO = re.compile(r"\\([a-zA-Z]+|.)")


def _check_identifier(value: str) -> str:
    if not is_identifier(value):
        raise ValueError(
            f"'{value}' is not a valid name: use letters, digits, '_' or '-' and "
            "start with a letter."
        )
    return value


def _check_color(value: str | None) -> str | None:
    if value is not None and not is_color(value):
        raise ValueError(
            f"'{value}' is not a valid color. Use an xcolor expression like "
            "'rgb:blue,5;red,2', a named color like 'red!50', or a hex code."
        )
    return value


def _check_label(value: str) -> str:
    if "^^" in value:
        raise ValueError("label may not use ^^ character notation.")
    for match in _LABEL_MACRO.finditer(value):
        macro = match.group(1)
        if macro not in _SAFE_LABEL_MACROS:
            raise ValueError(
                rf"label uses disallowed macro '\{macro}'; only math/text macros "
                "are permitted."
            )
    return value


def _check_anchor(value: str) -> str:
    if not (value.isalpha() and value.islower()):
        raise ValueError(
            f"'{value}' is not a valid anchor. Use a node anchor name like "
            "'east', 'west', 'north', 'south', 'northeast', 'nearwest'."
        )
    return value


class NodeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    channels: int | None = Field(default=None, gt=0)
    resolution: int | list[int] = 1
    caption: str = " "
    color: str | None = None
    band_color: str | None = None
    opacity: float | None = None
    height: float | None = None
    width: float | None = None
    depth: float | None = None
    col: int = 0  # column index, used by 2D layouts (pyramid)
    label_pos: Literal["on", "right", "below", "none"] = "on"  # where a block's label sits
    x: float | None = None  # explicit position for the 'free' layout (diagram units)
    y: float | None = None

    _v_name = field_validator("name")(_check_identifier)
    _v_color = field_validator("color", "band_color")(_check_color)


class SectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    label: str

    _v_refs = field_validator("from_", "to")(_check_identifier)


class ConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    style: Literal["solid", "dashed", "skip"] = "solid"
    skip_pos: float = 1.5  # arc height for skip connections
    from_anchor: str = "east"
    to_anchor: str = "west"
    label: str = ""  # author LaTeX (e.g. math), drawn above the edge

    _v_refs = field_validator("from_", "to")(_check_identifier)
    _v_anchors = field_validator("from_anchor", "to_anchor")(_check_anchor)
    _v_label = field_validator("label")(_check_label)


class DiagramConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "diagram"
    layout: str = "sequential"
    theme: str = "default"
    colors: dict[str, str] = Field(default_factory=dict)
    sizing: SizingConfig = Field(default_factory=SizingConfig)
    legend: bool = True
    # "auto" derives a scale from the rendered width; a number forces it
    font_scale: float | Literal["auto"] = "auto"
    layers: list[NodeConfig]
    connections: list[ConnectionConfig] = Field(default_factory=list)
    sections: list[SectionConfig] = Field(default_factory=list)

    @field_validator("colors")
    @classmethod
    def _v_colors(cls, value: dict[str, str]) -> dict[str, str]:
        for key, color in value.items():
            _check_color(color)
        return value


def load_config(path: str | Path) -> DiagramConfig:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must be a YAML mapping, got {type(data).__name__}.")
    return DiagramConfig.model_validate(data)
