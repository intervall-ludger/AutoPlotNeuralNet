# AutoPlotNeuralNet

> **Still in progress** — the diagram design is functional but still being
> refined; expect layout and styling to keep improving.

Config-driven TikZ diagrams of neural networks. Write a small YAML file, get a
`.tex` / PDF / PNG of your architecture — no manual TikZ.

```
config (YAML)  ->  apnn  ->  .tex  ->  PDF / PNG
```

## Gallery

Every diagram below is generated from a bundled template — no manual TikZ.
Run `uv run apnn render src/apnn/templates/<name>.yaml -o out/<name> --to png`.

### FFN — feedforward / MLP
![FFN](docs/gallery/ffn.png)

### CNN classifier
![CNN](docs/gallery/cnn.png)

### AlexNet
![AlexNet](docs/gallery/alexnet.png)

### ResNet — residual skip connections
![ResNet](docs/gallery/resnet.png)

### Autoencoder — encoder / decoder
![Autoencoder](docs/gallery/autoencoder.png)

### U-Net — auto skip connections per resolution level
![U-Net](docs/gallery/unet.png)

### RetinaNet / FPN — stacked feature-map pyramid
![RetinaNet](docs/gallery/retinanet.png)

### Gemma — decoder-only transformer (block level)
![Gemma](docs/gallery/gemma.png)

### FCN-8s — fully convolutional, skip-stream fusion
![FCN-8s](docs/gallery/fcn8.png)

## Requirements

- Python managed via [`uv`](https://docs.astral.sh/uv/)
- A LaTeX distribution providing `pdflatex` (rendering to PDF)
- `pdftoppm` from poppler (rendering to PNG) — optional, only for `--to png`

## Install

```bash
uv sync
```

## Usage

```bash
# render a bundled template
uv run apnn render src/apnn/templates/ffn.yaml -o examples/ffn --to png

# scaffold your own config from a template
uv run apnn new ffn > my_net.yaml
uv run apnn render my_net.yaml --to pdf

# list templates
uv run apnn list-templates
```

`--to` accepts `tex`, `pdf` (default) or `png`. `-o/--out` is the output path
without extension. Add `-v` for debug logging.

## Config format

```yaml
name: ffn                 # also used as the output file stem
layout: sequential        # how layers are arranged (default: sequential)
theme: default            # default | nature | grayscale
colors:                   # optional per-type color overrides
  fc: "rgb:blue,5;red,2.5;white,5"
sizing:                   # optional, all fields default (see below)
  ref_resolution: 224     # resolution mapped to ref_size
  ref_size: 40            # box height/depth at ref_resolution
  min_size: 8             # smallest box height/depth
  ref_channels: 64        # channel count mapped to ref_width
  ref_width: 2.5          # box thickness at ref_channels
  min_width: 1.0
  max_width: 8.0
legend: true
font_scale: 1.0           # scale fonts so they read consistently across diagrams
                          # (wide diagrams > 1.0, narrow ones < 1.0; ~ width / 1150pt)
layers:
  - {type: input,   name: in,  channels: 784, caption: Input}
  - {type: fc,      name: h1,  channels: 256, caption: Dense}
  - {type: softmax, name: out, channels: 10,  caption: Softmax}
sections: []              # optional bracket groups: [{from, to, label}]
connections: []           # optional manual edges: [{from, to, style}]
                          #   style: solid (default) | dashed | skip
```

Available layer types: `input`, `output`, `fc`, `softmax`, `conv`, `conv_block`,
`pool`, `upsample`, `deconv` (up-convolution), `sum` (element-wise sum, drawn as
a `+` ball), `block` (a generic labelled box for custom / 2D diagrams).
Layouts:
- `sequential` — FFN / CNN classifier (single row)
- `flow` — like `sequential`, but pooling is fused flush onto its conv (FCN / VGG)
- `encoder_decoder` — UNet, with automatic skip connections per resolution level
- `pyramid` — RetinaNet / FPN; place nodes in columns via the `col` field
  (col 0 = backbone, col 1 = feature pyramid, col 2 = subnets) and levels are
  stacked by `resolution`

Skip connections accept a `skip_pos` (arc height), e.g.
`{from: pool4, to: elt1, style: skip, skip_pos: 2.5}`.

Bundled templates: `ffn`, `cnn`, `alexnet`, `resnet`, `autoencoder`, `unet`,
`retinanet`, `gemma`, `fcn8` (see `apnn list-templates`, and the gallery above).

Note: in xcolor `rgb:` color expressions, avoid the named color `orange`
(it renders incorrectly) — mix `red` + `yellow` instead.

Names (`name`, and `from`/`to` references) must be valid identifiers
(`[A-Za-z][A-Za-z0-9_-]*`); colors must be xcolor expressions, named colors or
hex codes. Captions and labels are treated as literal text (special LaTeX
characters are escaped automatically).

Each layer may override `color`, `band_color`, `opacity`, and the box geometry
(`height`, `width`, `depth`); otherwise geometry is derived from `resolution` and
`channels` via the `sizing` config.

## Python API

The CLI is a thin layer over a builder API:

```python
from apnn import Diagram, load_config, render

diagram = Diagram.from_config(load_config("my_net.yaml"))
render(diagram, "examples/ffn", fmt="png")
```

## Logging

Logging uses the standard `logging` module; pass `-v` to the CLI for `DEBUG`
output, otherwise it logs at `INFO`. When using the Python API directly, call
`logging.basicConfig()` yourself to see log output.

## Credits

Inspired by [PlotNeuralNet](https://github.com/HarisIqbal88/PlotNeuralNet).
