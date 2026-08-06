"""
rerun_comparison.py
===================
Re-runs E4 (held-out model comparison) alone, without the expensive surrogate
tests in run_all.py.

Two defects are fixed relative to the first pass, and both mattered:

1. The multinomial-logistic baseline contributed *nothing*. It passed
   `multi_class=` to scikit-learn, which removed that argument in 1.7; the
   resulting TypeError was swallowed by a bare `except: pass` in the caller, so
   the baseline silently reported no folds at all and appeared in the results
   table as an empty row.

2. The comparison ran only on units where the cusp geometry was identified,
   which is 24% of the corpus. But CHM, OU, HMM and GBM need only the series --
   the geometry is irrelevant to one-step-ahead prediction. Restricting to
   identified units conditions the comparison on the outcome, which is the same
   survivorship bias closed elsewhere in the pipeline, reintroduced here.

Both are now fixed, all silent excepts in E4 are logged, and per-model fold
counts are recorded so a baseline that quietly drops out is visible.

    python experiments/rerun_comparison.py --config B
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import datasets as D                                   # noqa: E402
from experiments.run_all import (e2_fit_all, e4_model_comparison,  # noqa: E402
                                 RESULTS, SEED, log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="B")
    ap.add_argument("--datasets", default="WESAD,EXAM,NURSE")
    ap.add_argument("--nurse-limit", type=int, default=150)
    args = ap.parse_args()

    rng = np.random.default_rng(SEED)
    units = []
    for ds in args.datasets.split(","):
        lim = args.nurse_limit if ds == "NURSE" else None
        log(f"loading {ds}")
        frames = D.prepare(ds, config=args.config, limit=lim, verbose=False)
        log(f"  {len(frames)} frames")
        units += e2_fit_all(frames, rng, ds)

    log(f"total units: {len(units)}")
    df = e4_model_comparison(units, rng)
    out = RESULTS / f"e4_comparison_cfg{args.config}.csv"
    df.to_csv(out, index=False)

    models = [m for m in ("CHM", "OU", "Markov", "Logistic", "HMM", "GBM")
              if m in df.columns]
    print("\n" + "=" * 74)
    print(f"Held-out one-step-ahead log-density  (config {args.config}, "
          f"{len(df)} units)")
    print("=" * 74)
    print(f"{'model':10s} {'mean':>9s} {'95% CI':>22s} {'units':>7s} "
          f"{'folds':>7s}")
    for m in models:
        v = df[m].dropna()
        if not len(v):
            print(f"{m:10s} {'--':>9s} {'(no folds contributed)':>22s}")
            continue
        se = v.std(ddof=1) / np.sqrt(len(v))
        nf = int(df.get(f"{m}_nfolds", pd.Series([0])).sum())
        print(f"{m:10s} {v.mean():+9.3f} "
              f"[{v.mean()-1.96*se:+8.3f},{v.mean()+1.96*se:+8.3f}] "
              f"{len(v):7d} {nf:7d}")

    if {"CHM", "OU"} <= set(df.columns):
        d = (df["CHM"] - df["OU"]).dropna()
        if len(d) > 2:
            w = stats.wilcoxon(d)
            print(f"\nCHM vs OU (its own nested monostable case):")
            print(f"   median difference {d.median():+.4f}, "
                  f"CHM better in {np.mean(d > 0):.1%} of units, "
                  f"Wilcoxon p={w.pvalue:.3g}")
            print("   The OU model IS the CHM with the cubic term switched off,")
            print("   so this is the cleanest single test of whether that term")
            print("   is doing any work.")

    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
