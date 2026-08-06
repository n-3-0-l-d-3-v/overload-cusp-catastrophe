"""
surrogate_comparison.py
=======================
E13: resolving the configuration-C non-replication.

Configuration C (skin temperature as the load coordinate) rejected the null in
11.5% of units against a random-walk ensemble, roughly 3.7 standard errors
above nominal, where configurations B and A both sat at 5.1%. Either skin
temperature carries fold structure the other coordinates do not, or the
random-walk surrogate is an inadequate null for it.

The second is testable. A random walk matched on length, increment variance and
marginal scale cannot reproduce deterministic low-frequency structure, and
wrist temperature carries a great deal of it (circadian rhythm, ambient
temperature, wear artefacts, sensor warm-up). If a signal has trend that the
null ensemble lacks, the surrogates are easy to beat and the test inflates.

IAAFT surrogates (Schreiber & Schmitz 1996) preserve both the power spectrum
and the marginal distribution, so the trend survives into the null and only
nonlinear structure distinguishes data from surrogate. Running the same test
under both ensembles separates the two explanations:

    if C's rejection rate falls to nominal under IAAFT  -> it was the null
    if it stays elevated                                -> it is the signal

    python experiments/surrogate_comparison.py --configs B,C,A
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import datasets as D                                  # noqa: E402
from chm.estimate import rw_surrogate_test                     # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
SEED = 20260722
N_SURR = 150


def collect(config, nurse_limit=60):
    """Load every unit for one sensor configuration."""
    units = []
    for sid in D.wesad_subjects():
        try:
            units.append(("WESAD", sid, D.load_wesad_subject(sid, config=config)))
        except Exception:
            pass
    for d in D.exam_sessions():
        try:
            fr = D.load_exam_session(d, config=config)
            if fr is not None:
                units.append(("EXAM", d.name, fr))
        except Exception:
            pass
    for d in D.nurse_subjects()[:nurse_limit]:
        try:
            fr = D.load_nurse_subject(d, config=config)
            if fr is not None:
                units.append(("NURSE", d.name, fr))
        except Exception:
            pass
    return units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="B,C,A")
    ap.add_argument("--nurse-limit", type=int, default=60)
    ap.add_argument("--surr", type=int, default=N_SURR)
    args = ap.parse_args()

    rng = np.random.default_rng(SEED)
    rows = []

    for cfg in args.configs.split(","):
        units = collect(cfg, args.nurse_limit)
        print(f"\nconfig {cfg}: {len(units)} units", flush=True)
        for ds, name, fr in units:
            if len(fr) < 60:
                continue
            x = fr["x"].to_numpy(float)
            S, T, U = (fr[c].to_numpy(float) for c in ("S", "T", "U"))
            row = {"config": cfg, "dataset": ds, "unit": str(name),
                   "n": len(x),
                   "ac1": float(np.corrcoef(x[:-1], x[1:])[0, 1])}
            for kind in ("rw", "iaaft"):
                try:
                    r = rw_surrogate_test(x, S, T, U, n_surr=args.surr, rng=rng,
                                          statistics=("lam_t",), surrogate=kind)
                    row[f"p_{kind}"] = r["lam_t"]["p"]
                except Exception as e:
                    print(f"   {name} [{kind}] failed: {e}")
                    row[f"p_{kind}"] = np.nan
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "e13_surrogate_comparison.csv", index=False)

    print("\n" + "=" * 72)
    print("Cubic-term rejection rate by surrogate ensemble")
    print("=" * 72)
    print(f"{'config':7s} {'units':>6s} {'median AC1':>11s} "
          f"{'p<.05 (RW)':>11s} {'p<.05 (IAAFT)':>14s}")
    for cfg, g in df.groupby("config"):
        rw = g["p_rw"].dropna()
        ia = g["p_iaaft"].dropna()
        print(f"{cfg:7s} {len(g):6d} {g['ac1'].median():11.3f} "
              f"{np.mean(rw < 0.05):11.3f} {np.mean(ia < 0.05):14.3f}")

    print("\nRead: nominal is 0.05. If configuration C falls to nominal under")
    print("IAAFT but not under RW, the elevation was the null model, not the")
    print("signal -- and the RW ensemble is inadequate for trended series.")

    # per-corpus detail for whichever config is most elevated
    print("\nPer-corpus detail:")
    for (cfg, ds), g in df.groupby(["config", "dataset"]):
        rw, ia = g["p_rw"].dropna(), g["p_iaaft"].dropna()
        if len(g):
            print(f"  {cfg} {ds:6s} n={len(g):3d}  "
                  f"RW={np.mean(rw < 0.05):.3f}  IAAFT={np.mean(ia < 0.05):.3f}")

    print(f"\nwrote {RESULTS/'e13_surrogate_comparison.csv'}")


if __name__ == "__main__":
    main()
