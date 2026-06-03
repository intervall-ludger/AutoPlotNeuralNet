# Known issues / deferred work

Findings from the M0+M1 auto-review that are intentionally deferred to the
milestone where they become relevant.

## Deferred to M3 (UNet / skip connections)
- **copyconnection color is hardcoded** in `tikz/document.to_begin()`
  (`rgb:blue,5;red,1;green,1;black,2`). Move it into `Theme` (e.g.
  `skip_edge`) and emit a `\def\copyedgecolor{...}` once skip connections are
  actually used by the encoder/decoder layout.

## Layout — caption-aware spacing
- Sequential spacing is based on box width + gap, not on the caption width.
  Narrow boxes with wide captions (e.g. a thin `Norm` block next to a `Head`)
  can overlap their baseline captions. Surfaced by the `gemma` template, worked
  around there by shortening labels. A real fix would widen the gap when the
  combined half-caption widths of two neighbours exceed their box spacing.

## Minor / style (do alongside the related feature)
- `layout/base.Layout.compute` raises `NotImplementedError`; could become a
  real `abc.ABC` + `@abstractmethod` once there are multiple external layouts.
- `ConnectionConfig.style` is a free string validated by an allowlist; the
  manual-connections feature is not exercised yet, revisit when it is.
