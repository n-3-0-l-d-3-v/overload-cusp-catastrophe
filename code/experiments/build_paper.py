"""
build_paper.py
==============
Produce the distributable forms of the manuscript.

No LaTeX toolchain is assumed to be installed, so this does two things:

1. Assembles an Overleaf-ready bundle (`paper/overleaf_bundle.zip`) containing
   main.tex, refs.bib, the generated tables and the figures, with paths already
   flattened so it compiles on upload with no edits.

2. Converts the manuscript to .docx via pandoc, for the common case of a
   supervisor or co-author who works in Word. The .docx is a readable
   equivalent, NOT an IEEE-formatted submission: pandoc cannot reproduce the
   two-column IEEEtran layout. Submit the LaTeX.

    python experiments/build_paper.py
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGS = ROOT / "figures"
BUILD = PAPER / "build"


def make_bundle():
    """Flatten graphics paths and zip everything Overleaf needs."""
    BUILD.mkdir(exist_ok=True, parents=True)
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    # Overleaf bundle keeps figures/ and tables/ alongside main.tex
    tex = tex.replace(r"\graphicspath{{../figures/}}", r"\graphicspath{{figures/}}")
    (BUILD / "main.tex").write_text(tex, encoding="utf-8")
    shutil.copy(PAPER / "refs.bib", BUILD / "refs.bib")

    tdir = BUILD / "tables"
    tdir.mkdir(exist_ok=True)
    for f in (PAPER / "tables").glob("*.tex"):
        shutil.copy(f, tdir / f.name)

    fdir = BUILD / "figures"
    fdir.mkdir(exist_ok=True)
    n_fig = 0
    for f in FIGS.glob("*.pdf"):
        shutil.copy(f, fdir / f.name)
        n_fig += 1
    # PNGs too: pdflatex prefers the PDF, but pandoc needs a raster
    # to embed figures in the .docx
    for f in FIGS.glob("*.png"):
        shutil.copy(f, fdir / f.name)

    # also carry the flattened single-file version, if present: some users
    # prefer pasting one .tex into Overleaf over uploading a multi-file bundle
    single = PAPER / "paper_ieee_singlefile.tex"
    if single.exists():
        shutil.copy(single, BUILD / "paper_ieee_singlefile.tex")

    zpath = PAPER / "overleaf_bundle.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in BUILD.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(BUILD))
    print(f"  overleaf bundle -> {zpath.relative_to(ROOT)}  ({n_fig} figures)")
    return zpath


def make_docx():
    try:
        import pypandoc
    except ImportError:
        print("  docx: pypandoc not installed; skipping "
              "(pip install pypandoc_binary)")
        return None

    # pandoc will not guess a file extension, so \includegraphics{fig1_geometry}
    # silently drops the image. Point it at the PNGs explicitly for this pass;
    # the LaTeX build still uses the PDFs.
    tex = (BUILD / "main.tex").read_text(encoding="utf-8")
    tex = re.sub(r"(\\includegraphics(?:\[[^\]]*\])?\{)([^}]*)(\})",
                 lambda m: m.group(1) + f"figures/{m.group(2)}.png" + m.group(3),
                 tex)
    src = BUILD / "main_docx.tex"
    src.write_text(tex, encoding="utf-8")

    out = PAPER / "paper.docx"
    try:
        pypandoc.convert_file(
            str(src), "docx", outputfile=str(out),
            extra_args=[
                f"--bibliography={PAPER/'refs.bib'}",
                "--citeproc",
                f"--resource-path={BUILD}",
                "--number-sections",
            ],
        )
        print(f"  word version    -> {out.relative_to(ROOT)}")
        print("     (readable equivalent; the LaTeX is the submission form)")
        return out
    except Exception as e:
        print(f"  docx conversion failed: {e}")
        return None


def _expanded_tex():
    r"""main.tex with \input{...} files spliced in, so label checks see them."""
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    for inc in re.findall(r"\\input\{([^}]*)\}", tex):
        f = PAPER / (inc if inc.endswith(".tex") else inc + ".tex")
        if f.exists():
            tex += "\n" + f.read_text(encoding="utf-8")
    return tex


def sanity_checks():
    """Cheap checks that catch the errors reviewers notice and authors do not."""
    tex = _expanded_tex()
    problems = []

    # abstract length (IEEE conference guidance: 150-250 words)
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if m:
        words = len(re.sub(r"\\[a-zA-Z]+|\{|\}|\$", " ", m.group(1)).split())
        flag = "" if 150 <= words <= 250 else "  <-- outside IEEE 150-250"
        print(f"  abstract words  : {words}{flag}")
        if words > 250:
            problems.append(f"abstract is {words} words (IEEE limit 250)")

    # unresolved references
    for lab in re.findall(r"\\ref\{([^}]*)\}", tex):
        if f"\\label{{{lab}}}" not in tex:
            problems.append(f"\\ref{{{lab}}} has no matching \\label")

    # figures referenced but not present
    for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex):
        if not (FIGS / f"{g}.pdf").exists() and not (FIGS / g).exists():
            problems.append(f"figure not found: {g}")

    # placeholder text left behind
    for bad in ("TODO", "XXX", "FIXME", "\\todo"):
        if bad in tex:
            problems.append(f"placeholder '{bad}' left in manuscript")

    if problems:
        print("\n  ISSUES:")
        for p in problems:
            print(f"     - {p}")
    else:
        print("  sanity checks   : clean")
    return problems


def main():
    print("building paper artefacts:")
    make_bundle()
    make_docx()
    problems = sanity_checks()
    print("\nTo compile: upload paper/overleaf_bundle.zip to Overleaf, "
          "set the compiler to pdfLaTeX, and build main.tex.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
