"""
reproduce.py
============
Run the whole artefact end to end, or any stage of it, and say plainly what
succeeded.

    python code/experiments/reproduce.py --stage check     # no data needed
    python code/experiments/reproduce.py --stage fast      # + quick MC
    python code/experiments/reproduce.py --stage all       # + full MC, hours

Stages
------
check   Tests, citation consistency, and a paper compile with the page-count
        and layout assertions. Needs no corpora and no network. This is the
        stage to run before a submission.
fast    Everything in `check`, plus the Monte Carlo suite at 2% replication.
        Minutes. Verifies the pipeline runs; the numbers are not publishable.
all     Everything in `check`, plus the Monte Carlo suite at full replication.
        Around seven hours on six cores. These are the numbers in the paper.

The corpus analyses (run_all.py) are deliberately not included: they need the
three datasets on disk, which are 20 GB and cannot be redistributed. Fetch them
with fetch_data.py first, then run run_all.py --config B.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def run(label, cmd, optional=False):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}", flush=True)
    t = time.time()
    r = subprocess.run(cmd, cwd=ROOT)
    dt = time.time() - t
    ok = r.returncode == 0
    status = "OK" if ok else ("SKIPPED" if optional else "FAILED")
    print(f"\n-> {label}: {status} ({dt:.0f}s)", flush=True)
    return ok or optional


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="check",
                    choices=("check", "fast", "all"))
    args = ap.parse_args()

    steps = [
        ("unit tests (analytic claims + parameter recovery)",
         [PY, "-m", "pytest"], False),
        ("citation consistency (offline)",
         [PY, "code/experiments/check_citations.py"], False),
        ("compile manuscript: 5 pages, no overfull boxes, no empty refs",
         [PY, "code/experiments/compile_paper.py", "--target", "5",
          "--strict"], True),
    ]

    if args.stage == "fast":
        steps.append(("Monte Carlo suite at 2% replication (smoke)",
                      [PY, "code/experiments/mega_run.py", "--block", "all",
                       "--rep-scale", "0.02"], False))
    elif args.stage == "all":
        steps.append(("Monte Carlo suite at full replication (hours)",
                      [PY, "code/experiments/mega_run.py", "--block", "all",
                       "--resume"], False))

    if args.stage in ("fast", "all"):
        steps.append(("figures from the Monte Carlo output",
                      [PY, "code/experiments/make_figures_v2.py"], False))

    results = [(label, run(label, cmd, opt)) for label, cmd, opt in steps]

    print(f"\n{'=' * 70}\nSUMMARY\n{'=' * 70}")
    for label, ok in results:
        print(f"  {'pass' if ok else 'FAIL'}  {label}")
    failed = [l for l, ok in results if not ok]
    if failed:
        print(f"\n{len(failed)} stage(s) failed.")
        return 1
    print("\nall stages passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
