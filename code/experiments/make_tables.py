"""
make_tables.py
==============
Turn the results CSVs into (a) LaTeX tables for the paper and (b) a plain-text
summary with every headline number, so the Results prose can be written against
the actual output rather than against expectations.

    python experiments/make_tables.py --config B
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
TABLES = ROOT / "paper" / "tables"
TABLES.mkdir(exist_ok=True, parents=True)


def _load(name):
    p = RESULTS / name
    return pd.read_csv(p) if p.exists() else None


def _ci(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size < 2:
        return np.nan, np.nan, np.nan
    m = v.mean()
    se = v.std(ddof=1) / np.sqrt(v.size)
    return m, m - 1.96 * se, m + 1.96 * se


def _frac_sig(p, alpha=0.05):
    p = np.asarray(p, float)
    p = p[np.isfinite(p)]
    return (np.mean(p < alpha), p.size) if p.size else (np.nan, 0)


def summarise(cfg):
    out = []
    A = out.append
    A(f"{'='*70}\nCONFIG {cfg}\n{'='*70}")

    # ---- E1 recovery ---------------------------------------------------- #
    e1 = _load("e1_recovery_summary.csv")
    if e1 is not None:
        A("\n[E1] Parameter recovery (30 simulated units)")
        for _, r in e1.iterrows():
            A(f"   {r['param']:8s} bias={r['bias']:+.4f} rmse={r['rmse']:.4f} "
              f"r={r['corr']:.3f}")

    # ---- E2 fits -------------------------------------------------------- #
    e2 = _load(f"e2_fits_cfg{cfg}.csv")
    if e2 is not None:
        A(f"\n[E2] Fits: {len(e2)} units")
        for ds, g in e2.groupby("dataset"):
            A(f"   {ds}: n={len(g)}  median alpha0={g['alpha0'].median():.3f}  "
              f"median lam={g['lam'].median():.3f}  "
              f"median sigma={g['sigma'].median():.3f}  "
              f"pct_bistable={g['pct_bistable'].median():.3f}")
        A("   state occupancy (median across units):")
        for s in ("calm", "focused", "stuck", "overloaded", "recovering"):
            c = f"pct_{s}"
            if c in e2.columns:
                A(f"      {s:11s} {e2[c].median():.3f}")

    # ---- E3 nulls ------------------------------------------------------- #
    e3 = _load(f"e3_lrt_cfg{cfg}.csv")
    if e3 is not None:
        A(f"\n[E3] Bistability, {len(e3)} units")
        # p_rw_lam_t first: it is the only one of these that isolates the cubic
        # restoring term, and therefore the only one that tests the mechanism
        # rather than "something other than a random walk".
        for col, lab in (("p_rw_lam_t", "RW null, CUBIC TERM (decisive)"),
                         ("p_nested", "nested monostable LRT"),
                         ("p_rw_lr", "random-walk null, LR stat"),
                         ("p_rw_bimodality", "random-walk null, bimodality"),
                         ("p_rw_alpha0", "random-walk null, alpha0")):
            if col in e3.columns:
                f, n = _frac_sig(e3[col])
                A(f"   {lab:34s} frac p<.05 = {f:.3f}  (n={n})")
        for ds, g in e3.groupby("dataset"):
            if "p_rw_lr" in g.columns:
                fl, n = _frac_sig(g.get("p_rw_lam_t", pd.Series(dtype=float)))
                f, _ = _frac_sig(g["p_rw_lr"])
                fb, _ = _frac_sig(g.get("p_rw_bimodality", pd.Series(dtype=float)))
                A(f"   {ds}: CUBIC frac={fl:.3f} | RW-LR frac={f:.3f}  "
                  f"RW-bimod frac={fb:.3f}  n={len(g)}")

    # ---- E4 model comparison -------------------------------------------- #
    e4 = _load(f"e4_comparison_cfg{cfg}.csv")
    if e4 is not None:
        A(f"\n[E4] Held-out one-step log-density ({len(e4)} units)")
        models = [m for m in ("CHM", "Markov", "Logistic", "HMM", "OU", "GBM")
                  if m in e4.columns]
        for m in models:
            mu, lo, hi = _ci(e4[m])
            A(f"   {m:9s} {mu:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
              f"n={e4[m].notna().sum()}")
        if "CHM" in e4.columns and "OU" in e4.columns:
            d = (e4["CHM"] - e4["OU"]).dropna()
            if len(d) > 2:
                t = stats.wilcoxon(d)
                A(f"   CHM vs OU (nested):  median diff={d.median():+.4f}  "
                  f"Wilcoxon p={t.pvalue:.2e}  win rate={np.mean(d>0):.3f}")
        if "CHM" in e4.columns and "GBM" in e4.columns:
            d = (e4["CHM"] - e4["GBM"]).dropna()
            if len(d) > 2:
                A(f"   CHM vs GBM (black box): median diff={d.median():+.4f}  "
                  f"win rate={np.mean(d>0):.3f}")

    # ---- E5 hysteresis / P1 --------------------------------------------- #
    j = RESULTS / f"scaling_p1_cfg{cfg}.json"
    if j.exists():
        sc = json.loads(j.read_text())
        A("\n[E5/P1] Hysteresis width vs a^{3/2}")
        if "exponent" in sc:
            A(f"   exponent={sc['exponent']:.3f}  "
              f"95% CI [{sc['ci_lo']:.3f}, {sc['ci_hi']:.3f}]  "
              f"R2={sc['r2']:.3f}  n={sc['n']}")
            A(f"   predicted 1.5 -> {'CONSISTENT' if sc.get('consistent') else 'REJECTED'}")
        else:
            A(f"   insufficient data (n={sc.get('n', 0)})")

    e5 = _load(f"e5_hysteresis_cfg{cfg}.csv")
    if e5 is not None:
        d = e5.dropna(subset=["observed_width"])
        if len(d):
            mu, lo, hi = _ci(d["observed_width"])
            A(f"   loop width>0 in {np.mean(d['observed_width']>0):.3f} of "
              f"{len(d)} units; mean={mu:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            if "p" in d.columns:
                f, n = _frac_sig(d["p"])
                A(f"   per-unit entry>exit significant in {f:.3f} of {n}")

    # ---- E6 EWS / P2 ---------------------------------------------------- #
    e6 = _load(f"e6_ews_cfg{cfg}.csv")
    if e6 is not None:
        A("\n[E6/P2] Early-warning scaling exponents")
        for col, pred, lab in (("var_exponent", -0.5, "variance (pred -0.50)"),
                               ("ac1_exponent", 0.5, "-logAC1 (pred +0.50)")):
            if col in e6.columns:
                v = e6[col].dropna()
                if len(v):
                    mu, lo, hi = _ci(v)
                    A(f"   {lab:24s} median={v.median():+.3f}  "
                      f"mean={mu:+.3f} [{lo:+.3f}, {hi:+.3f}]  n={len(v)}")
                    A(f"      -> predicted {pred:+.2f} "
                      f"{'INSIDE' if lo <= pred <= hi else 'OUTSIDE'} mean CI")
        for ds, g in e6.groupby("dataset"):
            v = g["var_exponent"].dropna()
            if len(v) > 2:
                A(f"      {ds}: median var exponent={v.median():+.3f} (n={len(v)})")
        for c in [c for c in e6.columns if c.startswith("auc_lead")]:
            v = e6[c].dropna()
            if len(v):
                mu, lo, hi = _ci(v)
                A(f"   {c}: mean AUC={mu:.3f} [{lo:.3f}, {hi:.3f}] n={len(v)}")
        if "kendall_p_surrogate" in e6.columns:
            f, n = _frac_sig(e6["kendall_p_surrogate"])
            A(f"   Kendall-tau trend vs AR(1) surrogate: frac p<.05 = {f:.3f} (n={n})")

    # ---- E7 dwell / P3 --------------------------------------------------- #
    e7 = _load(f"e7_dwell_cfg{cfg}.csv")
    if e7 is not None and len(e7):
        A("\n[E7/P3] Dwell-time over-dispersion vs geometric")
        for st, g in e7.groupby("state"):
            mu, lo, hi = _ci(g["overdispersion"])
            A(f"   {st:11s} CV_obs={g['cv_observed'].median():.3f}  "
              f"CV_geom={g['cv_geometric'].median():.3f}  "
              f"excess={mu:+.3f} [{lo:+.3f}, {hi:+.3f}]  n={len(g)}")
            f, n = _frac_sig(g["ks_p"])
            A(f"      KS vs geometric rejected in {f:.3f} of {n}")

    # ---- E8 re-entry / P4 ------------------------------------------------ #
    e8 = _load(f"e8_reentry_cfg{cfg}.csv")
    if e8 is not None and len(e8):
        A("\n[E8/P4] Re-entry hazard (exploratory)")
        A(f"   median gap={e8['median_gap'].median():.1f} windows, n={len(e8)}")
        f, n = _frac_sig(e8["ks_expon_p"])
        A(f"   KS vs exponential rejected in {f:.3f} of {n}")

    # ---- E9 external validation ------------------------------------------ #
    e9 = _load(f"e9_validation_cfg{cfg}.csv")
    if e9 is not None and len(e9):
        A("\n[E9] Derived states vs WESAD protocol labels")
        A(f"   P(high-load | stress)={e9['p_high_given_stress'].mean():.3f}  "
          f"P(high-load | other)={e9['p_high_given_other'].mean():.3f}")
        odds = e9["odds_ratio"].replace([np.inf, -np.inf], np.nan).dropna()
        if len(odds):
            A(f"   median odds ratio={odds.median():.2f}")
        f, n = _frac_sig(e9["fisher_p"])
        A(f"   Fisher p<.05 in {f:.3f} of {n} subjects")

    return "\n".join(out)


# --------------------------------------------------------------------------- #
def latex_tables(cfg):
    """Emit the LaTeX the paper \\inputs."""
    L = []
    A = L.append

    e4 = _load(f"e4_comparison_cfg{cfg}.csv")
    if e4 is not None:
        models = [m for m in ("CHM", "OU", "Markov", "Logistic", "HMM", "GBM")
                  if m in e4.columns and e4[m].notna().any()]
        A(r"\begin{table}[t]")
        A(r"\caption{Held-out one-step-ahead predictive log-density per step "
          r"(higher is better), mean and 95\% CI across units. OU is the "
          r"monostable model nested inside CHM; GBM is a black-box reference "
          r"that produces no thresholds, no hysteresis width and no exponents.}")
        A(r"\label{tab:comparison}")
        A(r"\centering")
        A(r"\begin{tabular}{@{}lrr@{}}")
        A(r"\toprule")
        A(r"Model & Log-density & 95\% CI \\")
        A(r"\midrule")
        for m in models:
            mu, lo, hi = _ci(e4[m])
            nm = r"\textbf{CHM (ours)}" if m == "CHM" else m
            val = f"\\textbf{{{mu:+.3f}}}" if m == "CHM" else f"{mu:+.3f}"
            A(f"{nm} & {val} & $[{lo:+.3f}, {hi:+.3f}]$ \\\\")
        A(r"\bottomrule")
        A(r"\end{tabular}")
        A(r"\end{table}")
        A("")

    # E12 -- the early-warning estimator validation
    e12 = _load("e12_ews_validation.csv")
    if e12 is not None and len(e12):
        roll = e12[~e12["estimator"].str.startswith("theory")]
        th = e12[e12["estimator"].str.startswith("theory")]
        A(r"\begin{table}[t]")
        A(r"\caption{Can the standard early-warning estimator recover the "
          r"exponent, on series simulated from a model that genuinely contains "
          r"a fold? The theory reproduces its own exponent; every "
          r"rolling-window configuration returns the wrong sign.}")
        A(r"\label{tab:ewsval}")
        A(r"\centering")
        A(r"\begin{tabular}{@{}llrrr@{}}")
        A(r"\toprule")
        A(r"Estimator & Detrend & Window & Predicted & Median \\")
        A(r"\midrule")
        if len(th):
            r = th.iloc[0]
            A(r"theory $\lambda(\mu)$ & --- & --- & $+0.50$ & "
              f"$\\mathbf{{{r['median']:+.3f}}}$ \\\\")
            A(r"\midrule")
        for _, r in roll.sort_values(["estimator", "detrend", "window"]).iterrows():
            name = (r"rolling $-\log$AC1" if "AC1" in r["estimator"]
                    else "rolling variance")
            d = "yes" if r["detrend"] else "no"
            A(f"{name} & {d} & {int(r['window'])} & "
              f"${r['predicted']:+.2f}$ & ${r['median']:+.3f}$ \\\\")
        A(r"\bottomrule")
        A(r"\end{tabular}")
        A(r"\end{table}")
        A("")

    # E0 -- power and size
    e0 = _load("e0_power_size.csv")
    if e0 is not None and len(e0):
        A(r"\begin{table}[t]")
        A(r"\caption{Test size and power at the sample sizes the corpora "
          r"provide. The nominal test would have found a genuine cusp, but it "
          r"also finds one in over 40\% of random walks; calibration restores "
          r"size at some cost in power against weak dynamics.}")
        A(r"\label{tab:powersize}")
        A(r"\centering")
        A(r"\begin{tabular}{@{}lrrr@{}}")
        A(r"\toprule")
        A(r"Input & $n$ & Nominal & Calibrated \\")
        A(r"\midrule")
        for _, r in e0.sort_values(["regime", "n"]).iterrows():
            cal = ("---" if not np.isfinite(r["reject_calibrated"])
                   else f"{r['reject_calibrated']:.2f}")
            A(f"{r['regime']} & {int(r['n'])} & "
              f"{r['reject_nominal']:.2f} & {cal} \\\\")
        A(r"\bottomrule")
        A(r"\end{tabular}")
        A(r"\end{table}")
        A("")

    # predictions summary
    A(r"\begin{table}[t]")
    A(r"\caption{Pre-stated predictions and outcomes. Exponents are compared "
      r"against their theoretical values by bootstrap confidence interval.}")
    A(r"\label{tab:predictions}")
    A(r"\centering")
    A(r"\begin{tabular}{@{}llll@{}}")
    A(r"\toprule")
    A(r"ID & Prediction & Predicted & Observed \\")
    A(r"\midrule")

    j = RESULTS / f"scaling_p1_cfg{cfg}.json"
    if j.exists():
        sc = json.loads(j.read_text())
        if "exponent" in sc:
            A(f"P1 & hysteresis width & $3/2$ & "
              f"${sc['exponent']:.2f}\\ [{sc['ci_lo']:.2f}, {sc['ci_hi']:.2f}]$ \\\\")
        else:
            A(r"P1 & hysteresis width & $3/2$ & insufficient data \\")

    e6 = _load(f"e6_ews_cfg{cfg}.csv")
    if e6 is not None:
        for col, pred, lab in (("var_exponent", "-1/2", "EWS variance"),
                               ("ac1_exponent", "+1/2", r"EWS $-\log$AC1")):
            v = e6[col].dropna() if col in e6.columns else pd.Series(dtype=float)
            if len(v):
                mu, lo, hi = _ci(v)
                A(f"P2 & {lab} & ${pred}$ & "
                  f"${mu:+.2f}\\ [{lo:+.2f}, {hi:+.2f}]$ \\\\")

    e7 = _load(f"e7_dwell_cfg{cfg}.csv")
    if e7 is not None and len(e7):
        g = e7[e7["state"] == "overloaded"]
        if len(g):
            mu, lo, hi = _ci(g["overdispersion"])
            A(f"P3 & dwell over-dispersion & $>0$ & "
              f"${mu:+.2f}\\ [{lo:+.2f}, {hi:+.2f}]$ \\\\")
    A(r"\bottomrule")
    A(r"\end{tabular}")
    A(r"\end{table}")

    (TABLES / "results_tables.tex").write_text("\n".join(L), encoding="utf-8")
    print(f"  wrote paper/tables/results_tables.tex")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="B")
    args = ap.parse_args()
    txt = summarise(args.config)
    print(txt)
    (RESULTS / f"SUMMARY_cfg{args.config}.txt").write_text(txt, encoding="utf-8")
    latex_tables(args.config)


if __name__ == "__main__":
    main()
