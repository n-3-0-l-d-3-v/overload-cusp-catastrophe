"""
make_figures_v2.py
==================
Figures built from the high-replication Monte Carlo suite (mega_run.py).
These supersede the low-replication versions for anything quantitative.

    python experiments/make_figures_v2.py

Fig. ident   parameter recovery against series length, all nine parameters
Fig. size    test size and power with Wilson intervals
Fig. ews     early-warning estimator validation across the full grid
Fig. persist size against AR(1) persistence, both surrogate ensembles
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True, parents=True)

COL1, COL2, DPI = 3.5, 7.16, 600

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "legend.fontsize": 6.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.1,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

C = {"good": "#2E7D32", "bad": "#C44E52", "mid": "#DD8452",
     "ref": "#333333", "alt": "#4C72B0", "grey": "#9E9E9E"}


def _save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=DPI)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf")


def fig_identifiability():
    f = RESULTS / "m1_recovery_summary.csv"
    if not f.exists():
        print("  ident: no data")
        return
    d = pd.read_csv(f)

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.5), constrained_layout=True)

    # (a) recovery correlation vs length
    ax = axes[0]
    order = [("lam", r"$\lambda$ relaxation", C["good"], "o", "-"),
             ("sigma", r"$\sigma$ diffusion", C["good"], "s", "-"),
             ("beta_S", r"$\beta_S$ sensory", C["mid"], "^", "--"),
             ("beta_T", r"$\beta_T$ switch", C["mid"], "v", "--"),
             ("alpha0", r"$\alpha_0$ splitting", C["bad"], "D", ":"),
             ("alpha_A", r"$\alpha_A$ debt gain", C["bad"], "x", ":"),
             ("eps", r"$\varepsilon$ slow rate", C["bad"], "+", ":")]
    for key, lab, col, mk, ls in order:
        s = d[d["param"] == key].sort_values("n")
        if len(s):
            ax.plot(s["n"], s["corr"], ls, marker=mk, color=col, ms=3.5,
                    label=lab, alpha=0.9)
    ax.axhline(0.8, color=C["ref"], lw=0.7, ls="--")
    ax.text(105, 0.82, "identified", fontsize=6, color=C["ref"])
    ax.axvline(200, color=C["grey"], lw=0.8, alpha=0.7)
    ax.text(207, -0.14, "median\nobserved $n$", fontsize=5.5, color=C["grey"])
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$ (windows)")
    ax.set_ylabel(r"corr(true, estimated)")
    ax.set_ylim(-0.2, 1.05)
    ax.set_title("(a) which parameters are recoverable")
    ax.legend(frameon=False, ncol=2, loc="lower right")

    # (b) the failure mode itself: error in alpha0 explodes as lambda-hat -> 0
    ax = axes[1]
    raw = RESULTS / "m1_recovery_raw.csv"
    if raw.exists():
        r = pd.read_csv(raw)
        r = r[np.isfinite(r["est_lam"]) & (r["est_lam"] > 0)
              & np.isfinite(r["est_alpha0"]) & np.isfinite(r["true_alpha0"])]
        if len(r):
            err = np.abs(r["est_alpha0"] - r["true_alpha0"])
            # bin by estimated lambda and show median error with IQR band
            bins = np.logspace(np.log10(r["est_lam"].min()),
                               np.log10(r["est_lam"].max()), 14)
            idx = np.digitize(r["est_lam"], bins)
            xs, med, lo, hi = [], [], [], []
            for k in range(1, len(bins)):
                m = idx == k
                if m.sum() < 15:
                    continue
                xs.append(np.sqrt(bins[k - 1] * bins[k]))
                med.append(np.median(err[m]))
                lo.append(np.percentile(err[m], 25))
                hi.append(np.percentile(err[m], 75))
            ax.plot(xs, med, "-", color=C["bad"], marker="o", ms=3)
            ax.fill_between(xs, lo, hi, color=C["bad"], alpha=0.18, lw=0)
            ax.axvline(0.0059, color=C["alt"], lw=1.0)
            ax.text(0.0068, max(med) * 0.5,
                    "median $\\hat\\lambda$\nin real data", fontsize=5.5,
                    color=C["alt"])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"estimated $\hat\lambda$")
    ax.set_ylabel(r"absolute error in $\hat\alpha_0$")
    ax.set_title(r"(b) the geometry fails as $\hat\lambda\!\to\!0$")

    _save(fig, "fig9_identifiability")


def fig_size_power():
    fs = RESULTS / "m2_size_summary.csv"
    fp = RESULTS / "m3_power_summary.csv"
    if not fs.exists():
        print("  size/power: no data yet")
        return
    s = pd.read_csv(fs)

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.4), sharey=True,
                             constrained_layout=True)
    ax = axes[0]
    ax.plot(s["n"], s["size_nominal"], "o-", color=C["bad"],
            label="nominal $t$-test")
    ax.fill_between(s["n"], s["ci_lo_nominal"], s["ci_hi_nominal"],
                    color=C["bad"], alpha=0.18, lw=0)
    if s["size_calibrated"].notna().any():
        ax.plot(s["n"], s["size_calibrated"], "s-", color=C["alt"],
                label="surrogate-calibrated")
        ax.fill_between(s["n"], s["ci_lo_calibrated"], s["ci_hi_calibrated"],
                        color=C["alt"], alpha=0.18, lw=0)
    ax.axhline(0.05, color=C["ref"], ls="--", lw=0.8, label="nominal 0.05")
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$")
    ax.set_ylabel("rejection rate")
    ax.set_title("(a) size: random-walk input")
    ax.legend(frameon=False)

    ax = axes[1]
    if fp.exists():
        p = pd.read_csv(fp)
        for name, col, mk in (("strong", C["good"], "o"),
                              ("moderate", C["mid"], "s"),
                              ("weak", C["bad"], "^"),
                              ("marginal", C["grey"], "v")):
            q = p[p["regime"] == name].sort_values("n")
            if len(q):
                ax.plot(q["n"], q["power_calibrated"], marker=mk, color=col,
                        ms=3.5, label=name)
                ax.fill_between(q["n"], q["ci_lo"], q["ci_hi"], color=col,
                                alpha=0.15, lw=0)
    ax.axhline(0.05, color=C["ref"], ls="--", lw=0.8)
    ax.axhline(0.8, color=C["grey"], ls=":", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$")
    ax.set_title("(b) power: genuine cusp input")
    ax.set_ylim(-0.03, 1.05)
    ax.legend(frameon=False)

    _save(fig, "fig10_size_power")


def fig_ews_grid():
    f = RESULTS / "m5_ews_summary.csv"
    if not f.exists():
        print("  ews grid: no data yet")
        return
    d = pd.read_csv(f)
    roll = d[d["estimator"] != "theory"]
    th = d[d["estimator"] == "theory"]

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.4), constrained_layout=True)
    for ax, est, pred, name in ((axes[0], "ac1", 0.5, r"rolling $-\log$AC1"),
                                (axes[1], "variance", -0.5, "rolling variance")):
        sub = roll[roll["estimator"] == est]
        for detr, col, mk in ((False, C["bad"], "o"), (True, C["alt"], "s")):
            q = sub[sub["detrend"] == detr].sort_values("window")
            if not len(q):
                continue
            g = q.groupby("window")["median"].median()
            ax.plot(g.index, g.values, marker=mk, color=col, ms=3.5,
                    label="raw" if not detr else "detrended")
        ax.axhline(pred, color=C["good"], ls="--", lw=1.0,
                   label=f"predicted {pred:+.1f}")
        ax.axhline(0.0, color=C["ref"], lw=0.6)
        if len(th):
            ax.axhline(th["median"].median(), color=C["grey"], ls=":", lw=0.9,
                       label="closed-form theory")
        ax.set_xlabel("rolling window (samples)")
        ax.set_ylabel("fitted exponent" if est == "ac1" else "")
        ax.set_title(name)
        ax.legend(frameon=False, fontsize=6)
    _save(fig, "fig11_ews_grid")


def fig_persistence():
    f = RESULTS / "m4_persistence_summary.csv"
    if not f.exists():
        print("  persistence: no data yet")
        return
    d = pd.read_csv(f).sort_values("phi")
    fig, ax = plt.subplots(figsize=(COL1, 2.2), constrained_layout=True)
    for kind, col, mk, lab in (("rw", C["bad"], "o", "random-walk surrogates"),
                               ("iaaft", C["alt"], "s", "IAAFT surrogates")):
        ax.plot(d["phi"], d[f"size_{kind}"], marker=mk, color=col, ms=3.5,
                label=lab)
        ax.fill_between(d["phi"], d[f"ci_lo_{kind}"], d[f"ci_hi_{kind}"],
                        color=col, alpha=0.16, lw=0)
    ax.axhline(0.05, color=C["ref"], ls="--", lw=0.8, label="nominal 0.05")
    ax.set_xlabel(r"AR(1) persistence $\phi$ (no cusp present)")
    ax.set_ylabel("false-positive rate")
    ax.set_title("calibrated size holds at every persistence")
    ax.legend(frameon=False)
    _save(fig, "fig12_persistence")


if __name__ == "__main__":
    print("figures (high-replication):")
    fig_identifiability()
    fig_size_power()
    fig_ews_grid()
    fig_persistence()
