"""
build_submission.py
===================
Build the two PDFs a double-blind IEEE conference submission needs from
paper/paper_conference.tex, without touching that file:

    review    author block, affiliations and repository link removed
    named     full author block, for the camera-ready upload

    python code/experiments/build_submission.py

Both are set on A4 with pdflatex, which gives the Times face of the IEEE Word
template the conference distributes. Output goes to paper/build/, which is not
tracked; the review PDF is also copied to paper/paper_conference_anonymous.pdf.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGS = ROOT / "figures"
BUILD = PAPER / "build"

# Empty, not a placeholder line: a committee screening for author blocks
# flagged "Anonymous Authors" as one and asked for a resubmission.
ANON_AUTHOR = "\\author{}"
LINK_RE = re.compile(
    r"Code, figures and this manuscript are released under the MIT licence at\s+"
    r"\\url\{[^}]*\}, with a\s+provenance table recording the replication count "
    r"behind every number\.", re.S)
ANON_LINK = (
    "Code, figures and a provenance table recording the replication count "
    "behind every number are publicly released under the MIT licence; the link "
    "is withheld for double-blind review.")


def variant(tex: str, anonymous: bool) -> str:
    tex = tex.replace("\\documentclass[conference]{IEEEtran}",
                      "\\documentclass[conference,a4paper]{IEEEtran}")
    if anonymous:
        tex, n = re.subn(r"\\author\{\n.*?\n\}\n(?=\n% Activates)",
                         lambda m: ANON_AUTHOR + "\n", tex, flags=re.S)
        if n != 1:
            raise SystemExit("author block not found")
        tex, n = LINK_RE.subn(lambda m: ANON_LINK, tex)
        if n != 1:
            raise SystemExit("repository sentence not found")
    return tex


def compile_pdf(stem: str) -> int:
    def run(*cmd):
        return subprocess.run(cmd, cwd=BUILD, capture_output=True, text=True,
                              errors="replace")
    run("pdflatex", "-interaction=nonstopmode", f"{stem}.tex")
    run("bibtex", stem)
    run("pdflatex", "-interaction=nonstopmode", f"{stem}.tex")
    r = run("pdflatex", "-interaction=nonstopmode", f"{stem}.tex")
    m = re.search(r"Output written on .*?\((\d+) pages?", r.stdout)
    if not m:
        print(r.stdout[-2000:])
        raise SystemExit(f"{stem}: no PDF produced")
    log = (BUILD / f"{stem}.log").read_text(errors="replace")
    undefined = len(re.findall(r"(Citation|Reference) `[^']+' on page", log))
    overfull = [float(x) for x in re.findall(r"Overfull \\hbox \(([\d.]+)pt", log)]
    print(f"{stem}.pdf: {m.group(1)} pages, {undefined} unresolved, "
          f"{sum(1 for x in overfull if x >= 5)} visible overfull boxes")
    return int(m.group(1))


def main() -> int:
    if not shutil.which("pdflatex"):
        print("pdflatex not found")
        return 2
    BUILD.mkdir(exist_ok=True)
    shutil.copy(PAPER / "refs.bib", BUILD)
    for f in FIGS.glob("*.pdf"):
        shutil.copy(f, BUILD)
    src = (PAPER / "paper_conference.tex").read_text(encoding="utf-8")
    src = src.replace("\r\n", "\n")
    pages = []
    for stem, anonymous in (("submission_review", True),
                            ("submission_named", False)):
        (BUILD / f"{stem}.tex").write_text(variant(src, anonymous),
                                           encoding="utf-8", newline="\n")
        pages.append(compile_pdf(stem))
    shutil.copy(BUILD / "submission_review.pdf",
                PAPER / "paper_conference_anonymous.pdf")
    print("copied the review PDF to paper/paper_conference_anonymous.pdf")
    return 0 if all(p <= 6 for p in pages) else 1


if __name__ == "__main__":
    sys.exit(main())
