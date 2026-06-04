from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

log = logging.getLogger(__name__)


def _load_pt(path: str | Path, arch: str | None, unsafe_load: bool = False):
    """Return (module, state_dict): exactly one is non-None.

    A module enables the shape-accurate forward-pass walk; a bare state_dict
    (no --arch) only carries weight shapes, so it yields a linear skeleton.
    """
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
        try:
            obj = torch.load(path, map_location="cpu", weights_only=not unsafe_load)
        except Exception as exc:
            raise ValueError(
                f"'{path}' could not be loaded as weights for --arch {arch} ({exc}). "
                "If it is a whole saved model, drop --arch and pass --unsafe-load."
            )
        if isinstance(obj, Mapping):
            model.load_state_dict(obj)
        elif isinstance(obj, nn.Module):
            model = obj
        return model.eval(), None

    # weights_only=True is the safe path: a state_dict loads fine. A whole saved
    # module fails it (full unpickle = arbitrary code), so that needs explicit
    # opt-in rather than a silent fallback.
    try:
        obj = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        if not unsafe_load:
            raise ValueError(
                f"'{path}' is not a plain state_dict ({exc}). If it is a whole "
                "saved model (torch.save(model, ...)), pass --unsafe-load to "
                "allow full deserialization (only for files you trust); if it "
                "holds only weights, pass --arch <name>."
            )
        obj = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(obj, nn.Module):
        return obj.eval(), None
    if isinstance(obj, Mapping):
        return None, obj
    raise ValueError(f"unsupported .pt contents: {type(obj).__name__}.")


def _first_tensor(out):
    """First tensor in a module output (LSTM/attention/HF heads return tuples)."""
    import torch
    if isinstance(out, torch.Tensor):
        return out
    if isinstance(out, (tuple, list)):
        for item in out:
            found = _first_tensor(item)
            if found is not None:
                return found
    return None


def _collect_shapes(model, example) -> dict[int, tuple[int, ...]]:
    import torch

    shapes: dict[int, tuple[int, ...]] = {}

    def hook(module, _inp, out):
        tensor = _first_tensor(out)
        if tensor is not None:
            shapes[id(module)] = tuple(tensor.shape)

    handles = [m.register_forward_hook(hook) for m in model.modules()]
    try:
        with torch.no_grad():
            model(example)
    except (TypeError, RuntimeError) as exc:
        raise ValueError(
            f"the example forward pass failed ({exc}). Check --input matches "
            "the model's expected shape; models needing multiple inputs are "
            "not supported yet."
        )
    finally:
        for h in handles:
            h.remove()
    return shapes


def _chw(shape: tuple[int, ...] | None) -> tuple[int | None, int | None]:
    if not shape:
        return None, None
    channels = shape[1] if len(shape) >= 2 else None
    # smaller spatial side bounds the feature map (non-square inputs)
    resolution = min(shape[2], shape[3]) if len(shape) >= 4 else None
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

    def _next_name(self, kind: str) -> str:
        self._counts[kind] = self._counts.get(kind, 0) + 1
        return f"{kind}{self._counts[kind]}"

    def _add(self, type_: str, kind: str, shape, caption: str, **extra) -> None:
        channels, resolution = _chw(shape)
        layer = {"type": type_, "name": self._next_name(kind), "caption": caption}
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


def _skeleton_from_state_dict(state_dict) -> list[dict]:
    """A linear conv/fc skeleton inferred from weight tensor ranks (no shapes)."""
    layers: list[dict] = []
    counts: dict[str, int] = {}

    def next_name(kind: str) -> str:
        counts[kind] = counts.get(kind, 0) + 1
        return f"{kind}{counts[kind]}"

    for key, tensor in state_dict.items():
        if not key.endswith(".weight"):
            continue
        ndim = tensor.dim()
        if ndim == 2:  # Linear: (out, in)
            layers.append({"type": "fc", "name": next_name("fc"),
                           "channels": int(tensor.shape[0]), "caption": "fc"})
        elif ndim >= 3:  # Conv: (out, in, *kernel)
            layers.append({"type": "conv", "name": next_name("conv"),
                           "channels": int(tensor.shape[0]), "caption": "conv"})
        # 1D weights are norm/bn scales -> folded out
    return layers


def _to_yaml(name: str, layers: list[dict], sizing: dict) -> str:
    def fmt(value) -> str:
        text = str(value)
        return f'"{text}"' if (" " in text or ":" in text) else text

    lines = [f"name: {name}", "layout: sequential", "sizing:"]
    lines += [f"  {key}: {value}" for key, value in sizing.items()]
    lines.append("layers:")
    order = ["type", "name", "channels", "resolution", "caption", "label_pos"]
    for layer in layers:
        parts = [f"{k}: {fmt(layer[k])}" for k in order if k in layer]
        lines.append("  - {" + ", ".join(parts) + "}")
    return "\n".join(lines) + "\n"


def config_from_torch(path: str | Path, input_shape: tuple[int, ...],
                      arch: str | None = None, name: str | None = None,
                      unsafe_load: bool = False) -> str:
    """Build an apnn YAML config from a PyTorch model (.pt)."""
    import torch

    module, state_dict = _load_pt(path, arch, unsafe_load=unsafe_load)
    diagram_name = name or (arch or Path(path).stem)
    in_channels, in_res = _chw(input_shape)

    if module is None:  # bare state_dict, no --arch -> linear skeleton
        log.info("'%s' holds only weights; building a linear skeleton from weight "
                 "shapes (pass --arch <name> for a torchvision model to get a "
                 "shape-accurate diagram).", path)
        layers = _skeleton_from_state_dict(state_dict)
        if not layers:
            raise ValueError("no Linear/Conv weights found to build a skeleton.")
        layers.insert(0, {"type": "input", "name": "input", "caption": "input",
                          **({"channels": in_channels} if in_channels else {})})
        sizing = {"mode": "units", "ref_channels": 64, "ref_size": 28, "min_size": 10}
        return _to_yaml(diagram_name, layers, sizing)

    is_spatial = len(input_shape) >= 4  # NCHW(D) -> spatial; sequences/tabular -> units
    example = torch.randn(*input_shape)
    shapes = _collect_shapes(module, example)

    walker = _Walker(shapes)
    walker.layers.append({
        "type": "input", "name": "input", "caption": "image" if is_spatial else "input",
        **({"channels": in_channels} if in_channels else {}),
        **({"resolution": in_res} if in_res and in_res > 1 else {}),
    })
    walker.walk(module)

    if len(walker.layers) <= 1:
        raise ValueError("could not extract any layers from the model.")
    if is_spatial:
        sizing = {"mode": "spatial", "ref_resolution": in_res or 224,
                  "ref_size": 40, "ref_channels": 64}
    else:
        sizing = {"mode": "units", "ref_channels": 64, "ref_size": 28, "min_size": 10}
    return _to_yaml(diagram_name, walker.layers, sizing)
