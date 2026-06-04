# Known issues / deferred work

Findings from the M0+M1 auto-review that are intentionally deferred to the
milestone where they become relevant.

## copyconnection color is hardcoded
- The skip-edge colour lives in `styles/init.tex` (`copyconnection` style +
  `\copymidarrow`, `rgb:blue,5;red,1;green,1;black,2`). Move it into `Theme`
  (e.g. `skip_edge`) and emit a `\def\copyedgecolor{...}` so themes can recolour
  skip connections.

## Layout — caption-aware spacing
- Sequential spacing is based on box width + gap, not on the caption width.
  Narrow boxes with wide captions (e.g. a thin `Norm` block next to a `Head`)
  can overlap their baseline captions. Surfaced by the `gemma` template, worked
  around there by shortening labels. A real fix would widen the gap when the
  combined half-caption widths of two neighbours exceed their box spacing.

## No test suite yet
- The user research (OSS-maintainer persona) flagged the absence of any
  `tests/`. Snapshot tests (YAML -> .tex per bundled template) plus a smoke
  test per node type / layout would guard refactors of `emit.py` and sizing.

## No node/layout plugin registry
- `NODE_TYPES` and `LAYOUTS` are plain dicts; extending them means editing the
  source. A `register_node` / `register_layout` hook (and relaxing
  `NodeConfig`'s `extra="forbid"` to a post-registry check) would let
  downstreams add types without forking.

## Deferred hardening (only matters if apnn is ever run as a service)
- `subprocess.run` calls in `render.py` have no `timeout`; a crafted/looping
  LaTeX run could hang. Output-path args (`-o`, `export-styles` dest) are
  intentionally unrestricted (a local CLI writes where the user says, like
  `cp`); revisit if the renderer is exposed to untrusted callers.

## Minor / style (do alongside the related feature)
- `layout/base.Layout.compute` raises `NotImplementedError`; could become a
  real `abc.ABC` + `@abstractmethod` once there are multiple external layouts.
- Legend dedups by (fill, label); a custom-coloured `conv` (e.g. the blue
  self-attn block in `multibranch`) shows a second "Convolution" entry.
