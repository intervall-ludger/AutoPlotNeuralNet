def to_head(styles_path: str, font_scale: float = 1.0) -> str:
    if not styles_path.endswith("/"):
        styles_path += "/"

    def font(size: float) -> str:
        s = size * font_scale
        return r"{\fontsize{" + f"{s:.1f}pt}}{{{s * 1.2:.1f}pt}}" + r"\selectfont}"

    return (
        r"\documentclass[border=8pt, multi, tikz]{standalone}" "\n"
        r"\usepackage{import}" "\n"
        r"\subimport{" + styles_path + r"}{init}" "\n"
        r"\usetikzlibrary{positioning}" "\n"
        r"\usetikzlibrary{3d}" "\n"
        r"\usetikzlibrary{calc}" "\n"
        r"\usetikzlibrary{fit,backgrounds}" "\n"
        r"\newcommand{\fntlg}" + font(32) + "\n"
        r"\newcommand{\fntmd}" + font(25) + "\n"
        r"\newcommand{\fntsm}" + font(20) + "\n"
    )


def to_begin() -> str:
    return (
        r"\begin{document}" "\n"
        r"\begin{tikzpicture}" "\n"
        r"\tikzstyle{connection}=[ultra thick,every node/.style={sloped,allow upside down},"
        r"draw=\edgecolor,opacity=0.7]" "\n"
        r"\tikzstyle{copyconnection}=[very thick,every node/.style={sloped,allow upside down},"
        r"draw={rgb:blue,5;red,1;green,1;black,2},opacity=0.85]" "\n"
        r"\newcommand{\copymidarrow}{\tikz \draw[-Stealth,line width=1.0mm,"
        r"draw={rgb:blue,5;red,1;green,1;black,2}] (-0.3,0) -- ++(0.3,0);}" "\n"
    )


def to_end() -> str:
    return (
        r"\end{tikzpicture}" "\n"
        r"\end{document}" "\n"
    )
