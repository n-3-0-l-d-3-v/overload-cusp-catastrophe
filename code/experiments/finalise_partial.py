"""
finalise_partial.py
===================
Turn a stopped Monte Carlo run into honest summary files.

The suite is chunked and checkpointed, so an interrupted run leaves complete
work behind in `results/_checkpoints/`. This script writes that work out as
proper summaries and records, in the CSV itself, exactly how much of the
intended grid each one covers. It never pads, interpolates, or presents a
partial sweep as a finished one.

Two jobs.

**Noise.** The run stopped 23 chunks into 38. Because jobs are ordered
sigma-major, those chunks happen to cover ten of the fifteen (sigma, drive)
cells at the full 1000 replicates rather than all fifteen at partial depth.
Ten complete cells are worth reporting; five missing cells are worth saying so
about. A `complete` column marks which is which.

**Power.** The power block never started, and the earlier smoke output was
deleted rather than shipped. The paper's power figures come from
`e0_power_size.csv`, a real 100-replicate-per-cell run, so this rebuilds
`m3_power_summary.csv` from that file with `n_rep` recorded honestly as 100.
The provenance is visible in the data rather than only in prose.

    python code/experiments/finalise_partial.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
CKPT = RESULTS / "_checkpoints"

SIGMAS = (0.10, 0.20, 0.30, 0.45, 0.60)
DRIVES = (0.5, 1.0, 1.5)
REP_NOISE_TARGET = 1000


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = p + z**2 / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((c - h) / d, (c + h) / d)


def finalise_noise():
    part = CKPT / "m6_noise_partial.csv"
    if not part.exists():
        print("noise: no checkpoint, skipping")
        return
    df = pd.read_csv(part)
    rows = []
    for sg in SIGMAS:
        for dr in DRIVES:
            d = df[(df["sigma"] == sg) & (df["drive_scale"] == dr)]
            if not len(d):
                continue
            k, n = int(d["detected"].sum()), len(d)
            lo, hi = wilson(k, n)
            rows.append({
                "sigma": sg, "drive_scale": dr, "n_rep": n,
                "detection_rate": k / n, "ci_lo": lo, "ci_hi": hi,
                "complete": n >= REP_NOISE_TARGET,
            })
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m6_noise_summary.csv", index=False)
    done = int(s["complete"].sum())
    print(f"noise: {done}/{len(SIGMAS) * len(DRIVES)} cells complete at "
          f"{REP_NOISE_TARGET} replicates "
          f"(detection {s.loc[s.complete, 'detection_rate'].min():.3f}"
          f"-{s.loc[s.complete, 'detection_rate'].max():.3f})")
    if done < len(SIGMAS) * len(DRIVES):
        miss = s[~s["complete"]]
        print(f"        incomplete/absent: "
              f"{len(SIGMAS) * len(DRIVES) - done} cells at the high-sigma end")


def finalise_power():
    """
    Rebuild m3_power_summary.csv from the E0 run.

    E0 labels its regimes 'cusp: strong' and carries a 'random walk (null)'
    row, which belongs in the size analysis rather than the power one; it is
    dropped here. E0 covers four lengths and three effect sizes, against the
    six and four the full block would have run.
    """
    src = RESULTS / "e0_power_size.csv"
    if not src.exists():
        print("power: no e0_power_size.csv, skipping")
        return
    e0 = pd.read_csv(src)
    e0 = e0[e0["regime"].str.startswith("cusp:")].copy()
    e0["regime"] = e0["regime"].str.replace("cusp: ", "", regex=False)

    rows = []
    for _, r in e0.iterrows():
        n_rep = int(r["n_rep"])
        k = int(round(r["reject_calibrated"] * n_rep))
        lo, hi = wilson(k, n_rep)
        rows.append({
            "n": int(r["n"]), "regime": r["regime"], "n_rep": n_rep,
            "power_nominal": float(r["reject_nominal"]),
            "power_calibrated": float(r["reject_calibrated"]),
            "ci_lo": lo, "ci_hi": hi, "source": "e0_power_size.csv",
        })
    s = pd.DataFrame(rows).sort_values(["regime", "n"])
    s.to_csv(RESULTS / "m3_power_summary.csv", index=False)
    at200 = s[s["n"] == 200].set_index("regime")["power_calibrated"]
    print(f"power: rebuilt from E0 at {s['n_rep'].iloc[0]} replicates/cell; "
          "n=200 calibrated power "
          + ", ".join(f"{k}={v:.2f}" for k, v in at200.items()))


if __name__ == "__main__":
    finalise_noise()
    finalise_power()
    sys.exit(0)
