"""
power_analysis.py
=================
E0: how much can this study actually detect?

A negative empirical result is only worth reporting if the procedure that
produced it would have found the effect had it been there.  This script
establishes that, and in doing so uncovers the reason the naive test cannot be
used at all.

Two quantities, at the sample sizes the real corpora provide:

    POWER  P(reject | a cusp is genuinely present)
    SIZE   P(reject | the series is a random walk)

The headline finding is the gap between them.  Power is essentially 1 even at
n = 200 and weak curvature, so the study is not underpowered.  But the size of
the nominal t-test on the cubic coefficient is roughly 0.35, not 0.05: on
near-unit-root data the t-statistic does not have a t-distribution (the
classical spurious-regression problem, and the same mechanism Ditlevsen &
Johnsen and Boettiger & Hastings identify for early-warning indicators).

Hence the paper reports surrogate-calibrated p-values throughout, and this
table is the justification.

    python experiments/power_analysis.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm.model import CHMParams, simulate                      # noqa: E402
from chm.estimate import fit_mle, rw_surrogate_test            # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
RESULTS.mkdir(exist_ok=True, parents=True)

SEED = 20260722
N_REP = 100
N_SURR = 100
SIZES = (100, 200, 500, 1000)
REGIMES = (
    ("strong", dict(alpha0=1.5, alpha_A=0.6, lam=0.20, sigma=0.30)),
    ("moderate", dict(alpha0=1.0, alpha_A=0.4, lam=0.10, sigma=0.25)),
    ("weak", dict(alpha0=0.6, alpha_A=0.2, lam=0.05, sigma=0.20)),
)


def smooth(n, rng, k=25):
    z = rng.standard_normal(n + k)
    s = np.convolve(z, np.ones(k) / k, mode="valid")[:n]
    return (s - s.mean()) / (s.std() + 1e-9)


def main():
    rng = np.random.default_rng(SEED)
    rows = []

    for n in SIZES:
        # ---- SIZE: random-walk series, nominal and calibrated ------------ #
        nominal, calibrated = [], []
        for r in range(N_REP):
            S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
            rw = np.cumsum(rng.standard_normal(n) * 0.2)
            f = fit_mle(rw, S, T, U)
            nominal.append(bool(f.get("lam_significant")))
            if r < 25:                       # calibrated test is expensive
                s = rw_surrogate_test(rw, S, T, U, n_surr=N_SURR, rng=rng,
                                      statistics=("lam_t",))
                calibrated.append(s["lam_t"]["p"] < 0.05)
        rows.append({
            "n": n, "regime": "random walk (null)",
            "reject_nominal": float(np.mean(nominal)),
            "reject_calibrated": float(np.mean(calibrated)) if calibrated else np.nan,
            "n_rep": N_REP,
        })
        print(f"n={n:5d}  RANDOM WALK   nominal={np.mean(nominal):.3f}  "
              f"calibrated={np.mean(calibrated) if calibrated else float('nan'):.3f}")

        # ---- POWER: genuine cusp dynamics -------------------------------- #
        for name, kw in REGIMES:
            nominal, calibrated = [], []
            for r in range(N_REP):
                S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
                p = CHMParams(beta_S=0.6, beta_T=0.2, beta_U=0.1, eps=0.03, **kw)
                x = simulate(p, S, T, U, rng=rng)["x"]
                if not np.all(np.isfinite(x)):
                    continue
                f = fit_mle(x, S, T, U)
                nominal.append(bool(f.get("lam_significant")))
                if r < 25:
                    s = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                                          statistics=("lam_t",))
                    calibrated.append(s["lam_t"]["p"] < 0.05)
            rows.append({
                "n": n, "regime": f"cusp: {name}",
                "reject_nominal": float(np.mean(nominal)),
                "reject_calibrated": float(np.mean(calibrated)) if calibrated else np.nan,
                "n_rep": len(nominal),
            })
            print(f"n={n:5d}  CUSP {name:9s} nominal={np.mean(nominal):.3f}  "
                  f"calibrated={np.mean(calibrated) if calibrated else float('nan'):.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "e0_power_size.csv", index=False)
    print(f"\nwrote {RESULTS/'e0_power_size.csv'}")

    null = df[df["regime"] == "random walk (null)"]
    print("\nSummary")
    print(f"  nominal test size    : {null['reject_nominal'].mean():.3f} "
          f"(should be 0.05)")
    print(f"  calibrated test size : {null['reject_calibrated'].mean():.3f} "
          f"(should be 0.05)")
    weak = df[df["regime"] == "cusp: weak"]
    print(f"  power, weakest regime: {weak['reject_calibrated'].mean():.3f}")


if __name__ == "__main__":
    main()
