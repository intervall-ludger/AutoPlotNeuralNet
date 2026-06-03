from ..latex import escape_text


def _wrap_color(c: str) -> str:
    if ("," in c or ";" in c) and not c.startswith("{"):
        return "{" + c + "}"
    return c


def to_box(name: str, fill: str, offset: str = "(0,0,0)", to: str = "(0,0,0)",
           width: float = 2, height: float = 40, depth: float = 40,
           opacity: float = 0.7, xlabel: str = "", ylabel: str = "",
           zlabel: str = "", caption: str = " ") -> str:
    fill = _wrap_color(fill)
    return (
        r"\pic[shift={" + offset + "}] at " + to + "\n"
        r"    {Box={" "\n"
        r"        name=" + name + ",\n"
        r"        caption={" + escape_text(caption) + "},\n"
        r"        xlabel={" + escape_text(xlabel) + "},\n"
        r"        ylabel={" + escape_text(ylabel) + "},\n"
        r"        zlabel={" + str(zlabel) + "},\n"
        r"        fill=" + fill + ",\n"
        r"        opacity=" + str(opacity) + ",\n"
        r"        height=" + str(height) + ",\n"
        r"        width=" + str(width) + ",\n"
        r"        depth=" + str(depth) + "\n"
        r"        }" "\n"
        r"    };" "\n"
    )


def to_banded_box(name: str, fill: str, bandfill: str, offset: str = "(0,0,0)",
                  to: str = "(0,0,0)", width: float = 2, bandwidth: float = 2,
                  height: float = 40, depth: float = 40, opacity: float = 0.7,
                  xlabel: str = "", ylabel: str = "", zlabel: str = "",
                  caption: str = " ") -> str:
    fill = _wrap_color(fill)
    bandfill = _wrap_color(bandfill)
    return (
        r"\pic[shift={" + offset + "}] at " + to + "\n"
        r"    {RightBandedBox={" "\n"
        r"        name=" + name + ",\n"
        r"        caption={" + escape_text(caption) + "},\n"
        r"        xlabel={" + escape_text(xlabel) + "},\n"
        r"        ylabel={" + escape_text(ylabel) + "},\n"
        r"        zlabel={" + str(zlabel) + "},\n"
        r"        fill=" + fill + ",\n"
        r"        bandfill=" + bandfill + ",\n"
        r"        opacity=" + str(opacity) + ",\n"
        r"        height=" + str(height) + ",\n"
        r"        width=" + str(width) + ",\n"
        r"        bandwidth=" + str(bandwidth) + ",\n"
        r"        depth=" + str(depth) + "\n"
        r"        }" "\n"
        r"    };" "\n"
    )


def to_connection(from_name: str, to_name: str) -> str:
    return (
        r"\draw [connection] (" + from_name + "-east)"
        r" -- node {\midarrow} (" + to_name + "-west);" "\n"
    )


def _anchor(name: str, anchor: str, shift_x: float) -> str:
    if shift_x:
        return f"([xshift={shift_x}cm]{name}-{anchor})"
    return "(" + name + "-" + anchor + ")"


def to_edge(from_name: str, from_anchor: str, to_name: str, to_anchor: str,
            dashed: bool = False, label: str = "", shift_x: float = 0.0) -> str:
    style = "connection, densely dashed" if dashed else "connection"
    if label:
        # connection labels are author-provided LaTeX (e.g. math), not escaped
        mid = r"node[midway, above, font=\fntsm\bfseries] {" + label + "}"
    else:
        mid = r"node {\midarrow}"
    return (
        r"\draw [" + style + "] " + _anchor(from_name, from_anchor, shift_x) + " -- "
        + mid + " " + _anchor(to_name, to_anchor, shift_x) + ";" "\n"
    )


def to_dashed_connection(from_name: str, to_name: str) -> str:
    return (
        r"\draw [connection, densely dashed] (" + from_name + "-east)"
        r" -- node {\midarrow} (" + to_name + "-west);" "\n"
    )


def to_skip(from_name: str, to_name: str, pos: float = 1.5) -> str:
    tag = from_name + "_to_" + to_name
    arrow = r"node {\copymidarrow}"
    return (
        r"\path (" + from_name + "-north) ++(0," + str(pos) + ",0) coordinate (" + tag + "-top);" "\n"
        r"\draw [copyconnection]" "\n"
        "    (" + from_name + "-north) -- " + arrow + " (" + tag + "-top)\n"
        "    -- " + arrow + " (" + to_name + "-north |- " + tag + "-top)\n"
        "    -- " + arrow + " (" + to_name + "-north);\n"
    )


def to_caption(name: str, baseline_ref: str, caption: str, drop: float = 0.5) -> str:
    """Box caption placed on a shared baseline (lowest box south, minus ``drop`` cm)."""
    return (
        r"\node[anchor=north, font=\fntmd, yshift=-" + f"{drop:.2f}" + "cm] at ("
        + name + "-south |- " + baseline_ref + "-south) {"
        + escape_text(caption) + "};" "\n"
    )


