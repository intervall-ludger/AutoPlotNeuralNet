from .base import Connection, Layout
from .encoder_decoder import EncoderDecoderLayout
from .pyramid import PyramidLayout
from .sequential import SequentialLayout

LAYOUTS: dict[str, type[Layout]] = {
    "sequential": SequentialLayout,
    "encoder_decoder": EncoderDecoderLayout,
    "pyramid": PyramidLayout,
}
