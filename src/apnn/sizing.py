from math import log2, sqrt
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SizingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # spatial: face size from resolution, thickness from channels (CNN / UNet)
    # units:   height from channel/unit count, thin constant thickness (FFN)
    # plate:   flat sheet, width=depth from resolution, thin height from channels (FPN)
    mode: Literal["spatial", "units", "plate"] = "spatial"

    ref_resolution: int = 224
    ref_size: float = 40.0
    min_size: float = 8.0
    max_size: float = 60.0
    ref_channels: int = 64
    ref_width: float = 2.5
    min_width: float = 1.0
    max_width: float = 8.0
    unit_thickness: float = 2.5


def _first_dim(resolution: int | tuple[int, ...]) -> int:
    if isinstance(resolution, (tuple, list)):
        return resolution[0]
    return resolution


def resolution_to_size(resolution: int | tuple[int, ...], cfg: SizingConfig) -> float:
    r = _first_dim(resolution)
    size = cfg.ref_size * (r / cfg.ref_resolution)
    return round(min(max(size, cfg.min_size), cfg.max_size), 1)


def channels_to_width(channels: int | None, cfg: SizingConfig) -> float:
    channels = cfg.ref_channels if channels is None else channels
    width = cfg.ref_width * log2(channels / cfg.ref_channels + 1)
    return round(max(cfg.min_width, min(width, cfg.max_width)), 1)


def units_to_height(channels: int | None, cfg: SizingConfig) -> float:
    # sqrt mapping keeps a readable spread between large and small layers
    channels = cfg.ref_channels if channels is None else channels
    height = cfg.ref_size / sqrt(cfg.ref_channels) * sqrt(channels)
    return round(min(max(height, cfg.min_size), cfg.max_size), 1)
