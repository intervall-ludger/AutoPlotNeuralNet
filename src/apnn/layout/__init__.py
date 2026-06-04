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
