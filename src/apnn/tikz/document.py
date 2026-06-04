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
        # init.tex \providecommand's defaults; override with the width-derived scale
        r"\renewcommand{\fntlg}" + font(32) + "\n"
        r"\renewcommand{\fntmd}" + font(25) + "\n"
        r"\renewcommand{\fntsm}" + font(20) + "\n"
    )


def to_begin() -> str:
    # edge styles + \copymidarrow now live in styles/init.tex so hand-written
    # documents that import the styles get them too
    return (
        r"\begin{document}" "\n"
        r"\begin{tikzpicture}" "\n"
    )


def to_end() -> str:
    return (
        r"\end{tikzpicture}" "\n"
        r"\end{document}" "\n"
    )
