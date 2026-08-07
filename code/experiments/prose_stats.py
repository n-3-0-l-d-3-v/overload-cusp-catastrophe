"""
prose_stats.py
==============
Measure sentence-length variation in the manuscript.

Not a plagiarism or AI detector -- those are unreliable and this makes no
attempt to imitate one. It measures one thing that is real: how much sentence
length varies. Prose that hits the same length every sentence reads as flat
whoever or whatever wrote it, and evening out that rhythm is ordinary line
editing that improves a paper regardless.

    python code/experiments/prose_stats.py
    python code/experiments/prose_stats.py --tex main_full_journal.tex --list

Reports mean, standard deviation, and the share of very short and very long
sentences. A standard deviation near or above the mean's half is healthy
academic prose; well under that reads mechanical.
"""

from __future__ import annotations

import argparse
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"


def strip_latex(t: str) -> str:
    """Reduce LaTeX to readable prose, approximately but consistently."""
    t = re.sub(r"(?<!\\)%.*", "", t)
    # Drop float and display environments wholesale: captions and table cells
    # are not prose and would skew the distribution.
    for env in ("figure", "figure*", "table", "table*", "tabular",
                "equation", "align", "align*", "IEEEkeywords", "thebibliography"):
        t = re.sub(re.escape("\\begin{" + env + "}") + r".*?"
                   + re.escape("\\end{" + env + "}"), " ", t, flags=re.S)
    t = re.sub(r"\$\$.*?\$\$", " X ", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " X ", t)
    t = re.sub(r"\\[a-zA-Z@]+\*?", " ", t)      # control sequences
    t = re.sub(r"[{}\[\]\\]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def sentences(t: str):
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [s.strip() for s in parts if len(s.strip().split()) >= 3]


def report(path: Path, show_list: bool):
    raw = path.read_text(encoding="utf-8")
    start = raw.find("\\begin{abstract}")
    end = raw.find("\\section*{Acknowledgment}")
    if start == -1:
        start = 0
    if end == -1:
        end = len(raw)
    body = strip_latex(raw[start:end])
    sents = sentences(body)
    w = [len(s.split()) for s in sents]
    if not w:
        print(f"{path.name}: no prose found")
        return

    mean = statistics.mean(w)
    sd = statistics.pstdev(w)
    short = sum(1 for x in w if x <= 8)
    long_ = sum(1 for x in w if x >= 30)

    print(f"\n{path.name}")
    print(f"  sentences            {len(w)}")
    print(f"  mean length          {mean:.1f} words")
    print(f"  standard deviation   {sd:.1f}   (sd/mean = {sd / mean:.2f})")
    print(f"  shortest / longest   {min(w)} / {max(w)}")
    print(f"  very short (<=8)     {short:3d}  ({100 * short / len(w):.0f}%)")
    print(f"  very long  (>=30)    {long_:3d}  ({100 * long_ / len(w):.0f}%)")
    verdict = ("varied" if sd / mean >= 0.5 else
               "somewhat flat" if sd / mean >= 0.38 else "flat")
    print(f"  rhythm               {verdict}")

    if show_list:
        print("\n  longest sentences:")
        for s in sorted(sents, key=lambda x: -len(x.split()))[:6]:
            print(f"    [{len(s.split()):3d}] {s[:110]}...")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="main.tex")
    ap.add_argument("--list", action="store_true",
                    help="show the longest sentences, which are what to fix")
    a = ap.parse_args()
    report(PAPER / a.tex, a.list)


if __name__ == "__main__":
    main()
