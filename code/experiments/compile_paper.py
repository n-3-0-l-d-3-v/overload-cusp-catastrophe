"""
compile_paper.py
================
Compile the manuscript and report anything a reviewer would see as a defect:
page count, boxes that overflow the column, and unresolved references.

    python code/experiments/compile_paper.py
    python code/experiments/compile_paper.py --target 5 --strict
    python code/experiments/compile_paper.py --tex main_full_journal.tex

Uses Tectonic if it is on PATH or under tools/, because it is self-contained
and fetches only the packages the document needs. Falls back to pdflatex.

Why the log is parsed rather than skimmed
-----------------------------------------
A LaTeX run that "succeeds" can still produce a PDF with text past the column
edge, a table wider than the page, or a figure sitting on the caption below it.
LaTeX reports all of that as warnings and exits zero, and in a two-column IEEE
layout the damage is easy to miss when scrolling a PDF.

An overfull \\hbox is text that did not fit its line, so it protrudes into the
gutter or the margin. Anything over about 5 pt is visible on paper. Overfull
\\vbox means content ran past the bottom of the column. Both are reported here
with the source line, so they can be fixed rather than noticed at submission.

Underfull boxes are cosmetic -- they mean loose inter-word spacing -- and are
counted but not treated as failures unless they are severe.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGS = ROOT / "figures"
TOOLS = ROOT / "tools"

# "Overfull \hbox (12.34pt too wide) in paragraph at lines 145--150"
BOX_RE = re.compile(
    r"(Overfull|Underfull)\s+\\([hv])box\s+\(([\d.]+)pt too (wide|deep)\)"
    r"(?:[^\n]*?at lines?\s+(\d+)(?:--(\d+))?)?", re.S)
BADNESS_RE = re.compile(
    r"(Underfull)\s+\\([hv])box\s+\(badness (\d+)\)"
    r"(?:[^\n]*?at lines?\s+(\d+)(?:--(\d+))?)?", re.S)
UNDEF_REF = re.compile(r"Reference `([^']+)' on page \d+ undefined")
UNDEF_CITE = re.compile(r"Citation `([^']+)' on page \d+ undefined")
MULTI_LABEL = re.compile(r"Label `([^']+)' multiply defined")
# \bibitem{key}\n<content>  -- an entry whose content is blank or whitespace
BIBITEM_RE = re.compile(r"\\bibitem\{([^}]*)\}(.*?)(?=\\bibitem\{|\\end\{thebibliography\})",
                        re.S)


def empty_bib_entries(bbl_text):
    """
    Bibliography entries that resolved to nothing.

    BibTeX has no comment character. A note written as
    `@article{key,   % checked` puts the note where the first field name
    belongs, and BibTeX emits a \\bibitem with an empty body rather than an
    error. The citation is "defined", so no warning fires, the compile exits
    zero, and the reference list silently contains a blank numbered entry.
    Two of those reached a submission-ready PDF in this project before anyone
    looked at the last page.
    """
    out = []
    for m in BIBITEM_RE.finditer(bbl_text):
        body = re.sub(r"[\s~]|\\newblock|\\BIBentry\w*|%.*", "", m.group(2))
        if len(body) < 8:
            out.append(m.group(1))
    return out


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
        data = pdf.read_bytes()
        return max(data.count(b"/Type /Page") - data.count(b"/Type /Pages"), 0)


def parse_log(text, threshold):
    """Pull the layout defects out of a LaTeX log."""
    over, under = [], []
    for m in BOX_RE.finditer(text):
        kind, box, pts, _, l0, l1 = m.groups()
        rec = {"box": box, "pt": float(pts),
               "lines": f"{l0}--{l1}" if l1 else (l0 or "?")}
        (over if kind == "Overfull" else under).append(rec)
    for m in BADNESS_RE.finditer(text):
        _, box, bad, l0, l1 = m.groups()
        under.append({"box": box, "pt": 0.0, "badness": int(bad),
                      "lines": f"{l0}--{l1}" if l1 else (l0 or "?")})
    return {
        "overfull": [o for o in over if o["pt"] >= threshold],
        "overfull_minor": [o for o in over if o["pt"] < threshold],
        "underfull": under,
        "undef_ref": sorted(set(UNDEF_REF.findall(text))),
        "undef_cite": sorted(set(UNDEF_CITE.findall(text))),
        "multi_label": sorted(set(MULTI_LABEL.findall(text))),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="main.tex")
    ap.add_argument("--target", type=int, default=None,
                    help="expected page count; nonzero exit if different")
    ap.add_argument("--strict", action="store_true",
                    help="nonzero exit on any visible overfull box "
                         "or unresolved reference")
    ap.add_argument("--threshold", type=float, default=5.0,
                    help="pt of overflow considered visible (default 5)")
    ap.add_argument("--out", default=None, help="output PDF name")
    args = ap.parse_args()

    kind, exe = find_engine()
    if not kind:
        print("No LaTeX engine found. Install Tectonic, drop the binary in "
              "tools/, or upload paper/ to Overleaf.")
        return 2

    stem = Path(args.tex).stem
    with tempfile.TemporaryDirectory() as td:
        build = Path(td)
        shutil.copy(PAPER / args.tex, build)
        shutil.copy(PAPER / "refs.bib", build)
        for f in FIGS.glob("*.pdf"):
            shutil.copy(f, build)
        # The journal draft \input's the generated results tables. Without
        # these the build halts on a missing-file error partway through.
        if (PAPER / "tables").is_dir():
            shutil.copytree(PAPER / "tables", build / "tables",
                            dirs_exist_ok=True)

        if kind == "tectonic":
            r = subprocess.run(
                [exe, "-X", "compile", args.tex, "--outdir", str(build),
                 "--keep-logs", "--print"],
                cwd=build, capture_output=True, text=True)
            # Parse only the final pass. Tectonic reruns until references
            # settle and streams every pass to stdout, so folding stdout in
            # here would report first-pass "undefined citation" warnings that
            # the last pass already resolved.
            log = (build / f"{stem}.log")
            log_text = log.read_text(errors="replace") if log.exists() else ""
            if not log_text:
                log_text = r.stdout + r.stderr
            if r.returncode:
                print(r.stdout[-3000:])
                print(r.stderr[-3000:])
                return 1
        else:
            for _ in range(2):
                subprocess.run([exe, "-interaction=nonstopmode", args.tex],
                               cwd=build, capture_output=True)
            subprocess.run(["bibtex", stem], cwd=build, capture_output=True)
            for _ in range(2):
                subprocess.run([exe, "-interaction=nonstopmode", args.tex],
                               cwd=build, capture_output=True)
            log = build / f"{stem}.log"
            log_text = log.read_text(errors="replace") if log.exists() else ""

        pdf = build / f"{stem}.pdf"
        if not pdf.exists():
            print("compile produced no PDF")
            return 1

        n = page_count(pdf)
        out = PAPER / (args.out or ("paper_5page.pdf" if stem == "main"
                                    else f"{stem}.pdf"))
        shutil.copy(pdf, out)

        d = parse_log(log_text, args.threshold)
        bbl = build / f"{stem}.bbl"
        d["empty_bib"] = (empty_bib_entries(bbl.read_text(errors="replace"))
                          if bbl.exists() else [])
        print(f"engine     : {kind}")
        print(f"source     : paper/{args.tex}")
        print(f"pages      : {n}")
        print(f"written to : {out.relative_to(ROOT)}")
        print()
        print(f"overfull boxes >= {args.threshold:g}pt : "
              f"{len(d['overfull'])}   <-- visible on the page")
        for o in d["overfull"]:
            print(f"    \\{o['box']}box  {o['pt']:6.2f}pt too "
                  f"{'wide' if o['box'] == 'h' else 'deep'}   "
                  f"at lines {o['lines']}")
        print(f"overfull boxes <  {args.threshold:g}pt : "
              f"{len(d['overfull_minor'])}  (sub-visual)")
        print(f"underfull boxes             : {len(d['underfull'])}  "
              f"(loose spacing, cosmetic)")

        problems = 0
        for name, items in (("undefined references", d["undef_ref"]),
                            ("undefined citations", d["undef_cite"]),
                            ("multiply defined labels", d["multi_label"]),
                            ("EMPTY bibliography entries", d["empty_bib"])):
            if items:
                problems += len(items)
                print(f"\n{name}: {len(items)}")
                for k in items:
                    print(f"    {k}")

        rc = 0
        if args.target is not None and n != args.target:
            print(f"\nPAGE COUNT MISMATCH: expected {args.target}, got {n}")
            rc = 1
        if args.strict and (d["overfull"] or problems):
            print("\nSTRICT: visible layout defects or unresolved references")
            rc = 1
        if rc == 0:
            print("\nclean")
    return rc


if __name__ == "__main__":
    sys.exit(main())
