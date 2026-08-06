"""
mega_run.py
===========
High-replication Monte Carlo suite. Everything the paper claims about the
estimator's behaviour is settled here, at replication counts high enough that
the Monte Carlo standard error on a rejection rate is under one percentage
point.

Why the scale matters. A rejection rate estimated from 40 replicates carries a
Monte Carlo standard error of about 3.5 points near p = 0.5, which is the same
order as the effects being reported. At 500 replicates that falls to about 2.2
points, and at 2000 to roughly 1.1. Claims of the form "size is 0.42, not 0.05"
deserve the tighter number, so we pay for it in compute rather than hedge in
prose.

Runs on all cores via joblib. Each block writes its own CSV so a partial run
still leaves usable output.

    python experiments/mega_run.py --block all
    python experiments/mega_run.py --block size      # just one block

Blocks
------
recovery    parameter recovery, 600 replicates over randomised truth
size        test size on random walks, 2000 replicates x 6 lengths
power       power on genuine cusps, 600 replicates x 6 lengths x 4 regimes
persistence size vs AR(1) persistence, 400 replicates x 9 phi values
ews         early-warning estimator validation, 200 replicates x full grid
noise       robustness of the null to noise level and driver strength
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import potential as P                                   # noqa: E402
from chm import ews as E                                         # noqa: E402
from chm.model import CHMParams, simulate                        # noqa: E402
from chm.estimate import fit_mle, rw_surrogate_test              # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
RESULTS.mkdir(exist_ok=True, parents=True)

SEED = 20260722
N_JOBS = -2                      # all cores but one, keeps the machine usable

# Replication counts. Chosen so Monte Carlo SE on a proportion is < 0.012.
REP_RECOVERY = 600
REP_SIZE = 2000
REP_POWER = 600
REP_PERSIST = 400
REP_EWS = 200
REP_NOISE = 400
N_SURR = 200                     # surrogates inside each calibrated test

LENGTHS = (100, 150, 200, 300, 500, 1000)
PHIS = (0.0, 0.3, 0.5, 0.7, 0.85, 0.95, 0.98, 0.995, 1.0)

REGIMES = {
    "strong":   dict(alpha0=1.5, alpha_A=0.6, lam=0.20, sigma=0.30),
    "moderate": dict(alpha0=1.0, alpha_A=0.4, lam=0.10, sigma=0.25),
    "weak":     dict(alpha0=0.6, alpha_A=0.2, lam=0.05, sigma=0.20),
    "marginal": dict(alpha0=0.4, alpha_A=0.1, lam=0.03, sigma=0.20),
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def smooth(n, rng, k=25):
    z = rng.standard_normal(n + k)
    s = np.convolve(z, np.ones(k) / k, mode="valid")[:n]
    return (s - s.mean()) / (s.std() + 1e-9)


def ar1(n, phi, rng):
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0]
    sd = np.sqrt(max(1 - phi**2, 1e-6)) if phi < 1 else 1.0
    for t in range(1, n):
        x[t] = phi * x[t - 1] + sd * e[t]
    s = x.std()
    return (x - x.mean()) / (s if s > 1e-12 else 1.0)


def wilson(k, n, z=1.96):
    """Wilson score interval. Correct near 0 and 1, where Wald is not."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = p + z**2 / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((c - h) / d, (c + h) / d)


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #
def _one_recovery(seed, n):
    rng = np.random.default_rng(seed)
    true = CHMParams(
        beta0=rng.uniform(-0.4, 0.4), beta_S=rng.uniform(0.2, 0.9),
        beta_T=rng.uniform(0.0, 0.5), beta_U=rng.uniform(0.0, 0.4),
        alpha0=rng.uniform(0.3, 1.8), alpha_A=rng.uniform(0.1, 1.2),
        lam=rng.uniform(0.05, 0.28), sigma=rng.uniform(0.15, 0.45),
        eps=rng.uniform(0.01, 0.10),
    )
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    x = simulate(true, S, T, U, rng=rng)["x"]
    if not np.all(np.isfinite(x)):
        return None
    est = fit_mle(x, S, T, U)["params"]
    keys = ("beta0", "beta_S", "beta_T", "beta_U", "alpha0",
            "alpha_A", "lam", "sigma", "eps")
    return {"n": n, **{f"true_{k}": getattr(true, k) for k in keys},
            **{f"est_{k}": getattr(est, k) for k in keys}}