def to_bracket_group(from_name: str, to_name: str, label: str,
                     yshift: int = -45, y_ref: str | None = None) -> str:
    if y_ref is None:
        y_ref = from_name
    return (
        r"\draw [decorate, decoration={brace, amplitude=8pt, mirror}]" "\n"
        "    ([yshift=" + str(yshift) + "pt]" + from_name + "-southwest |- " + y_ref + "-southwest)\n"
        "    -- ([yshift=" + str(yshift) + "pt]" + to_name + "-southeast |- " + y_ref + "-southwest)\n"
        r"    node [midway, below=10pt, font=\fntlg\bfseries] {" + escape_text(label) + "};\n"
    )


def _legend_mini_box(name: str, fill: str, bandfill: str, is_banded: bool,
                     w: float = 0.7, h: float = 0.85, d: float = 0.3) -> str:
    half_h = h / 2
    band_x = w * 2 / 3  # band starts at 2/3 of the box width
    right_fill = bandfill if is_banded else fill

    def coord(dx: float = 0, dy: float = 0) -> str:
        shifts = []
        if dx:
            shifts.append(f"xshift={dx:.3f}cm")
        if dy:
            shifts.append(f"yshift={dy:.3f}cm")
        return "([" + ", ".join(shifts) + "]" + name + ")" if shifts else "(" + name + ")"

    fill = _wrap_color(fill)
    bandfill = _wrap_color(bandfill)
    right_fill = _wrap_color(right_fill)
    lines = ""
    lines += r"\fill[fill=" + fill + ", fill opacity=0.7] " + coord(dy=-half_h) + " rectangle " + coord(dx=w, dy=half_h) + ";\n"
    if is_banded:
        lines += r"\fill[fill=" + bandfill + ", fill opacity=0.7] " + coord(dx=band_x, dy=-half_h) + " rectangle " + coord(dx=w, dy=half_h) + ";\n"
    lines += r"\draw[black!50, line width=0.3pt] " + coord(dy=-half_h) + " rectangle " + coord(dx=w, dy=half_h) + ";\n"
    lines += r"\fill[fill=" + fill + ", fill opacity=0.45] " + coord(dy=half_h) + " -- " + coord(dx=d, dy=half_h + d) + " -- " + coord(dx=w + d, dy=half_h + d) + " -- " + coord(dx=w, dy=half_h) + " -- cycle;\n"
    lines += r"\draw[black!50, line width=0.3pt] " + coord(dy=half_h) + " -- " + coord(dx=d, dy=half_h + d) + " -- " + coord(dx=w + d, dy=half_h + d) + " -- " + coord(dx=w, dy=half_h) + ";\n"
    lines += r"\fill[fill=" + right_fill + ", fill opacity=0.55] " + coord(dx=w, dy=-half_h) + " -- " + coord(dx=w + d, dy=-half_h + d) + " -- " + coord(dx=w + d, dy=half_h + d) + " -- " + coord(dx=w, dy=half_h) + " -- cycle;\n"
    lines += r"\draw[black!50, line width=0.3pt] " + coord(dx=w, dy=-half_h) + " -- " + coord(dx=w + d, dy=-half_h + d) + " -- " + coord(dx=w + d, dy=half_h + d) + " -- " + coord(dx=w, dy=half_h) + ";\n"
    lines += r"\coordinate (" + name + "-east) at " + coord(dx=w + d) + ";\n"
    lines += r"\coordinate (" + name + "-top) at " + coord(dx=d, dy=half_h + d) + ";\n"
    lines += r"\coordinate (" + name + "-bot) at " + coord(dy=-half_h) + ";\n"
    return lines


def to_legend(items: list[dict], gap: int = 50, item_width: float | None = None) -> str:
    n = len(items)
    if item_width is None:
        longest = max((len(item["label"]) for item in items), default=0)
        item_width = max(5.0, 2.2 + longest * 0.42)
    total_width = n * item_width

    lines = ""
    # centre the legend on the full diagram width (bounding box centre), below it
    lines += (
        r"\coordinate (legend-anchor) at ([yshift=-" + str(gap) + "pt]current bounding box.south);" "\n"
        r"\coordinate (legend-start) at ([xshift=-" + f"{total_width / 2:.3f}" + "cm]legend-anchor);" "\n"
    )

    for i, item in enumerate(items):
        xshift = i * item_width
        leg = "leg" + str(i)
        lines += r"\coordinate (" + leg + ") at ([xshift=" + f"{xshift:.3f}" + "cm]legend-start);\n"
        fill = item["fill"]
        bandfill = item.get("bandfill", fill)
        lines += _legend_mini_box(leg, fill, bandfill, item.get("banded", False))
        lines += (
            r"\node[right=10pt of " + leg + r"-east, font=\fntmd, anchor=west] ("
            + leg + "lbl) {" + escape_text(item["label"]) + "};\n"
        )

    fit_parts = []
    for i in range(n):
        leg = "leg" + str(i)
        fit_parts.extend(["(" + leg + ")", "(" + leg + "-top)", "(" + leg + "-bot)", "(" + leg + "lbl)"])

    lines += (
        r"\begin{scope}[on background layer]" "\n"
        r"\node[fit=" + " ".join(fit_parts) + ", "
        r"inner xsep=18pt, inner ysep=14pt, rounded corners=8pt, "
        r"fill=black!2, draw=black!35, line width=0.6pt] (legend-bg) {};" "\n"
        r"\end{scope}" "\n"
    )
    return lines
