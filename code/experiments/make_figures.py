"""
make_figures.py
===============
All figures for the paper, at IEEE two-column widths (3.5 in single, 7.16 in
double) and 600 dpi.

    python experiments/make_figures.py --config B

Fig. 1  the cusp geometry: potential, bifurcation set, and the derived states
Fig. 2  the 3/2 hysteresis law, theory vs measurement                    (P1)
Fig. 3  early-warning scaling exponents against their predicted values   (P2)
Fig. 4  bistability against the random-walk null
Fig. 5  held-out model comparison
Fig. 6  transition matrix and dwell-time over-dispersion                 (P3)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chm import potential as P                                    # noqa: E402
from chm.model import STATES                                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True, parents=True)

COL1, COL2 = 3.5, 7.16
DPI = 600

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.6,
    "lines.linewidth": 1.0,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

C = {"calm": "#4C72B0", "focused": "#55A868", "stuck": "#DD8452",
     "overloaded": "#C44E52", "recovering": "#8172B3",
     "theory": "#333333", "data": "#C44E52", "null": "#AAAAAA"}


def _save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=DPI)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf")


# --------------------------------------------------------------------------- #
def fig1_geometry():
    fig, axes = plt.subplots(1, 3, figsize=(COL2, 2.25),
                             constrained_layout=True)

    # (a) the potential at three drives
    ax = axes[0]
    x = np.linspace(-2.0, 2.0, 400)
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    for b, ls, lab in ((-0.8 * bc, ":", r"$b<-b_c$"),
                       (0.0, "-", r"$b=0$"),
                       (0.8 * bc, "--", r"$b>0$")):
        ax.plot(x, P.potential(x, a, b), ls, color=C["theory"], label=lab)
    ax.set_xlabel(r"load $x$")
    ax.set_ylabel(r"$V(x;a,b)$")
    ax.set_title("(a) cusp potential")
    ax.legend(frameon=False, loc="upper center", handlelength=1.6)

    # (b) bifurcation set with the five states
    ax = axes[1]
    aa = np.linspace(0, 3.0, 300)
    bc_curve = P.fold_drive(aa)
    ax.fill_between(aa, -bc_curve, bc_curve, color=C["stuck"], alpha=0.18,
                    label="bistable")
    ax.plot(aa, bc_curve, color=C["theory"], lw=0.9)
    ax.plot(aa, -bc_curve, color=C["theory"], lw=0.9)
    ax.axhline(0, color="k", lw=0.4)
    # placement follows the geometry: above the wedge is monostable-high,
    # below it monostable-low, inside it the two bistable regimes
    ax.annotate("overloaded", (1.15, 1.68), fontsize=6.5, ha="center")
    ax.annotate("calm / focused", (1.15, -1.72), fontsize=6.5, ha="center")
    ax.annotate("stuck", (2.45, 0.42), fontsize=6.5, ha="center")
    ax.annotate("recovering", (2.45, -0.72), fontsize=6.5, ha="center")
    ax.set_xlabel(r"splitting factor $a$")
    ax.set_ylabel(r"drive $b$")
    ax.set_title("(b) bifurcation set")
    ax.set_ylim(-2, 2)

    # (c) the hysteresis loop
    ax = axes[2]
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    bs = np.linspace(-1.6 * bc, 1.6 * bc, 400)
    lo, hi = P.stable_equilibria(a * np.ones_like(bs), bs)
    sad = P.saddle(a * np.ones_like(bs), bs)
    ax.plot(bs, lo, color=C["calm"], label="lower branch")
    ax.plot(bs, hi, color=C["overloaded"], label="upper branch")
    ax.plot(bs, sad, ":", color=C["null"], lw=0.8, label="saddle")
    ax.axvline(bc, color=C["theory"], lw=0.5, ls="--")
    ax.axvline(-bc, color=C["theory"], lw=0.5, ls="--")
    ax.annotate("", xy=(bc, 1.35), xytext=(bc, 0.35),
                arrowprops=dict(arrowstyle="->", lw=0.8, color=C["overloaded"]))
    ax.annotate("", xy=(-bc, -1.35), xytext=(-bc, -0.35),
                arrowprops=dict(arrowstyle="->", lw=0.8, color=C["calm"]))
    ax.set_xlabel(r"drive $b$")
    ax.set_ylabel(r"equilibrium load $x^*$")
    ax.set_title(r"(c) hysteresis, width $\Delta b=\frac{4}{3\sqrt{3}}a^{3/2}$")
    ax.legend(frameon=False, loc="lower right", handlelength=1.4)

    _save(fig, "fig1_geometry")


# --------------------------------------------------------------------------- #
def fig2_hysteresis(cfg):
    f = RESULTS / f"e5_hysteresis_cfg{cfg}.csv"
    if not f.exists():
        return
    d = pd.read_csv(f).dropna(subset=["observed_width", "a_bar"])
    d = d[(d["a_bar"] > 0) & (d["observed_width"] > 0)]
    if len(d) < 4:
        print("  fig2: too few units")
        return

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.3))

    ax = axes[0]
    aa = np.linspace(max(d["a_bar"].min(), 1e-2), d["a_bar"].max(), 100)
    ax.plot(aa, P.hysteresis_width(aa), color=C["theory"],
            label=r"theory $\frac{4}{3\sqrt{3}}a^{3/2}$")
    for ds, m in (("WESAD", "o"), ("EXAM", "s"), ("NURSE", "^")):
        s = d[d["dataset"] == ds]
        if len(s):
            ax.scatter(s["a_bar"], s["observed_width"], s=9, marker=m,
                       alpha=0.7, label=ds)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"mean splitting factor $\bar a$")
    ax.set_ylabel(r"observed loop width $\Delta b$")
    ax.set_title("(a) hysteresis width vs theory")
    ax.legend(frameon=False, fontsize=6)

    ax = axes[1]
    j = RESULTS / f"scaling_p1_cfg{cfg}.json"
    sc = json.loads(j.read_text()) if j.exists() else {}
    if "exponent" in sc:
        ax.errorbar([0], [sc["exponent"]],
                    yerr=[[sc["exponent"] - sc["ci_lo"]],
                          [sc["ci_hi"] - sc["exponent"]]],
                    fmt="o", color=C["data"], capsize=3, ms=4,
                    label="estimated")
        ax.axhline(1.5, color=C["theory"], ls="--", label="predicted 3/2")
        ax.set_xlim(-0.6, 0.6)
        ax.set_xticks([])
        ax.set_ylabel("scaling exponent")
        ax.set_title(f"(b) exponent, $R^2$={sc.get('r2', float('nan')):.2f}, "
                     f"n={sc.get('n', 0)}")
        ax.legend(frameon=False)
    _save(fig, f"fig2_hysteresis_cfg{cfg}")


# --------------------------------------------------------------------------- #
def fig3_ews(cfg):
    f = RESULTS / f"e6_ews_cfg{cfg}.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    fig, axes = plt.subplots(1, 3, figsize=(COL2, 2.2))

    for ax, col, pred, name in (
        (axes[0], "var_exponent", -0.5, r"variance: predicted $-1/2$"),
        (axes[1], "ac1_exponent", 0.5, r"$-\log$AC1: predicted $+1/2$"),
    ):
        v = d[col].dropna()
        if len(v):
            ax.hist(v, bins=18, color=C["data"], alpha=0.7)
            ax.axvline(pred, color=C["theory"], ls="--", label="predicted")
            ax.axvline(v.median(), color=C["calm"], ls="-",
                       label=f"median {v.median():.2f}")
            ax.legend(frameon=False, fontsize=6)
        ax.set_xlabel("fitted exponent")
        ax.set_ylabel("units")
        ax.set_title(name)

    ax = axes[2]
    leads = [c for c in d.columns if c.startswith("auc_lead")]
    if leads:
        vals = [d[c].dropna() for c in leads]
        ax.boxplot(vals, labels=[c.replace("auc_lead", "") for c in leads],
                   widths=0.5, showfliers=False)
        ax.axhline(0.5, color=C["theory"], ls="--", lw=0.7)
        ax.set_xlabel("lead time (windows)")
        ax.set_ylabel("AUC")
        ax.set_title("prospective onset prediction")
    _save(fig, f"fig3_ews_cfg{cfg}")


# --------------------------------------------------------------------------- #
def fig4_nulls(cfg):
    f = RESULTS / f"e3_lrt_cfg{cfg}.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.2))

    ax = axes[0]
    if {"lr_obs", "lr_null_p95"} <= set(d.columns):
        s = d.dropna(subset=["lr_obs", "lr_null_p95"])
        ax.scatter(s["lr_null_p95"], s["lr_obs"], s=9, alpha=0.7,
                   color=C["data"])
        m = max(s["lr_null_p95"].max(), s["lr_obs"].max()) if len(s) else 1
        ax.plot([0, m], [0, m], "--", color=C["theory"], lw=0.7)
        ax.set_xlabel("random-walk null, 95th pct")
        ax.set_ylabel("observed LR statistic")
        ax.set_title("(a) bistability vs random walk")

    ax = axes[1]
    ps = [c for c in ("p_nested", "p_rw_lr", "p_rw_bimodality")
          if c in d.columns]
    if ps:
        ax.boxplot([d[c].dropna() for c in ps],
                   labels=["nested\nLRT", "RW\n(LR)", "RW\n(bimodal)"],
                   widths=0.5, showfliers=False)
        ax.axhline(0.05, color=C["theory"], ls="--", lw=0.7)
        ax.set_ylabel("p-value")
        ax.set_title("(b) per-unit p-values")
    _save(fig, f"fig4_nulls_cfg{cfg}")


# --------------------------------------------------------------------------- #
def fig5_comparison(cfg):
    f = RESULTS / f"e4_comparison_cfg{cfg}.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    models = [m for m in ("CHM", "Markov", "Logistic", "HMM", "OU", "GBM")
              if m in d.columns and d[m].notna().any()]
    fig, ax = plt.subplots(figsize=(COL1, 2.2))
    vals = [d[m].dropna() for m in models]
    ax.boxplot(vals, labels=models, widths=0.55, showfliers=False)
    ax.set_ylabel("held-out log-density / step")
    ax.set_title("one-step-ahead prediction")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _save(fig, f"fig5_comparison_cfg{cfg}")


# --------------------------------------------------------------------------- #
def fig6_states(cfg):
    tm = RESULTS / f"transition_matrix_cfg{cfg}.csv"
    dw = RESULTS / f"e7_dwell_cfg{cfg}.csv"
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.4))

    if tm.exists():
        M = pd.read_csv(tm, index_col=0)
        ax = axes[0]
        im = ax.imshow(M.values, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(STATES)))
        ax.set_xticklabels([s[:4] for s in STATES], rotation=40, ha="right")
        ax.set_yticks(range(len(STATES)))
        ax.set_yticklabels([s[:4] for s in STATES])
        for i in range(len(STATES)):
            for j in range(len(STATES)):
                v = M.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=5.5, color="white" if v > 0.5 else "black")
        ax.set_title("(a) empirical transition matrix")
        fig.colorbar(im, ax=ax, fraction=0.046)

    if dw.exists():
        d = pd.read_csv(dw)
        ax = axes[1]
        for st, mk in (("overloaded", "o"), ("stuck", "s")):
            s = d[d["state"] == st]
            if len(s):
                ax.scatter(s["cv_geometric"], s["cv_observed"], s=9,
                           marker=mk, alpha=0.7, label=st, color=C[st])
        lim = [0, 2.0]
        ax.plot(lim, lim, "--", color=C["theory"], lw=0.7,
                label="geometric (Markov)")
        ax.set_xlabel("CV under geometric null")
        ax.set_ylabel("observed CV of dwell time")
        ax.set_title("(b) dwell-time over-dispersion")
        ax.legend(frameon=False, fontsize=6)
    _save(fig, f"fig6_states_cfg{cfg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="B")
    args = ap.parse_args()
    print("figures:")
    fig1_geometry()
    fig2_hysteresis(args.config)
    fig3_ews(args.config)
    fig4_nulls(args.config)
    fig5_comparison(args.config)
    fig6_states(args.config)
    fig7_power_size()
    fig8_timescale(args.config)




# --------------------------------------------------------------------------- #
def fig7_power_size():
    """
    The methodological headline: power is ~1 while the nominal test's SIZE is
    ~0.35 rather than 0.05.  Both panels share a y-axis so the gap between
    "would have found it" and "finds it when it isn't there" is immediate.
    """
    f = RESULTS / "e0_power_size.csv"
    if not f.exists():
        print("  fig7: no power/size results yet")
        return
    d = pd.read_csv(f)

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.4), sharey=True,
                             constrained_layout=True)

    ax = axes[0]
    null = d[d["regime"].str.contains("random walk")]
    ax.plot(null["n"], null["reject_nominal"], "o-", color=C["overloaded"],
            label="nominal $t$-test")
    if null["reject_calibrated"].notna().any():
        ax.plot(null["n"], null["reject_calibrated"], "s-", color=C["calm"],
                label="surrogate-calibrated")
    ax.axhline(0.05, color=C["theory"], ls="--", lw=0.8, label="nominal 0.05")
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$")
    ax.set_ylabel("rejection rate")
    ax.set_title("(a) SIZE: random-walk input")
    ax.legend(frameon=False, fontsize=6.5)

    ax = axes[1]
    for name, mk in (("cusp: strong", "o"), ("cusp: moderate", "s"),
                     ("cusp: weak", "^")):
        s = d[d["regime"] == name]
        if len(s):
            ax.plot(s["n"], s["reject_calibrated"].fillna(s["reject_nominal"]),
                    mk + "-", label=name.replace("cusp: ", ""))
    ax.axhline(0.05, color=C["theory"], ls="--", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("series length $n$")
    ax.set_title("(b) POWER: true cusp input")
    ax.legend(frameon=False, fontsize=6.5)
    ax.set_ylim(-0.03, 1.05)

    _save(fig, "fig7_power_size")


def fig8_timescale(cfg="B"):
    """Is the null an artefact of the analysis window?  Apparently not."""
    f = RESULTS / "e11_timescale.csv"
    if not f.exists():
        print("  fig8: no timescale results yet")
        return
    d = pd.read_csv(f)

    fig, ax = plt.subplots(figsize=(COL1, 2.2), constrained_layout=True)
    ax.plot(d["window_s"], d["frac_significant_calibrated"], "o-",
            color=C["overloaded"], label="calibrated rejection rate")
    ax.axhline(0.05, color=C["theory"], ls="--", lw=0.8, label="chance (0.05)")
    ax.set_xscale("log")
    ax.set_xlabel("analysis window (s)")
    ax.set_ylabel("fraction of units significant")
    ax.set_ylim(-0.02, max(0.3, float(d["frac_significant_calibrated"].max()) * 1.3))
    ax.set_title("cusp detection vs sampling timescale")
    # annotate both the autocorrelation and the unit count: the rightmost
    # point rests on far fewer units than the others and should not be read
    # as a trend
    for _, r in d.iterrows():
        if not np.isfinite(r["frac_significant_calibrated"]):
            continue
        ax.annotate(f"AC1={r['median_ac1']:.2f}\nn={int(r['n_units'])}",
                    (r["window_s"], r["frac_significant_calibrated"]),
                    textcoords="offset points", xytext=(0, 8),
                    fontsize=5.5, ha="center", linespacing=1.1)
    ax.margins(x=0.18)
    ax.legend(frameon=False, fontsize=6.5)
    _save(fig, "fig8_timescale")

if __name__ == "__main__":
    main()
