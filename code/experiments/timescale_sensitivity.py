"""
timescale_sensitivity.py
========================
Is the null an artefact of the analysis window?

At a 30 s window the load coordinate has lag-1 autocorrelation ~0.985, i.e. the
process is heavily oversampled relative to its own relaxation. The per-step
drift is then small compared with the noise, and the cubic term contributes
only at the margin -- which is exactly the regime in which a real cusp would be
hardest to see.

If the cusp signature appears at coarser sampling, the null is about the window
and not about the mechanism, and the paper's conclusion would have to change.
So this is run before the conclusion is written, not after.

    python experiments/timescale_sensitivity.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import datasets as D                                  # noqa: E402
from chm.estimate import fit_mle, rw_surrogate_test            # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
WINDOWS = (30.0, 60.0, 120.0, 300.0)
N_SURR = 100
SEED = 20260722


def main():
    rng = np.random.default_rng(SEED)
    rows = []

    for w in WINDOWS:
        units = []
        for sid in D.wesad_subjects():
            try:
                units.append(("WESAD", sid, D.load_wesad_subject(sid, window_s=w)))
            except Exception:
                pass
        for d in D.nurse_subjects()[:40]:
            try:
                fr = D.load_nurse_subject(d, window_s=w)
                if fr is not None:
                    units.append(("NURSE", d.name, fr))
            except Exception:
                pass

        ident, sig_cal, ac1s, ns = [], [], [], []
        for ds, name, fr in units:
            if len(fr) < 60:
                continue
            x = fr["x"].to_numpy(float)
            S, T, U = (fr[c].to_numpy(float) for c in ("S", "T", "U"))
            f = fit_mle(x, S, T, U)
            ident.append(bool(f.get("cusp_identified")))
            ac1s.append(float(np.corrcoef(x[:-1], x[1:])[0, 1]))
            ns.append(len(x))
            try:
                s = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                                      statistics=("lam_t",))
                sig_cal.append(s["lam_t"]["p"] < 0.05)
            except Exception:
                pass

        row = {
            "window_s": w,
            "n_units": len(ident),
            "median_n_samples": float(np.median(ns)) if ns else np.nan,
            "median_ac1": float(np.median(ac1s)) if ac1s else np.nan,
            "frac_cusp_identified": float(np.mean(ident)) if ident else np.nan,
            "frac_significant_calibrated": float(np.mean(sig_cal)) if sig_cal else np.nan,
        }
        rows.append(row)
        print(f"window={w:5.0f}s  units={row['n_units']:3d}  "
              f"median n={row['median_n_samples']:6.0f}  "
              f"AC1={row['median_ac1']:.3f}  "
              f"identified={row['frac_cusp_identified']:.3f}  "
              f"calibrated sig={row['frac_significant_calibrated']:.3f}",
              flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "e11_timescale.csv", index=False)
    print(f"\nwrote {RESULTS/'e11_timescale.csv'}")
    print("\nRead this as: if 'calibrated sig' stays near the 0.05 nominal rate "
          "across every window, the null is not a sampling artefact.")


if __name__ == "__main__":
    main()