def block_recovery(rng_seed=SEED):
    log(f"RECOVERY: {REP_RECOVERY} reps x {len(LENGTHS)} lengths")
    jobs = [(rng_seed + 100000 * i + j, n)
            for i, n in enumerate(LENGTHS) for j in range(REP_RECOVERY)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_recovery)(s, n) for s, n in jobs)
    df = pd.DataFrame([r for r in out if r])
    df.to_csv(RESULTS / "m1_recovery_raw.csv", index=False)

    keys = ("beta0", "beta_S", "beta_T", "beta_U", "alpha0",
            "alpha_A", "lam", "sigma", "eps")
    rows = []
    for n in LENGTHS:
        d = df[df["n"] == n]
        for k in keys:
            t, e = d[f"true_{k}"], d[f"est_{k}"]
            m = np.isfinite(t) & np.isfinite(e)
            if m.sum() < 3:
                continue
            rows.append({"n": n, "param": k, "n_rep": int(m.sum()),
                         "bias": float((e[m] - t[m]).mean()),
                         "rmse": float(np.sqrt(((e[m] - t[m])**2).mean())),
                         "corr": float(np.corrcoef(t[m], e[m])[0, 1])})
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m1_recovery_summary.csv", index=False)
    if not len(s):
        log("   no summary rows (too few replicates)")
        return s
    big = s[s["n"] >= 500] if (s["n"] >= 500).any() else s
    log(f"   at n>={int(big['n'].min())}: mean |bias| "
        f"{big['bias'].abs().mean():.4f}, min corr {big['corr'].min():.3f}")
    return s


def _one_size(seed, n, surrogate):
    rng = np.random.default_rng(seed)
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    rw = np.cumsum(rng.standard_normal(n) * 0.2)
    sd = rw.std()
    rw = (rw - rw.mean()) / (sd if sd > 1e-12 else 1.0)
    f = fit_mle(rw, S, T, U)
    nominal = bool(f.get("lam_significant"))
    cal = np.nan
    if surrogate:
        try:
            r = rw_surrogate_test(rw, S, T, U, n_surr=N_SURR, rng=rng,
                                  statistics=("lam_t",))
            cal = float(r["lam_t"]["p"] < 0.05)
        except Exception:
            pass
    return {"n": n, "nominal": float(nominal), "calibrated": cal}


def block_size(rng_seed=SEED + 1):
    """Nominal size at full replication; calibrated on a large subsample."""
    log(f"SIZE: {REP_SIZE} reps x {len(LENGTHS)} lengths "
        f"(calibrated on first {REP_SIZE//4})")
    jobs = [(rng_seed + 100000 * i + j, n, j < REP_SIZE // 4)
            for i, n in enumerate(LENGTHS) for j in range(REP_SIZE)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_size)(s, n, sur) for s, n, sur in jobs)
    df = pd.DataFrame(out)
    df.to_csv(RESULTS / "m2_size_raw.csv", index=False)

    rows = []
    for n in LENGTHS:
        d = df[df["n"] == n]
        kn, nn = int(d["nominal"].sum()), len(d)
        c = d["calibrated"].dropna()
        kc, nc = int(c.sum()), len(c)
        lo_n, hi_n = wilson(kn, nn)
        lo_c, hi_c = wilson(kc, nc)
        rows.append({"n": n, "n_rep_nominal": nn, "size_nominal": kn / nn,
                     "ci_lo_nominal": lo_n, "ci_hi_nominal": hi_n,
                     "n_rep_calibrated": nc,
                     "size_calibrated": kc / nc if nc else np.nan,
                     "ci_lo_calibrated": lo_c, "ci_hi_calibrated": hi_c})
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m2_size_summary.csv", index=False)
    log(f"   nominal size {s['size_nominal'].mean():.3f}, "
        f"calibrated {s['size_calibrated'].mean():.3f} (target 0.05)")
    return s


def _one_power(seed, n, regime, kw):
    rng = np.random.default_rng(seed)
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    p = CHMParams(beta_S=0.6, beta_T=0.2, beta_U=0.1, eps=0.03, **kw)
    x = simulate(p, S, T, U, rng=rng)["x"]
    if not np.all(np.isfinite(x)):
        return None
    f = fit_mle(x, S, T, U)
    cal = np.nan
    try:
        r = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                              statistics=("lam_t",))
        cal = float(r["lam_t"]["p"] < 0.05)
    except Exception:
        pass
    return {"n": n, "regime": regime,
            "nominal": float(bool(f.get("lam_significant"))),
            "calibrated": cal}


