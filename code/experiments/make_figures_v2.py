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

# IEEEtran column width is 3.487in and text width 7.16in. A figure must be
# authored at the width it will be *included* at, because LaTeX scales the
# whole thing -- fonts included -- to fit \includegraphics[width=...]. A 7.16in
# figure dropped into a \columnwidth slot is shrunk by a factor of two, which
# turns 8pt axis labels into 4pt and is why the first version of Figs. 2 and 3
# was unreadable in print. Nothing in the LaTeX log warns about this.
COL1, COL2, DPI = 3.487, 7.16, 600

# Which width each figure is authored for. Checked at save time.
USAGE = {
    "fig9_identifiability": COL1,
    "fig10_size_power": COL1,
    "fig11_ews_grid": COL2,
    "fig12_persistence": COL1,
}

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
    want = USAGE.get(name)
    got = fig.get_size_inches()[0]
    if want and abs(got - want) > 0.35:
        raise SystemExit(
            f"{name}: authored {got:.2f}in wide but the manuscript includes "
            f"it at {want:.2f}in. LaTeX would rescale the fonts by "
            f"{want / got:.2f}x. Fix the figsize or the USAGE entry.")
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=DPI)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf  ({got:.2f}in wide)")


def fig_identifiability():
    f = RESULTS / "m1_recovery_summary.csv"
    if not f.exists():
        print("  ident: no data")
        return
    d = pd.read_csv(f)

    # Two rows, not two columns: at \columnwidth a side-by-side pair leaves
    # each panel 1.7in wide, which is too narrow for a log axis and a legend.
    fig, axes = plt.subplots(2, 1, figsize=(COL1, 2.95),
                             gridspec_kw={"height_ratios": [1.25, 1.0]},
                             constrained_layout=True)

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
            ax.plot(s["n"], s["corr"], ls, marker=mk, color=col, ms=3.0,
                    label=lab, alpha=0.9)
    ax.axhline(0.8, color=C["ref"], lw=0.7, ls="--")
    ax.text(880, 0.84, "identified", fontsize=5.8, color=C["ref"],
            ha="right", va="bottom")
    ax.axvline(200, color=C["grey"], lw=0.8, alpha=0.7)
    ax.text(200, 1.10, "median observed $n$", fontsize=5.5, color=C["grey"],
            ha="center", va="bottom")
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$ (windows)")
    ax.set_ylabel(r"corr(true, est.)")
    # No curve goes below -0.1, so the band under zero is free. Putting the
    # legend there keeps it off the data instead of on top of it.
    ax.set_ylim(-0.72, 1.30)
    ax.set_title("(a) which parameters are recoverable", fontsize=8, pad=9)
    ax.legend(frameon=False, ncol=4, loc="lower center", fontsize=5.0,
              handlelength=1.4, handletextpad=0.4, columnspacing=0.7,
              labelspacing=0.2, borderpad=0.1)

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
            ax.annotate("median $\\hat\\lambda$ in\nthe real corpora",
                        xy=(0.0059, max(med)), xytext=(0.010, max(med) * 1.25),
                        fontsize=5.8, color=C["alt"], va="center",
                        arrowprops=dict(arrowstyle="-", color=C["alt"],
                                        lw=0.6, shrinkA=0, shrinkB=2))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"estimated $\hat\lambda$")
    ax.set_ylabel(r"abs. error in $\hat\alpha_0$")
    ax.set_title(r"(b) the geometry fails as $\hat\lambda\!\to\!0$", fontsize=8)

    _save(fig, "fig9_identifiability")


def fig_size_power():
    fs = RESULTS / "m2_size_summary.csv"
    fp = RESULTS / "m3_power_summary.csv"
    if not fs.exists():
        print("  size/power: no data yet")
        return
    s = pd.read_csv(fs)

    # Stacked, sharing the log-x series-length axis. Both panels are rejection
    # rates against the same abscissa, so one x-label serves both and each
    # panel keeps the full column width.
    fig, axes = plt.subplots(2, 1, figsize=(COL1, 2.70), sharex=True,
                             sharey=True, constrained_layout=True)
    ax = axes[0]
    ax.plot(s["n"], s["size_nominal"], "o-", color=C["bad"], ms=3.2,
            label="nominal $t$-test")
    ax.fill_between(s["n"], s["ci_lo_nominal"], s["ci_hi_nominal"],
                    color=C["bad"], alpha=0.18, lw=0)
    if s["size_calibrated"].notna().any():
        ax.plot(s["n"], s["size_calibrated"], "s-", color=C["alt"], ms=3.2,
                label="surrogate-calibrated")
        ax.fill_between(s["n"], s["ci_lo_calibrated"], s["ci_hi_calibrated"],
                        color=C["alt"], alpha=0.18, lw=0)
    ax.axhline(0.05, color=C["ref"], ls="--", lw=0.8, label="nominal 0.05")
    ax.set_ylabel("rejection rate")
    ax.set_title("(a) size: random-walk input (no cusp)", fontsize=8)
    ax.legend(frameon=False, fontsize=6, loc="center right",
              handlelength=1.8, labelspacing=0.3, borderpad=0.2)

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
                        ms=3.2, label=name)
                ax.fill_between(q["n"], q["ci_lo"], q["ci_hi"], color=col,
                                alpha=0.15, lw=0)
    ax.axhline(0.05, color=C["ref"], ls="--", lw=0.8)
    ax.axhline(0.8, color=C["grey"], ls=":", lw=0.8)
    ax.text(0.99, 0.80, "0.8", transform=ax.get_yaxis_transform(),
            fontsize=5.5, color=C["grey"], ha="right", va="bottom")
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$ (windows)")
    ax.set_ylabel("rejection rate")
    ax.set_title("(b) power: input that genuinely contains a cusp", fontsize=8)
    ax.set_ylim(-0.05, 1.08)
    ax.legend(frameon=False, fontsize=6, ncol=2, loc="lower right",
              handlelength=1.8, columnspacing=0.9, labelspacing=0.3,
              borderpad=0.2)

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
