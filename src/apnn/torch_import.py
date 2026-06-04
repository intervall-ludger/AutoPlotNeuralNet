from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

log = logging.getLogger(__name__)


def _load_model(path: str | Path, arch: str | None):
    import torch
    import torch.nn as nn

    if arch:
        import torchvision.models as tvm
        try:
            model = tvm.get_model(arch, weights=None)
        except Exception:
            if not hasattr(tvm, arch):
                raise ValueError(f"unknown torchvision arch '{arch}'.")
            model = getattr(tvm, arch)(weights=None)
        obj = torch.load(path, map_location="cpu", weights_only=True)
        if isinstance(obj, Mapping):
            model.load_state_dict(obj)
        elif isinstance(obj, nn.Module):
            model = obj
        return model.eval()

    # no arch: a state_dict loads with weights_only; a whole module needs the
    # (less safe) full unpickle
    try:
        obj = torch.load(path, map_location="cpu", weights_only=True)
    except Exception:
        obj = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(obj, nn.Module):
        return obj.eval()
    if isinstance(obj, Mapping):
        raise ValueError(
            "this .pt holds only weights (a state_dict) — the architecture and "
            "skip connections live in the model code, not the weights. Re-run "
            "with --arch <name> (e.g. resnet50) to rebuild it via torchvision, "
            "or pass a whole saved model."
        )
    raise ValueError(f"unsupported .pt contents: {type(obj).__name__}.")


def _collect_shapes(model, example) -> dict[int, tuple[int, ...]]:
    import torch

    shapes: dict[int, tuple[int, ...]] = {}

    def hook(module, _inp, out):
        if isinstance(out, torch.Tensor):
            shapes[id(module)] = tuple(out.shape)

    handles = [m.register_forward_hook(hook) for m in model.modules()]
    try:
        with torch.no_grad():
            model(example)
    finally:
        for h in handles:
            h.remove()
    return shapes


def _chw(shape: tuple[int, ...] | None) -> tuple[int | None, int | None]:
    if not shape:
        return None, None
    channels = shape[1] if len(shape) >= 2 else None
    resolution = shape[2] if len(shape) >= 4 else None
    return channels, resolution


def _is_folded(module) -> bool:
    import torch.nn as nn
    return isinstance(module, (
        nn.ReLU, nn.ReLU6, nn.LeakyReLU, nn.GELU, nn.SiLU, nn.ELU, nn.Sigmoid,
        nn.Tanh, nn.Hardswish, nn.Hardsigmoid, nn.Dropout, nn.Dropout1d,
        nn.Dropout2d, nn.Dropout3d, nn.Identity, nn.Flatten,
        nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d, nn.LayerNorm, nn.GroupNorm,
    ))


def _repeated_block(module) -> tuple[str, int] | None:
    """A container of >=2 identical composite sub-modules -> collapse to 'xN'."""
    import torch.nn as nn
    if not isinstance(module, (nn.Sequential, nn.ModuleList)):
        return None
    kids = list(module.children())
    if len(kids) < 2:
        return None
    first = type(kids[0])
    if all(type(k) is first for k in kids) and any(kids[0].children()):
        return first.__name__, len(kids)
    return None


class _Walker:
    def __init__(self, shapes: dict[int, tuple[int, ...]]):
        self.shapes = shapes
        self.layers: list[dict] = []
        self._counts: dict[str, int] = {}

    def _name(self, kind: str) -> str:
        self._counts[kind] = self._counts.get(kind, 0) + 1
        return f"{kind}{self._counts[kind]}"

    def _add(self, type_: str, kind: str, shape, caption: str, **extra) -> None:
        channels, resolution = _chw(shape)
        layer = {"type": type_, "name": self._name(kind), "caption": caption}
        if channels is not None:
            layer["channels"] = channels
        if resolution and resolution > 1:
            layer["resolution"] = resolution
        layer.update(extra)
        self.layers.append(layer)

    def walk(self, module) -> None:
        import torch.nn as nn
        for name, child in module.named_children():
            repeated = _repeated_block(child)
            shape = self.shapes.get(id(child))
            if repeated:
                _block_type, n = repeated
                # name lives in the legend; no baseline caption -> no crowding
                self._add("block", "block", shape, f"{name} x{n}", label_pos="none")
            elif isinstance(child, (nn.Sequential, nn.ModuleList)):
                self.walk(child)
            elif _is_folded(child):
                continue
            elif isinstance(child, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
                self._add("conv", "conv", shape, "conv")
            elif isinstance(child, (nn.ConvTranspose1d, nn.ConvTranspose2d, nn.ConvTranspose3d)):
                self._add("deconv", "deconv", shape, "up-conv")
            elif isinstance(child, (nn.MaxPool1d, nn.MaxPool2d, nn.MaxPool3d,
                                    nn.AvgPool1d, nn.AvgPool2d, nn.AvgPool3d,
                                    nn.AdaptiveAvgPool1d, nn.AdaptiveAvgPool2d,
                                    nn.AdaptiveAvgPool3d, nn.AdaptiveMaxPool2d)):
                self._add("pool", "pool", shape, "pool")
            elif isinstance(child, nn.Linear):
                self._add("fc", "fc", shape, "fc")
            elif any(child.children()):
                self.walk(child)
            else:
                self._add("block", "block", shape, type(child).__name__, label_pos="none")


def _to_yaml(name: str, in_res: int, layers: list[dict]) -> str:
    def fmt(value) -> str:
        text = str(value)
        return f'"{text}"' if (" " in text or ":" in text) else text

    lines = [
        f"name: {name}",
        "layout: sequential",
        "sizing:",
        "  mode: spatial",
        f"  ref_resolution: {in_res}",
        "  ref_size: 40",
        "  ref_channels: 64",
        "layers:",
    ]
    order = ["type", "name", "channels", "resolution", "caption", "label_pos"]
    for layer in layers:
        parts = [f"{k}: {fmt(layer[k])}" for k in order if k in layer]
        lines.append("  - {" + ", ".join(parts) + "}")
    return "\n".join(lines) + "\n"


def config_from_torch(path: str | Path, input_shape: tuple[int, ...],
                      arch: str | None = None, name: str | None = None) -> str:
    """Build an apnn YAML config from a PyTorch model (.pt)."""
    import torch

    model = _load_model(path, arch)
    example = torch.randn(*input_shape)
    shapes = _collect_shapes(model, example)

    walker = _Walker(shapes)
    in_channels, in_res = _chw(input_shape)
    walker.layers.append({
        "type": "input", "name": "input", "caption": "image",
        **({"channels": in_channels} if in_channels else {}),
        **({"resolution": in_res} if in_res and in_res > 1 else {}),
    })
    walker.walk(model)

    if len(walker.layers) <= 1:
        raise ValueError("could not extract any layers from the model.")
    diagram_name = name or (arch or Path(path).stem)
    return _to_yaml(diagram_name, in_res or 224, walker.layers)
