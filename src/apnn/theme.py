from dataclasses import dataclass, fields, replace


@dataclass
class Theme:
    conv: str = r"rgb:yellow,5;red,2.5;white,5"
    conv_band: str = r"rgb:yellow,5;red,5;white,5"
    pool: str = r"rgb:red,1;black,0.3"
    upsample: str = r"rgb:blue,2;green,1;black,0.3"
    fc: str = r"rgb:blue,5;red,2.5;white,5"
    fc_band: str = r"rgb:blue,5;red,5;white,4"
    softmax: str = r"rgb:magenta,5;black,7"
    sum_op: str = r"rgb:blue,5;green,15"
    concat: str = r"rgb:blue,3;green,2;white,5"
    input_layer: str = r"rgb:magenta,2;blue,1;white,8"
    output_layer: str = r"rgb:green,3;blue,1;white,6"
    edge: str = r"rgb:blue,4;red,1;green,4;black,3"

    def colors_tex(self) -> str:
        return r"\def\edgecolor{" + self.edge + "}\n"


THEMES: dict[str, Theme] = {
    "default": Theme(),
    "nature": Theme(
        conv=r"rgb:teal,4;green,2;white,5",
        conv_band=r"rgb:teal,6;green,3;white,3",
        upsample=r"rgb:green,2;blue,1;white,8",
        fc=r"rgb:blue,4;white,6",
        fc_band=r"rgb:blue,5;white,4",
        softmax=r"rgb:magenta,4;black,5",
    ),
    "grayscale": Theme(
        conv=r"rgb:black,2;white,8",
        conv_band=r"rgb:black,3;white,7",
        pool=r"rgb:black,4;white,6",
        upsample=r"rgb:black,1;white,9",
        fc=r"rgb:black,3;white,7",
        fc_band=r"rgb:black,4;white,6",
        softmax=r"rgb:black,5;white,5",
        sum_op=r"rgb:black,2;white,8",
        concat=r"rgb:black,2;white,8",
        input_layer=r"rgb:black,1;white,9",
        output_layer=r"rgb:black,3;white,7",
    ),
}

_VALID_KEYS = {f.name for f in fields(Theme)}


def resolve_theme(name: str, overrides: dict[str, str] | None = None) -> Theme:
    try:
        base = THEMES[name]
    except KeyError:
        raise ValueError(
            f"Unknown theme '{name}'. Available: {', '.join(sorted(THEMES))}."
        )
    if not overrides:
        return replace(base)
    unknown = set(overrides) - _VALID_KEYS
    if unknown:
        raise ValueError(
            f"Unknown color keys: {', '.join(sorted(unknown))}. "
            f"Valid keys: {', '.join(sorted(_VALID_KEYS))}."
        )
    return replace(base, **overrides)