def block_power(rng_seed=SEED + 2):
    log(f"POWER: {REP_POWER} reps x {len(LENGTHS)} lengths x {len(REGIMES)} regimes")
    jobs = [(rng_seed + 1000000 * i + 1000 * ri + j, n, name, kw)
            for i, n in enumerate(LENGTHS)
            for ri, (name, kw) in enumerate(REGIMES.items())
            for j in range(REP_POWER)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_power)(s, n, nm, kw) for s, n, nm, kw in jobs)
    df = pd.DataFrame([r for r in out if r])
    df.to_csv(RESULTS / "m3_power_raw.csv", index=False)

    rows = []
    for n in LENGTHS:
        for name in REGIMES:
            d = df[(df["n"] == n) & (df["regime"] == name)]
            if not len(d):
                continue
            c = d["calibrated"].dropna()
            kc, nc = int(c.sum()), len(c)
            lo, hi = wilson(kc, nc)
            rows.append({"n": n, "regime": name, "n_rep": len(d),
                         "power_nominal": float(d["nominal"].mean()),
                         "power_calibrated": kc / nc if nc else np.nan,
                         "ci_lo": lo, "ci_hi": hi})
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m3_power_summary.csv", index=False)
    for name in REGIMES:
        d = s[(s["regime"] == name) & (s["n"] == 200)]
        if len(d):
            log(f"   n=200 {name:9s}: calibrated power "
                f"{d['power_calibrated'].iloc[0]:.3f}")
    return s


def _one_persist(seed, phi, n=200):
    rng = np.random.default_rng(seed)
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    x = ar1(n, phi, rng)
    ac1 = float(np.corrcoef(x[:-1], x[1:])[0, 1])
    res = {"phi": phi, "ac1": ac1}
    for kind in ("rw", "iaaft"):
        try:
            r = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                                  statistics=("lam_t",), surrogate=kind)
            res[kind] = float(r["lam_t"]["p"] < 0.05)
        except Exception:
            res[kind] = np.nan
    return res


def block_persistence(rng_seed=SEED + 3):
    log(f"PERSISTENCE: {REP_PERSIST} reps x {len(PHIS)} phi values, both ensembles")
    jobs = [(rng_seed + 100000 * i + j, phi)
            for i, phi in enumerate(PHIS) for j in range(REP_PERSIST)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_persist)(s, phi) for s, phi in jobs)
    df = pd.DataFrame(out)
    df.to_csv(RESULTS / "m4_persistence_raw.csv", index=False)

    rows = []
    for phi in PHIS:
        d = df[df["phi"] == phi]
        row = {"phi": phi, "mean_ac1": float(d["ac1"].mean()), "n_rep": len(d)}
        for kind in ("rw", "iaaft"):
            v = d[kind].dropna()
            k, nn = int(v.sum()), len(v)
            lo, hi = wilson(k, nn)
            row[f"size_{kind}"] = k / nn if nn else np.nan
            row[f"ci_lo_{kind}"], row[f"ci_hi_{kind}"] = lo, hi
        rows.append(row)
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m4_persistence_summary.csv", index=False)
    log(f"   worst RW size {s['size_rw'].max():.3f}, "
        f"worst IAAFT {s['size_iaaft'].max():.3f}")
    return s


def _one_ews(seed, n, win, detr):
    rng = np.random.default_rng(seed)
    S, T, U = smooth(n, rng, 40), smooth(n, rng, 40), smooth(n, rng, 40)
    true = CHMParams(beta0=-0.05, beta_S=0.65, beta_T=0.25, beta_U=0.15,
                     alpha0=1.30, alpha_A=0.55, lam=0.18, sigma=0.30, eps=0.03)
    sim = simulate(true, S, T, U, rng=rng)
    x, a, b = sim["x"], sim["a"], sim["b"]
    if not np.all(np.isfinite(x)):
        return None
    mu = P.distance_to_fold(a, b)
    sad = P.saddle(a, b)
    lower = np.where(np.isnan(sad), x < 0, x < sad)

    def slope(xv, yv):
        m = np.isfinite(xv) & np.isfinite(yv) & (xv > 1e-3) & (yv > 0)
        if m.sum() < 30:
            return np.nan
        return float(np.polyfit(np.log(xv[m]), np.log(yv[m]), 1)[0])

    lo, _ = P.stable_equilibria(a, b)
    g_true = slope(mu, P.relaxation_rate(lo, a))

    y = E.detrend(x, win) if detr else x
    ac1 = E.rolling_ac1(y, win)
    nl = -np.log(np.clip(ac1, 1e-6, 0.999999))
    g_ac1 = slope(np.where(lower, mu, np.nan), np.where(lower, nl, np.nan))
    var = E.rolling_variance(y, win)
    g_var = slope(np.where(lower, mu, np.nan), np.where(lower, var, np.nan))

    return {"n": n, "window": win, "detrend": detr,
            "theory": g_true, "ac1": g_ac1, "variance": g_var}


