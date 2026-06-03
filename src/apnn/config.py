from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .latex import is_color, is_identifier
from .sizing import SizingConfig


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


class NodeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    channels: int | None = None
    resolution: int | list[int] = 1
    caption: str = " "
    color: str | None = None
    band_color: str | None = None
    opacity: float | None = None
    height: float | None = None
    width: float | None = None
    depth: float | None = None
    col: int = 0  # column index, used by 2D layouts (pyramid)
    label_pos: Literal["on", "right", "below"] = "on"  # where a block's label sits

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

    _v_refs = field_validator("from_", "to")(_check_identifier)


class DiagramConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "diagram"
    layout: str = "sequential"
    theme: str = "default"
    colors: dict[str, str] = Field(default_factory=dict)
    sizing: SizingConfig = Field(default_factory=SizingConfig)
    legend: bool = True
    font_scale: float = 1.0  # scale all fonts; bump for very wide diagrams
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
