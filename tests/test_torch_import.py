import pytest
from apnn.torch_import import _chw, _skeleton_from_state_dict


def test_chw_square():
    assert _chw((1, 3, 224, 224)) == (3, 224)


def test_chw_nonsquare_uses_smaller_side():
    assert _chw((1, 3, 224, 112)) == (3, 112)


def test_chw_tabular_has_no_resolution():
    assert _chw((1, 12)) == (12, None)


class _FakeTensor:
    def __init__(self, *shape):
        self.shape = shape

    def dim(self):
        return len(self.shape)


def test_skeleton_skips_bias_and_norm():
    state_dict = {
        "net.0.weight": _FakeTensor(10, 12),   # Linear
        "net.0.bias": _FakeTensor(10),          # bias -> skip
        "net.2.weight": _FakeTensor(10, 10),    # Linear
        "net.4.weight": _FakeTensor(2, 10),     # Linear
        "bn.weight": _FakeTensor(10),           # 1D norm scale -> skip
        "conv.weight": _FakeTensor(16, 3, 3, 3),  # Conv
    }
    layers = _skeleton_from_state_dict(state_dict)
    assert [l["type"] for l in layers] == ["fc", "fc", "fc", "conv"]
    assert [l["channels"] for l in layers] == [10, 10, 2, 16]


def test_config_from_torch_whole_model_needs_unsafe(tmp_path):
    torch = pytest.importorskip("torch")
    import torch.nn as nn
    from apnn.torch_import import config_from_torch

    model = nn.Sequential(
        nn.Conv2d(3, 8, 3, padding=1), nn.ReLU(),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, 2),
    )
    path = tmp_path / "model.pt"
    torch.save(model, path)

    with pytest.raises(ValueError, match="unsafe-load"):
        config_from_torch(path, (1, 3, 16, 16))

    yaml_text = config_from_torch(path, (1, 3, 16, 16), unsafe_load=True)
    assert "type: conv" in yaml_text
    assert "type: fc" in yaml_text
