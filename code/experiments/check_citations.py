"""
check_citations.py
==================
Cross-check \\cite keys in the manuscript against refs.bib in both directions.
An uncited entry is harmless clutter; a cited-but-missing key silently prints
as [?] in the compiled PDF, which is the kind of thing that gets noticed in
review and nowhere earlier.

    python experiments/check_citations.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parents[2] / "paper"


def main():
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    bib = (PAPER / "refs.bib").read_text(encoding="utf-8")

    cited = set()
    for m in re.finditer(r"\\cite\{([^}]*)\}", tex):
        cited.update(k.strip() for k in m.group(1).split(",") if k.strip())

    keys = set(re.findall(r"@\w+\{\s*([^,\s]+)\s*,", bib))

    missing = sorted(cited - keys)
    unused = sorted(keys - cited)

    print(f"cite keys used in main.tex : {len(cited)}")
    print(f"entries in refs.bib        : {len(keys)}")
    print(f"resolved                   : {len(cited & keys)}")

    if missing:
        print("\nERROR - cited but absent from refs.bib "
              "(these compile as [?]):")
        for k in missing:
            print(f"   {k}")
    else:
        print("\nOK - every cited key resolves.")

    if unused:
        print("\nNote - present in refs.bib but never cited "
              "(IEEEtran omits these from the reference list):")
        for k in unused:
            print(f"   {k}")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
