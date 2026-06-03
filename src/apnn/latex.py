import re

_SPECIAL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "|": r"\textbar{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
}

_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
# xcolor expressions: rgb:blue,5;red,2 / red!50!white / named / HTML hex
_COLOR = re.compile(r"^[A-Za-z0-9 :;,!.#-]+$")


def escape_text(text: object) -> str:
    """Escape LaTeX special characters so user text renders literally."""
    return "".join(_SPECIAL.get(ch, ch) for ch in str(text))


def is_identifier(name: str) -> bool:
    return bool(_IDENT.match(name))


def is_color(value: str) -> bool:
    return bool(_COLOR.match(value))
