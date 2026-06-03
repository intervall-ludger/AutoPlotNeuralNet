def to_head(styles_path: str) -> str:
    if not styles_path.endswith("/"):
        styles_path += "/"
    return (
        r"\documentclass[border=8pt, multi, tikz]{standalone}" "\n"
        r"\usepackage{import}" "\n"
        r"\subimport{" + styles_path + r"}{init}" "\n"
        r"\usetikzlibrary{positioning}" "\n"
        r"\usetikzlibrary{3d}" "\n"
        r"\usetikzlibrary{calc}" "\n"
        r"\usetikzlibrary{fit,backgrounds}" "\n"
        r"\newcommand{\fntlg}{\fontsize{32pt}{38pt}\selectfont}" "\n"
        r"\newcommand{\fntmd}{\fontsize{25pt}{30pt}\selectfont}" "\n"
        r"\newcommand{\fntsm}{\fontsize{20pt}{24pt}\selectfont}" "\n"
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
