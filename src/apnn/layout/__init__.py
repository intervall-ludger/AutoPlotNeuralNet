from .base import Connection, Layout
from .encoder_decoder import EncoderDecoderLayout
from .free import FreeLayout
from .pyramid import PyramidLayout
from .sequential import FlowLayout, SequentialLayout

LAYOUTS: dict[str, type[Layout]] = {
    "sequential": SequentialLayout,
    "flow": FlowLayout,
    "encoder_decoder": EncoderDecoderLayout,
    "pyramid": PyramidLayout,
    "free": FreeLayout,
}


def register_layout(name: str, layout_cls: type[Layout]) -> None:
    """Register a custom layout so configs can use ``layout: <name>``."""
    if not (isinstance(layout_cls, type) and issubclass(layout_cls, Layout)):
        raise TypeError(f"register_layout expects a Layout subclass, got {layout_cls!r}.")
    LAYOUTS[name] = layout_cls
