"""
size_vs_persistence.py
======================
E15: is the calibrated test correctly sized for every persistence level, or
only for near-unit-root series?

Why this is asked. The surrogate comparison (E13) produced two results that do
not fit the story so far:

    config B (tonic EDA, AC1 ~ 0.98)   RW 0.046   IAAFT 0.069   <- nominal
    config C (skin temp, AC1 ~ 1.00)   RW 0.149   IAAFT 0.161   <- elevated
    config A (cardiac,   AC1 ~ 0.31)   RW 0.115   IAAFT 0.138   <- elevated

Configuration A is the NEGATIVE CONTROL. It is a noise-dominated coordinate in
which nothing should be found, and it is rejecting at two to three times
nominal under both ensembles. A negative control that fails is telling us the
test is mis-sized somewhere, not that the cardiac index contains folds.

The obvious suspect is persistence. The random-walk ensemble is matched to a
unit root by construction; applied to a series with AC1 ~ 0.3 it is far too
persistent a null, so the real series looks anomalously mean-reverting and the
test over-rejects. IAAFT should not share that flaw, since it matches the
spectrum -- so if IAAFT is also elevated, something else is going on.

This script measures the size of both calibrated tests directly, on AR(1) data
with known persistence and NO cusp, across the AC1 range the corpora actually
span.

    python experiments/size_vs_persistence.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm.estimate import rw_surrogate_test                     # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
SEED = 20260722
PHIS = (0.3, 0.5, 0.7, 0.9, 0.98, 1.0)
N_REP = 40
N_SURR = 100
N = 200


def ar1(n, phi, rng):
    """AR(1) with unit marginal variance; phi = 1 gives a random walk."""
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0]
    sd = np.sqrt(max(1 - phi ** 2, 1e-6)) if phi < 1 else 1.0
    for t in range(1, n):
        x[t] = phi * x[t - 1] + sd * e[t]
    s = x.std()
    return (x - x.mean()) / (s if s > 1e-12 else 1.0)


def smooth(n, rng, k=25):
    z = rng.standard_normal(n + k)
    s = np.convolve(z, np.ones(k) / k, mode="valid")[:n]
    return (s - s.mean()) / (s.std() + 1e-9)


def main():
    rng = np.random.default_rng(SEED)
    rows = []

    print(f"Size of the calibrated test on AR(1) data with NO cusp "
          f"(n={N}, {N_REP} reps, {N_SURR} surrogates)")
    print("=" * 68)
    print(f"{'phi':>6s} {'mean AC1':>9s} {'size (RW)':>10s} {'size (IAAFT)':>13s}")

    for phi in PHIS:
        rej = {"rw": [], "iaaft": []}
        ac1s = []
        for _ in range(N_REP):
            S, T, U = smooth(N, rng), smooth(N, rng), smooth(N, rng)
            x = ar1(N, phi, rng)
            ac1s.append(float(np.corrcoef(x[:-1], x[1:])[0, 1]))
            for kind in ("rw", "iaaft"):
                try:
                    r = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                                          statistics=("lam_t",),
                                          surrogate=kind)
                    rej[kind].append(r["lam_t"]["p"] < 0.05)
                except Exception:
                    pass
        row = {"phi": phi, "mean_ac1": float(np.mean(ac1s)),
               "size_rw": float(np.mean(rej["rw"])) if rej["rw"] else np.nan,
               "size_iaaft": float(np.mean(rej["iaaft"])) if rej["iaaft"] else np.nan,
               "n_rep": N_REP}
        rows.append(row)
        print(f"{phi:6.2f} {row['mean_ac1']:9.3f} {row['size_rw']:10.3f} "
              f"{row['size_iaaft']:13.3f}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "e15_size_vs_persistence.csv", index=False)

    print("\nInterpretation")
    worst_rw = df.loc[df["size_rw"].idxmax()]
    worst_ia = df.loc[df["size_iaaft"].idxmax()]
    print(f"  worst RW size    : {worst_rw['size_rw']:.3f} at phi={worst_rw['phi']}")
    print(f"  worst IAAFT size : {worst_ia['size_iaaft']:.3f} at phi={worst_ia['phi']}")
    near_unit = df[df["phi"] >= 0.98]
    print(f"  near unit root (phi>=0.98): RW {near_unit['size_rw'].mean():.3f}, "
          f"IAAFT {near_unit['size_iaaft'].mean():.3f}")
    low = df[df["phi"] <= 0.5]
    print(f"  low persistence (phi<=0.5): RW {low['size_rw'].mean():.3f}, "
          f"IAAFT {low['size_iaaft'].mean():.3f}")
    print("\n  If size is nominal only near phi=1, the calibrated test is valid")
    print("  for tonic EDA (AC1~0.98) but NOT for the cardiac index (AC1~0.31),")
    print("  and elevations in that configuration are an artefact of the null.")
    print(f"\nwrote {RESULTS/'e15_size_vs_persistence.csv'}")


if __name__ == "__main__":
    main()
