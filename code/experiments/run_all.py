"""
run_all.py
==========
The full experimental protocol for the paper.  One command reproduces every
number, table and figure:

    python experiments/run_all.py --config A

Experiments
-----------
E1  Parameter recovery on simulated data (does the estimator work at all?)
E2  Per-subject CHM fits on all three corpora
E3  Bistability likelihood-ratio test with parametric-bootstrap null
E4  Held-out model comparison against five baselines
E5  Hysteresis: measured loop width vs the predicted a^{3/2} law   (P1)
E6  Early-warning scaling exponents vs the predicted -1/2 / +1/2   (P2)
E7  Dwell-time over-dispersion vs the geometric null               (P3)
E8  Re-entry hazard after recovery                                 (P4)
E9  External validation of derived states against protocol labels
E10 Prospective onset prediction (AUC at several lead times)

Everything is seeded.  Results land in results/ as CSV and JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import potential as P                                   # noqa: E402
from chm import ews as E                                         # noqa: E402
from chm import baselines as B                                   # noqa: E402
from chm import datasets as D                                    # noqa: E402
from chm.model import CHMParams, simulate, STATES                # noqa: E402
from chm.estimate import (fit_mle, fit_monostable, lrt_bistability,   # noqa: E402
                          rw_surrogate_test, latent_path,
                          one_step_predictive_loglik)
from chm.states import (assign_states, empirical_transition_matrix,    # noqa: E402
                        dwell_times, STATE_INDEX)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT.parent / "results"
RESULTS.mkdir(exist_ok=True, parents=True)

SEED = 20260722
EWS_WIN = 30            # rolling window for the indicators (samples)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _smooth_noise(n, rng, k=25):
    z = rng.standard_normal(n + k)
    s = np.convolve(z, np.ones(k) / k, mode="valid")[:n]
    return (s - s.mean()) / (s.std() + 1e-9)


# --------------------------------------------------------------------------- #
# E1  parameter recovery
# --------------------------------------------------------------------------- #
def e1_parameter_recovery(n_reps=30, n=4000, seed=SEED):
    log("E1  parameter recovery")
    rng = np.random.default_rng(seed)
    keys = ["beta0", "beta_S", "beta_T", "beta_U", "alpha0", "alpha_A",
            "lam", "sigma", "eps"]
    rows = []
    for r in range(n_reps):
        true = CHMParams(
            beta0=rng.uniform(-0.4, 0.4), beta_S=rng.uniform(0.2, 0.9),
            beta_T=rng.uniform(0.0, 0.5), beta_U=rng.uniform(0.0, 0.4),
            alpha0=rng.uniform(0.3, 1.8), alpha_A=rng.uniform(0.1, 1.2),
            lam=rng.uniform(0.10, 0.28), sigma=rng.uniform(0.20, 0.45),
            eps=rng.uniform(0.01, 0.08),
        )
        S, T, U = (_smooth_noise(n, rng) for _ in range(3))
        x = simulate(true, S, T, U, rng=rng)["x"]
        if not np.all(np.isfinite(x)):
            continue
        est = fit_mle(x, S, T, U)["params"]
        for k in keys:
            rows.append({"rep": r, "param": k,
                         "true": getattr(true, k), "est": getattr(est, k)})

    df = pd.DataFrame(rows)
    summ = []
    for k in keys:
        d = df[df["param"] == k]
        summ.append({
            "param": k,
            "bias": float((d["est"] - d["true"]).mean()),
            "rmse": float(np.sqrt(((d["est"] - d["true"]) ** 2).mean())),
            "corr": float(np.corrcoef(d["true"], d["est"])[0, 1]),
            "n": int(len(d)),
        })
    out = pd.DataFrame(summ)
    df.to_csv(RESULTS / "e1_recovery_raw.csv", index=False)
    out.to_csv(RESULTS / "e1_recovery_summary.csv", index=False)
    log(f"     mean |bias| = {out['bias'].abs().mean():.4f}, "
        f"min corr = {out['corr'].min():.3f}")
    return out


# --------------------------------------------------------------------------- #
# E2  per-unit fits
# --------------------------------------------------------------------------- #
def fit_unit(frame, rng, n_restarts=6):
    """Fit the CHM to one subject/session and derive its state sequence."""
    x = frame["x"].to_numpy(float)
    S = frame["S"].to_numpy(float)
    T = frame["T"].to_numpy(float)
    U = frame["U"].to_numpy(float)

    res = fit_mle(x, S, T, U)
    p = res["params"]

    # If the th1 >= 0 constraint was active, lam = 0 and the structural
    # parameters are undefined (a = th2/th1).  Such units are NOT dropped:
    # dropping them would retain only units where a cusp happened to be found,
    # which is exactly the survivorship bias that would manufacture a positive
    # result.  They are carried through with geometry marked unavailable and
    # counted in the denominator of every reported proportion.
    if not res.get("cusp_identified") or not np.isfinite(p.alpha0):
        nan = np.full(len(x), np.nan)
        return {"fit": res, "params": p, "A": nan, "a": nan, "b": nan,
                "states": np.array([""] * len(x), dtype="<U10"),
                "x": x, "S": S, "T": T, "U": U, "identified": False}

    A, a, b = latent_path(x, S, T, U, p)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        nan = np.full(len(x), np.nan)
        return {"fit": res, "params": p, "A": nan, "a": nan, "b": nan,
                "states": np.array([""] * len(x), dtype="<U10"),
                "x": x, "S": S, "T": T, "U": U, "identified": False}

    st = assign_states(x, a, b)
    return {"fit": res, "params": p, "A": A, "a": a, "b": b,
            "states": st, "x": x, "S": S, "T": T, "U": U, "identified": True}


def e2_fit_all(frames, rng, tag):
    log(f"E2  fitting {len(frames)} units [{tag}]")
    out = []
    for fr in frames:
        try:
            u = fit_unit(fr, rng)
        except Exception as e:
            log(f"     skip {fr['subject'].iloc[0]}: {e}")
            continue
        p = u["params"]
        st = u["states"]
        out.append({
            "unit": u, "frame": fr,
            "row": {
                "dataset": fr["dataset"].iloc[0],
                "subject": str(fr["subject"].iloc[0]),
                "n": len(fr),
                **{k: getattr(p, k) for k in
                   ("beta0", "beta_S", "beta_T", "beta_U", "alpha0",
                    "alpha_A", "lam", "sigma", "eps")},
                "identified": bool(u.get("identified")),
                "mean_a": float(np.nanmean(u["a"])) if u.get("identified") else np.nan,
                "mean_b": float(np.nanmean(u["b"])) if u.get("identified") else np.nan,
                "pct_bistable": float(np.mean(P.is_bistable(u["a"], u["b"])))
                if u.get("identified") else np.nan,
                "nll": u["fit"]["nll"], "aic": u["fit"]["aic"],
                "cusp_identified": u["fit"].get("cusp_identified"),
                "lam_t": u["fit"].get("lam_t"),
                "lam_p_nominal": u["fit"].get("lam_p"),
                **{f"pct_{s}": float(np.mean(st == s)) for s in STATES},
            },
        })
    return out


# --------------------------------------------------------------------------- #
# E3  bistability test
# --------------------------------------------------------------------------- #
def e3_bistability(units, rng, n_boot=100, max_units=None):
    """
    Two nulls per unit.

    The nested monostable LRT is reported for completeness, but the
    random-walk surrogate test is the one that decides.  Tonic EDA is close to
    a unit-root process, and a random walk over a finite window looks bimodal
    and fits a flat-bottomed potential better than a single well.  Anything a
    random walk reproduces is not evidence.
    """
    log("E3  bistability: nested LRT + random-walk surrogate test")
    rows = []
    sel = units if max_units is None else units[:max_units]
    for u in sel:
        f, fr = u["unit"], u["frame"]
        row = {"dataset": fr["dataset"].iloc[0],
               "subject": str(fr["subject"].iloc[0])}
        try:
            r = lrt_bistability(f["x"], f["S"], f["T"], f["U"],
                                n_boot=n_boot, rng=rng)
            row.update({"lrt_stat": r["stat"], "p_nested": r["p"],
                        "alpha0_full": r["full"]["params"].alpha0,
                        "n_boot": r["n_boot"]})
        except Exception as e:
            log(f"     nested LRT failed for {row['subject']}: {e}")
        try:
            s = rw_surrogate_test(f["x"], f["S"], f["T"], f["U"],
                                  n_surr=n_boot, rng=rng)
            for k, v in s.items():
                row[f"{k}_obs"] = v["observed"]
                row[f"{k}_null_p95"] = v["null_p95"]
                row[f"p_rw_{k}"] = v["p"]
        except Exception as e:
            log(f"     RW surrogate failed for {row['subject']}: {e}")
        rows.append(row)
        log(f"     {row['subject']}: LR={row.get('lrt_stat', float('nan')):.1f} "
            f"p_nested={row.get('p_nested', float('nan')):.3f} "
            f"p_rw(LR)={row.get('p_rw_lr', float('nan')):.3f} "
            f"p_rw(bimod)={row.get('p_rw_bimodality', float('nan')):.3f}")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# E4  held-out model comparison
# --------------------------------------------------------------------------- #
def e4_model_comparison(units, rng, n_folds=5):
    log("E4  held-out model comparison")
    rows = []
    for u in units:
        f, fr = u["unit"], u["frame"]
        x, S, T, U = f["x"], f["S"], f["T"], f["U"]

        # The continuous-model comparison (CHM, OU, HMM, GBM) does NOT require
        # the cusp geometry to be identified -- it only needs the series. Only
        # the state-based baselines (Markov, Logistic) need a state sequence.
        # Restricting the whole comparison to identified units, as an earlier
        # version did, conditions the result on the outcome and reinstates
        # exactly the survivorship bias closed in e2_fit_all. Every unit is
        # scored here; state-based models are scored where states exist, and
        # the per-model n is reported alongside the mean.
        has_states = bool(f.get("identified")) and np.all(f["states"] != "")
        st_idx = (np.array([STATE_INDEX[s] for s in f["states"]], int)
                  if has_states else None)
        C = np.column_stack([S, T, U])
        n = len(x)
        if n < 200:
            continue

        folds = np.array_split(np.arange(n), n_folds)
        acc = {k: [] for k in ("CHM", "Markov", "Logistic", "HMM", "OU", "GBM")}

        for k in range(n_folds):
            te = folds[k]
            tr = np.setdiff1d(np.arange(n), te)
            if len(tr) < 100 or len(te) < 30:
                continue
            # contiguous blocks only, so the lag structure is preserved
            te = np.arange(te[0], te[-1] + 1)
            tr_x, te_x = x[tr], x[te]

            try:
                p_tr = fit_mle(tr_x, S[tr], T[tr], U[tr])["params"]
                acc["CHM"].append(
                    one_step_predictive_loglik(p_tr, te_x, S[te], T[te], U[te]))
            except Exception as e:
                log(f"     CHM failed: {e}")

            if st_idx is not None:
                try:
                    acc["Markov"].append(
                        B.markov_chain_loglik(st_idx[tr], st_idx[te]))
                except Exception as e:
                    log(f"     Markov failed: {e}")

                try:
                    Xtr = np.column_stack([C[tr][:-1],
                                           np.eye(5)[st_idx[tr][:-1]]])
                    Xte = np.column_stack([C[te][:-1],
                                           np.eye(5)[st_idx[te][:-1]]])
                    acc["Logistic"].append(
                        B.multinomial_logistic_loglik(Xtr, st_idx[tr][1:],
                                                      Xte, st_idx[te][1:]))
                except Exception as e:
                    log(f"     Logistic failed: {e}")

            try:
                acc["HMM"].append(B.hmm_loglik(
                    np.column_stack([tr_x, C[tr]]),
                    np.column_stack([te_x, C[te]]), n_components=5))
            except Exception as e:
                log(f"     HMM failed: {e}")

            try:
                acc["OU"].append(
                    B.ou_fit_predict(tr_x, C[tr], te_x, C[te])["loglik"])
            except Exception as e:
                log(f"     OU failed: {e}")

            try:
                Xtr = np.column_stack([tr_x[:-1], C[tr][:-1]])
                Xte = np.column_stack([te_x[:-1], C[te][:-1]])
                acc["GBM"].append(B.gbm_predict_loglik(
                    Xtr, tr_x[1:], Xte, te_x[1:])["loglik"])
            except Exception as e:
                log(f"     GBM failed: {e}")

        row = {"dataset": fr["dataset"].iloc[0],
               "subject": str(fr["subject"].iloc[0]),
               "identified": bool(f.get("identified"))}
        for m, v in acc.items():
            v = [q for q in v if np.isfinite(q)]
            row[m] = float(np.mean(v)) if v else np.nan
            # per-model fold count, so a baseline that quietly contributes
            # nothing shows up as a zero rather than as an absent column
            row[f"{m}_nfolds"] = len(v)
        rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# E5  hysteresis and the 3/2 law
# --------------------------------------------------------------------------- #
def e5_hysteresis(units):
    log("E5  hysteresis width vs the a^{3/2} law")
    rows = []
    for u in units:
        f, fr = u["unit"], u["frame"]
        if not f.get("identified"):
            continue
        a, b, st = f["a"], f["b"], f["states"]

        entry, exit_ = [], []
        up = np.isin(st, ["overloaded", "recovering"])
        for i in range(1, len(st)):
            if up[i] and not up[i - 1]:
                entry.append(b[i])
            elif up[i - 1] and not up[i]:
                exit_.append(b[i])

        if len(entry) >= 3 and len(exit_) >= 3:
            gap = float(np.mean(entry) - np.mean(exit_))
            t, p = stats.ttest_ind(entry, exit_, equal_var=False)
        else:
            gap, t, p = np.nan, np.nan, np.nan

        a_bar = float(np.mean(a[a > 0])) if np.any(a > 0) else np.nan
        predicted = float(P.hysteresis_width(np.array([a_bar]))[0]) \
            if np.isfinite(a_bar) else np.nan

        rows.append({
            "dataset": fr["dataset"].iloc[0],
            "subject": str(fr["subject"].iloc[0]),
            "n_entry": len(entry), "n_exit": len(exit_),
            "mean_entry_b": float(np.mean(entry)) if entry else np.nan,
            "mean_exit_b": float(np.mean(exit_)) if exit_ else np.nan,
            "observed_width": gap, "a_bar": a_bar,
            "predicted_width": predicted, "t": t, "p": p,
        })
    df = pd.DataFrame(rows)

    # the actual test of P1: does observed width scale as a^{3/2}?
    d = df.dropna(subset=["observed_width", "a_bar"])
    d = d[(d["a_bar"] > 0) & (d["observed_width"] > 0)]
    scaling = {"n": int(len(d))}
    if len(d) >= 6:
        lr = stats.linregress(np.log(d["a_bar"]), np.log(d["observed_width"]))
        boots = []
        rng = np.random.default_rng(SEED)
        idx = np.arange(len(d))
        la, lw = np.log(d["a_bar"].to_numpy()), np.log(d["observed_width"].to_numpy())
        for _ in range(2000):
            s = rng.choice(idx, len(idx), True)
            if np.std(la[s]) > 1e-9:
                boots.append(stats.linregress(la[s], lw[s]).slope)
        boots = np.array(boots)
        scaling.update({
            "exponent": float(lr.slope),
            "ci_lo": float(np.percentile(boots, 2.5)),
            "ci_hi": float(np.percentile(boots, 97.5)),
            "r2": float(lr.rvalue ** 2),
            "predicted": 1.5,
            "consistent": bool(np.percentile(boots, 2.5) <= 1.5
                               <= np.percentile(boots, 97.5)),
        })
    return df, scaling


# --------------------------------------------------------------------------- #
# E6  early-warning scaling exponents
# --------------------------------------------------------------------------- #
def e6_ews(units, rng, window=EWS_WIN):
    log("E6  early-warning scaling exponents")
    rows, exps = [], []
    for u in units:
        f, fr = u["unit"], u["frame"]
        if not f.get("identified"):
            continue
        x, a, b, st = f["x"], f["a"], f["b"], f["states"]
        xd = E.detrend(x, window)
        ac1 = E.rolling_ac1(xd, window)
        var = E.rolling_variance(xd, window)
        mu = P.distance_to_fold(a, b)

        v_fit = E.fit_scaling_exponent(mu, var, predicted=-0.5, rng=rng)
        neg_log_ac1 = -np.log(np.clip(ac1, 1e-6, 0.999999))
        a_fit = E.fit_scaling_exponent(mu, neg_log_ac1, predicted=0.5, rng=rng)

        onsets = E.onset_indices(st, "overloaded")
        aucs = {f"auc_lead{l}": E.lead_time_auc(var, onsets, len(x), l, rng=rng)["auc"]
                for l in (3, 6, 12)}

        tau_var, p_var, _ = E.surrogate_pvalue(
            var[np.isfinite(var)][-200:], E.kendall_tau_trend, n_surr=200,
            kind="ar1", rng=rng) if np.isfinite(var).sum() > 50 else (np.nan,) * 3

        rows.append({
            "dataset": fr["dataset"].iloc[0],
            "subject": str(fr["subject"].iloc[0]),
            "var_exponent": v_fit["gamma"], "var_ci_lo": v_fit["ci"][0],
            "var_ci_hi": v_fit["ci"][1], "var_r2": v_fit["r2"],
            "var_p_vs_pred": v_fit["p_vs_predicted"], "var_n": v_fit["n"],
            "ac1_exponent": a_fit["gamma"], "ac1_ci_lo": a_fit["ci"][0],
            "ac1_ci_hi": a_fit["ci"][1], "ac1_r2": a_fit["r2"],
            "ac1_p_vs_pred": a_fit["p_vs_predicted"], "ac1_n": a_fit["n"],
            "kendall_tau_var": tau_var, "kendall_p_surrogate": p_var,
            "n_onsets": len(onsets), **aucs,
        })
        exps.append((v_fit["gamma"], a_fit["gamma"]))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# E7 / E8  dwell times and re-entry hazard
# --------------------------------------------------------------------------- #
def e7_dwell(units):
    log("E7  dwell-time over-dispersion")
    rows = []
    for u in units:
        f, fr = u["unit"], u["frame"]
        if not f.get("identified"):
            continue
        st = f["states"]
        for target in ("overloaded", "stuck"):
            d = dwell_times(st, target)
            if d.size < 8:
                continue
            cv = float(d.std() / max(d.mean(), 1e-9))
            # geometric null with the same mean: CV = sqrt(1-p), p = 1/mean
            p_geom = 1.0 / max(d.mean(), 1.0 + 1e-9)
            cv_geom = float(np.sqrt(max(1 - p_geom, 0.0)))
            ks = stats.kstest(
                d, lambda q: 1 - (1 - p_geom) ** np.floor(np.maximum(q, 0)))
            rows.append({
                "dataset": fr["dataset"].iloc[0],
                "subject": str(fr["subject"].iloc[0]), "state": target,
                "n_episodes": int(d.size), "mean_dwell": float(d.mean()),
                "cv_observed": cv, "cv_geometric": cv_geom,
                "overdispersion": cv - cv_geom,
                "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
            })
    return pd.DataFrame(rows)


def e8_reentry(units):
    log("E8  re-entry hazard after recovery")
    rows = []
    for u in units:
        f, fr = u["unit"], u["frame"]
        if not f.get("identified"):
            continue
        st = np.asarray(f["states"])
        up = np.isin(st, ["overloaded", "recovering"])
        gaps = []
        last_exit = None
        for i in range(1, len(st)):
            if up[i - 1] and not up[i]:
                last_exit = i
            elif up[i] and not up[i - 1] and last_exit is not None:
                gaps.append(i - last_exit)
                last_exit = None
        gaps = np.array(gaps, float)
        if gaps.size >= 8:
            # exponential hazard: rate = 1/mean gap; report the fitted rate and
            # whether short gaps are over-represented relative to exponential
            rate = 1.0 / gaps.mean()
            ks = stats.kstest(gaps, "expon", args=(0, gaps.mean()))
            rows.append({
                "dataset": fr["dataset"].iloc[0],
                "subject": str(fr["subject"].iloc[0]),
                "n_gaps": int(gaps.size), "mean_gap": float(gaps.mean()),
                "median_gap": float(np.median(gaps)),
                "hazard_rate": float(rate),
                "ks_expon_p": float(ks.pvalue),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# E9  external validation against protocol labels
# --------------------------------------------------------------------------- #
def e9_external_validation(units):
    log("E9  external validation of derived states")
    rows = []
    for u in units:
        f, fr = u["unit"], u["frame"]
        if not f.get("identified") or "protocol" not in fr.columns:
            continue
        proto = fr["protocol"].to_numpy()[: len(f["states"])]
        st = f["states"][: len(proto)]
        keep = np.isin(proto, ["baseline", "stress", "amusement", "meditation"])
        if keep.sum() < 50:
            continue
        high = np.isin(st[keep], ["overloaded", "stuck", "recovering"])
        stressed = proto[keep] == "stress"
        if stressed.sum() < 5 or (~stressed).sum() < 5:
            continue
        tab = np.array([[np.sum(high & stressed), np.sum(high & ~stressed)],
                        [np.sum(~high & stressed), np.sum(~high & ~stressed)]])
        try:
            odds, p = stats.fisher_exact(tab)
        except Exception:
            odds, p = np.nan, np.nan
        rows.append({
            "dataset": fr["dataset"].iloc[0],
            "subject": str(fr["subject"].iloc[0]),
            "p_high_given_stress": float(high[stressed].mean()),
            "p_high_given_other": float(high[~stressed].mean()),
            "odds_ratio": float(odds), "fisher_p": float(p),
            "n": int(keep.sum()),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="B", choices=["A", "B", "C"],
                    help="sensor assignment (see chm.signals)")
    ap.add_argument("--datasets", default="WESAD,EXAM,NURSE")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--nurse-limit", type=int, default=60)
    ap.add_argument("--boot", type=int, default=100)
    ap.add_argument("--skip-e1", action="store_true")
    args = ap.parse_args()

    rng = np.random.default_rng(SEED)
    suffix = f"_cfg{args.config}"
    t0 = time.time()

    if not args.skip_e1:
        e1_parameter_recovery()

    all_units, meta = [], []
    for ds in args.datasets.split(","):
        lim = args.nurse_limit if ds == "NURSE" else args.limit
        log(f"loading {ds}")
        frames = D.prepare(ds, config=args.config, limit=lim)
        if not frames:
            log(f"     no data for {ds}; skipping")
            continue
        units = e2_fit_all(frames, rng, ds)
        all_units += units
        meta += [u["row"] for u in units]

    if not all_units:
        log("no units fitted -- check data/raw/")
        return

    pd.DataFrame(meta).to_csv(RESULTS / f"e2_fits{suffix}.csv", index=False)

    hyst, scaling = e5_hysteresis(all_units)
    hyst.to_csv(RESULTS / f"e5_hysteresis{suffix}.csv", index=False)

    e6_ews(all_units, rng).to_csv(RESULTS / f"e6_ews{suffix}.csv", index=False)
    e7_dwell(all_units).to_csv(RESULTS / f"e7_dwell{suffix}.csv", index=False)
    e8_reentry(all_units).to_csv(RESULTS / f"e8_reentry{suffix}.csv", index=False)
    e9_external_validation(all_units).to_csv(
        RESULTS / f"e9_validation{suffix}.csv", index=False)
    e4_model_comparison(all_units, rng).to_csv(
        RESULTS / f"e4_comparison{suffix}.csv", index=False)
    e3_bistability(all_units, rng, n_boot=args.boot).to_csv(
        RESULTS / f"e3_lrt{suffix}.csv", index=False)

    # aggregate transition matrix, for the figure
    mats = [empirical_transition_matrix(u["unit"]["states"])
            for u in all_units if u["unit"].get("identified")]
    agg = pd.DataFrame(np.mean(mats, axis=0) if mats else np.zeros((5, 5)),
                       index=STATES, columns=STATES)
    agg.to_csv(RESULTS / f"transition_matrix{suffix}.csv")

    with open(RESULTS / f"scaling_p1{suffix}.json", "w") as fh:
        json.dump(scaling, fh, indent=2)

    log(f"done in {time.time()-t0:.0f}s -> {RESULTS}")
    log(f"P1 hysteresis exponent: {scaling}")


if __name__ == "__main__":
    main()