def block_ews(rng_seed=SEED + 4):
    lengths = (1500, 6000, 20000)
    windows = (20, 30, 60, 120, 240)
    log(f"EWS: {REP_EWS} reps x {len(lengths)} lengths x {len(windows)} windows x 2")
    jobs = [(rng_seed + 1000000 * i + 10000 * wi + 10 * int(d) + j, n, w, d)
            for i, n in enumerate(lengths)
            for wi, w in enumerate(windows)
            for d in (False, True)
            for j in range(REP_EWS)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_ews)(s, n, w, d) for s, n, w, d in jobs)
    df = pd.DataFrame([r for r in out if r])
    df.to_csv(RESULTS / "m5_ews_raw.csv", index=False)

    rows = []
    for n in lengths:
        for w in windows:
            for d in (False, True):
                sub = df[(df["n"] == n) & (df["window"] == w) & (df["detrend"] == d)]
                if not len(sub):
                    continue
                for est, pred in (("theory", 0.5), ("ac1", 0.5), ("variance", -0.5)):
                    v = sub[est].dropna()
                    if not len(v):
                        continue
                    rows.append({
                        "n": n, "window": w, "detrend": d, "estimator": est,
                        "predicted": pred, "n_rep": len(v),
                        "median": float(v.median()), "mean": float(v.mean()),
                        "q025": float(v.quantile(0.025)),
                        "q975": float(v.quantile(0.975)),
                        "frac_correct_sign": float(
                            np.mean(np.sign(v) == np.sign(pred))),
                    })
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m5_ews_summary.csv", index=False)
    roll = s[s["estimator"] != "theory"]
    log(f"   rolling configs with correct median sign: "
        f"{int((np.sign(roll['median']) == np.sign(roll['predicted'])).sum())}"
        f"/{len(roll)}")
    th = s[s["estimator"] == "theory"]
    log(f"   theory median exponent {th['median'].median():+.3f} (predicted +0.500)")
    return s


def _one_noise(seed, sigma, drive_scale, n=200):
    rng = np.random.default_rng(seed)
    S, T, U = (smooth(n, rng) * drive_scale for _ in range(3))
    p = CHMParams(beta_S=0.6, beta_T=0.2, beta_U=0.1, alpha0=1.2,
                  alpha_A=0.5, lam=0.15, sigma=sigma, eps=0.03)
    x = simulate(p, S, T, U, rng=rng)["x"]
    if not np.all(np.isfinite(x)):
        return None
    try:
        r = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                              statistics=("lam_t",))
        return {"sigma": sigma, "drive_scale": drive_scale,
                "detected": float(r["lam_t"]["p"] < 0.05)}
    except Exception:
        return None


def block_noise(rng_seed=SEED + 5):
    sigmas = (0.10, 0.20, 0.30, 0.45, 0.60)
    drives = (0.5, 1.0, 1.5)
    log(f"NOISE: {REP_NOISE} reps x {len(sigmas)} sigmas x {len(drives)} drives")
    jobs = [(rng_seed + 100000 * i + 1000 * di + j, sg, dr)
            for i, sg in enumerate(sigmas)
            for di, dr in enumerate(drives)
            for j in range(REP_NOISE)]
    out = Parallel(n_jobs=N_JOBS, verbose=0)(
        delayed(_one_noise)(s, sg, dr) for s, sg, dr in jobs)
    df = pd.DataFrame([r for r in out if r])
    df.to_csv(RESULTS / "m6_noise_raw.csv", index=False)

    rows = []
    for sg in sigmas:
        for dr in drives:
            d = df[(df["sigma"] == sg) & (df["drive_scale"] == dr)]
            if not len(d):
                continue
            k, nn = int(d["detected"].sum()), len(d)
            lo, hi = wilson(k, nn)
            rows.append({"sigma": sg, "drive_scale": dr, "n_rep": nn,
                         "detection_rate": k / nn, "ci_lo": lo, "ci_hi": hi})
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m6_noise_summary.csv", index=False)
    log(f"   detection range {s['detection_rate'].min():.3f} to "
        f"{s['detection_rate'].max():.3f}")
    return s


BLOCKS = {"recovery": block_recovery, "size": block_size, "power": block_power,
          "persistence": block_persistence, "ews": block_ews, "noise": block_noise}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", default="all",
                    help="all, or comma-separated: " + ",".join(BLOCKS))
    args = ap.parse_args()
    names = list(BLOCKS) if args.block == "all" else args.block.split(",")

    t0 = time.time()
    log(f"mega_run starting: blocks {names}, {N_JOBS} job slots")
    for nm in names:
        if nm not in BLOCKS:
            log(f"   unknown block {nm}, skipping")
            continue
        t = time.time()
        BLOCKS[nm]()
        log(f"   {nm} finished in {time.time()-t:.0f}s")
    log(f"ALL DONE in {time.time()-t0:.0f}s -> {RESULTS}")


if __name__ == "__main__":
    main()
