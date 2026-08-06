"""
compile_paper.py
================
Compile the manuscript and report the exact page count.

Uses Tectonic if it is on PATH or in tools/, because it is self-contained and
fetches only the packages the document actually needs. Falls back to pdflatex.

    python experiments/compile_paper.py
    python experiments/compile_paper.py --target 5     # fail if not 5 pages

Page count matters here: the conference version has a hard 5-page limit, and
"about five pages" is not a thing you can submit.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGS = ROOT / "figures"
TOOLS = ROOT / "tools"


def find_engine():
    for name in ("tectonic", "tectonic.exe"):
        p = shutil.which(name)
        if p:
            return ("tectonic", p)
    for cand in TOOLS.glob("**/tectonic*"):
        if cand.is_file():
            return ("tectonic", str(cand))
    p = shutil.which("pdflatex")
    if p:
        return ("pdflatex", p)
    return (None, None)


def page_count(pdf: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except ImportError:
        # crude fallback: count page objects
        data = pdf.read_bytes()
        return max(data.count(b"/Type /Page") - data.count(b"/Type /Pages"), 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=None,
                    help="expected page count; nonzero exit if different")
    args = ap.parse_args()

    kind, exe = find_engine()
    if not kind:
        print("No LaTeX engine found. Install Tectonic, or drop the binary in "
              "tools/, or upload paper/ to Overleaf.")
        return 2

    with tempfile.TemporaryDirectory() as td:
        build = Path(td)
        shutil.copy(PAPER / "main.tex", build)
        shutil.copy(PAPER / "refs.bib", build)
        for f in FIGS.glob("*.pdf"):
            shutil.copy(f, build)

        if kind == "tectonic":
            cmd = [exe, "-X", "compile", "main.tex", "--outdir", str(build)]
            r = subprocess.run(cmd, cwd=build, capture_output=True, text=True)
            if r.returncode:
                print(r.stdout[-3000:])
                print(r.stderr[-3000:])
                return 1
        else:
            for _ in range(2):
                subprocess.run([exe, "-interaction=nonstopmode", "main.tex"],
                               cwd=build, capture_output=True)
            subprocess.run(["bibtex", "main"], cwd=build, capture_output=True)
            for _ in range(2):
                subprocess.run([exe, "-interaction=nonstopmode", "main.tex"],
                               cwd=build, capture_output=True)

        pdf = build / "main.pdf"
        if not pdf.exists():
            print("compile produced no PDF")
            return 1

        n = page_count(pdf)
        out = PAPER / "paper_5page.pdf"
        shutil.copy(pdf, out)
        print(f"engine     : {kind}")
        print(f"pages      : {n}")
        print(f"written to : {out.relative_to(ROOT)}")

        if args.target is not None and n != args.target:
            print(f"PAGE COUNT MISMATCH: expected {args.target}, got {n}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
