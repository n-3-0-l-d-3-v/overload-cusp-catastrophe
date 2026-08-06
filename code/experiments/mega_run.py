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
points, at 2000 to roughly 1.1, and at 5000 to 0.7. Claims of the form "size is
0.42, not 0.05" deserve the tighter number, so we pay for it in compute rather
than hedge in prose.

Execution model
---------------
An earlier version dispatched every replicate to joblib in one call and lost a
six-hour run to a `TerminatedWorkerError` partway through the third block. Two
causes, both fixed here.

*BLAS oversubscription.* Each loky worker spawned its own OpenMP/MKL thread
pool, so eleven workers on a twelve-thread machine asked for well over a
hundred threads. The thread-limit environment variables are now set before
numpy is imported, which is the only point at which they take effect.

*No checkpointing.* Work is now split into chunks. Each chunk runs in a fresh
worker pool, appends its rows to a partial CSV and records itself as done, so a
crash costs one chunk rather than the whole block and `--resume` picks up where
it stopped. A chunk that dies is bisected and retried, which isolates a single
poison replicate instead of discarding several hundred good ones.

Usage
-----
    python code/experiments/mega_run.py --block all --resume
    python code/experiments/mega_run.py --block size
    python code/experiments/mega_run.py --block all --rep-scale 0.1   # smoke test

Every block writes `m<k>_*_raw.csv` and `m<k>_*_summary.csv` into results/.
Checkpoints live in results/_checkpoints/ and are not part of the artefact.

Blocks
------
recovery    parameter recovery, randomised truth, 6 series lengths
size        test size on random walks, nominal vs surrogate-calibrated
power       power on genuine cusps, 6 lengths x 4 effect regimes
persistence size vs AR(1) persistence, both surrogate ensembles
ews         early-warning estimator validation against closed-form ground truth
noise       robustness of the null to noise level and driver strength
"""

from __future__ import annotations

import os

# Must precede the numpy import: these are read once, when the native
# libraries are first loaded. Each worker process gets one BLAS thread, and
# parallelism comes from the process pool instead. Setting them afterwards is
# silently ineffective, which is what bit the previous run.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse                                                  # noqa: E402
import json                                                      # noqa: E402
import sys                                                       # noqa: E402
import time                                                      # noqa: E402
import warnings                                                  # noqa: E402
from pathlib import Path                                         # noqa: E402

import numpy as np                                               # noqa: E402
from scipy.stats import spearmanr                                # noqa: E402
import pandas as pd                                              # noqa: E402
from joblib import Parallel, delayed                             # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import potential as P                                   # noqa: E402
from chm import ews as E                                         # noqa: E402
from chm.model import CHMParams, simulate                        # noqa: E402
from chm.estimate import fit_mle, rw_surrogate_test              # noqa: E402

RESULTS = Path(__file__).resolve().parents[2] / "results"
RESULTS.mkdir(exist_ok=True, parents=True)
CKPT = RESULTS / "_checkpoints"
CKPT.mkdir(exist_ok=True, parents=True)

SEED = 20260722
N_JOBS = 10                      # 6 physical cores; leaves headroom for the OS

# Replication counts. Chosen so the Monte Carlo SE on a proportion is under
# 0.01 for the headline claims (size, power) and under 0.02 elsewhere.
REP_RECOVERY = 2000
REP_SIZE = 5000
REP_POWER = 2000
REP_PERSIST = 1000
REP_EWS = 500
REP_NOISE = 1000
N_SURR = 200                     # surrogates inside each calibrated test

# Chunk sizes, picked so one chunk is roughly one to three minutes of wall
# time. Surrogate-calibrated jobs cost ~N_SURR fits each and get small chunks;
# the cheap blocks get large ones so checkpoint overhead stays negligible.
CHUNK_SURR = 400
CHUNK_CHEAP = 2500

LENGTHS = (100, 150, 200, 300, 500, 1000)
PHIS = (0.0, 0.3, 0.5, 0.7, 0.85, 0.95, 0.98, 0.995, 1.0)

REGIMES = {
    "strong":   dict(alpha0=1.5, alpha_A=0.6, lam=0.20, sigma=0.30),
    "moderate": dict(alpha0=1.0, alpha_A=0.4, lam=0.10, sigma=0.25),
    "weak":     dict(alpha0=0.6, alpha_A=0.2, lam=0.05, sigma=0.20),
    "marginal": dict(alpha0=0.4, alpha_A=0.1, lam=0.03, sigma=0.20),
}

REP_SCALE = 1.0                  # overridden by --rep-scale


def reps(base):
    """Replication count after --rep-scale, never below one."""
    return max(1, int(round(base * REP_SCALE)))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fmt_dur(s):
    s = int(s)
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m{s % 60:02d}s"
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


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
# chunked, checkpointed executor
# --------------------------------------------------------------------------- #
def _safe(worker, job):
    """Never let one bad replicate take down a chunk."""
    try:
        return worker(*job)
    except Exception:
        return None


def _run_batch(worker, jobs, n_jobs):
    """
    Run a batch, bisecting on worker death.

    A `TerminatedWorkerError` means a worker process was killed -- segfault in
    a native library, or the OS reclaiming memory. joblib cannot tell us which
    replicate did it, so we halve the batch and retry. A single poison job is
    isolated in log2(len(jobs)) passes and returned as None; everything around
    it survives.
    """
    if not jobs:
        return []
    try:
        with Parallel(n_jobs=min(n_jobs, len(jobs)), backend="loky",
                      max_nbytes=None, batch_size=1) as par:
            return list(par(delayed(_safe)(worker, j) for j in jobs))
    except Exception as exc:
        if len(jobs) == 1:
            log(f"      dropped one replicate: {type(exc).__name__}")
            return [None]
        mid = len(jobs) // 2
        log(f"      worker died on {len(jobs)} jobs "
            f"({type(exc).__name__}); bisecting")
        return (_run_batch(worker, jobs[:mid], n_jobs)
                + _run_batch(worker, jobs[mid:], n_jobs))


def run_chunked(name, worker, jobs, chunk=CHUNK_SURR, resume=True):
    """
    Execute `jobs` in checkpointed chunks and return the collected rows.

    State lives in two files. `<name>.json` records which chunk indices are
    finished and the job-list fingerprint they belong to; `<name>_partial.csv`
    holds the rows produced so far. Changing the replication count changes the
    fingerprint, which invalidates the checkpoint rather than silently mixing
    two different runs.
    """
    state_f = CKPT / f"{name}.json"
    part_f = CKPT / f"{name}_partial.csv"
    total = len(jobs)
    n_chunks = (total + chunk - 1) // chunk
    fingerprint = f"{total}:{chunk}:{N_SURR}:{SEED}"

    state = {"fingerprint": fingerprint, "done": []}
    if resume and state_f.exists():
        try:
            prev = json.loads(state_f.read_text())
            if prev.get("fingerprint") == fingerprint:
                state = prev
                log(f"   resuming {name}: {len(state['done'])}/{n_chunks} "
                    f"chunks already done")
            else:
                log(f"   {name}: checkpoint is for a different job set, "
                    f"starting over")
                part_f.unlink(missing_ok=True)
        except Exception:
            part_f.unlink(missing_ok=True)
    else:
        part_f.unlink(missing_ok=True)

    done = set(state["done"])
    t0 = time.time()
    completed_now = 0

    for ci in range(n_chunks):
        if ci in done:
            continue
        rows = [r for r in _run_batch(worker, jobs[ci * chunk:(ci + 1) * chunk],
                                      N_JOBS) if r]
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(part_f, mode="a", header=not part_f.exists(), index=False)
        done.add(ci)
        state["done"] = sorted(done)
        state_f.write_text(json.dumps(state))

        completed_now += 1
        remaining = n_chunks - len(done)
        rate = (time.time() - t0) / completed_now
        log(f"   {name}: chunk {len(done)}/{n_chunks} "
            f"({100 * len(done) / n_chunks:.0f}%), "
            f"eta {fmt_dur(rate * remaining)}")

    if not part_f.exists():
        return pd.DataFrame()
    return pd.read_csv(part_f)


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
    out = {"n": n}
    for k in ("beta0", "beta_S", "beta_T", "beta_U", "alpha0", "alpha_A",
              "lam", "sigma", "eps"):
        out[f"true_{k}"] = getattr(true, k)
        out[f"est_{k}"] = getattr(est, k)
    return out


def block_recovery(resume=True):
    R = reps(REP_RECOVERY)
    log(f"RECOVERY: {R} reps x {len(LENGTHS)} lengths")
    jobs = [(SEED + 100000 * i + j, n)
            for i, n in enumerate(LENGTHS) for j in range(R)]
    df = run_chunked("m1_recovery", _one_recovery, jobs,
                     chunk=CHUNK_CHEAP, resume=resume)
    if df.empty:
        return df
    df.to_csv(RESULTS / "m1_recovery_raw.csv", index=False)

    rows = []
    for n in LENGTHS:
        d = df[df["n"] == n]
        for k in ("beta0", "beta_S", "beta_T", "beta_U", "alpha0", "alpha_A",
                  "lam", "sigma", "eps"):
            t, e = d[f"true_{k}"], d[f"est_{k}"]
            m = np.isfinite(t) & np.isfinite(e)
            t, e = t[m], e[m]
            if len(t) < 3:
                continue
            # Pearson and Spearman answer different questions here, and the
            # gap between them is itself a result. The geometry parameters are
            # ratios with a near-zero denominator, so their sampling
            # distribution is heavy-tailed: at n=1000 the recovered alpha0
            # spans [-140, 3.3] while its 99th percentile is 2.0. One blow-up
            # is enough to drag Pearson from 0.88 to 0.10. Pearson therefore
            # measures whether the estimate can be read as a number; Spearman
            # measures whether the ordering survives. Reporting only one of
            # them would overstate the result in one direction or the other.
            rows.append({
                "n": n, "param": k, "n_rep": int(len(t)),
                "bias": float((e - t).mean()),
                "rmse": float(np.sqrt(((e - t) ** 2).mean())),
                "corr": float(np.corrcoef(t, e)[0, 1]) if t.std() > 0 else np.nan,
                "spearman": float(spearmanr(t, e).statistic) if t.std() > 0 else np.nan,
                "p99_abs_est": float(np.percentile(np.abs(e), 99)),
                "max_abs_est": float(np.abs(e).max()),
            })
    s = pd.DataFrame(rows)
    s.to_csv(RESULTS / "m1_recovery_summary.csv", index=False)
    at200 = s[s["n"] == 200].set_index("param")["corr"]
    log("   n=200 recovery: " + ", ".join(
        f"{k}={at200.get(k, float('nan')):.2f}"
        for k in ("lam", "sigma", "alpha0", "alpha_A", "eps")))
    return s


def _one_size(seed, n, do_surrogate):
    rng = np.random.default_rng(seed)
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    x = np.cumsum(rng.standard_normal(n))
    x = (x - x.mean()) / (x.std() + 1e-12)
    f = fit_mle(x, S, T, U)
    row = {"n": n, "nominal": float(bool(f.get("lam_significant"))),
           "calibrated": np.nan}
    if do_surrogate:
        try:
            r = rw_surrogate_test(x, S, T, U, n_surr=N_SURR, rng=rng,
                                  statistics=("lam_t",))
            row["calibrated"] = float(r["lam_t"]["p"] < 0.05)
        except Exception:
            pass
    return row


def block_size(resume=True):
    R = reps(REP_SIZE)
    log(f"SIZE: {R} reps x {len(LENGTHS)} lengths "
        f"(calibrated on first {R // 4})")
    jobs = [(SEED + 1 + 100000 * i + j, n, j < R // 4)
            for i, n in enumerate(LENGTHS) for j in range(R)]
    df = run_chunked("m2_size", _one_size, jobs, chunk=CHUNK_SURR, resume=resume)
    if df.empty:
        return df
    df.to_csv(RESULTS / "m2_size_raw.csv", index=False)

    rows = []
    for n in LENGTHS:
        d = df[df["n"] == n]
        kn, nn = int(d["nominal"].sum()), len(d)
        c = d["calibrated"].dropna()
        kc, nc = int(c.sum()), len(c)
        lo_n, hi_n = wilson(kn, nn)
        lo_c, hi_c = wilson(kc, nc)
        rows.append({"n": n, "n_rep_nominal": nn,
                     "size_nominal": kn / nn if nn else np.nan,
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


def block_power(resume=True):
    R = reps(REP_POWER)
    log(f"POWER: {R} reps x {len(LENGTHS)} lengths x {len(REGIMES)} regimes")
    jobs = [(SEED + 2 + 1000000 * i + 1000 * ri + j, n, name, kw)
            for i, n in enumerate(LENGTHS)
            for ri, (name, kw) in enumerate(REGIMES.items())
            for j in range(R)]
    df = run_chunked("m3_power", _one_power, jobs, chunk=CHUNK_SURR,
                     resume=resume)
    if df.empty:
        return df
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


def block_persistence(resume=True):
    R = reps(REP_PERSIST)
    log(f"PERSISTENCE: {R} reps x {len(PHIS)} phi values, both ensembles")
    jobs = [(SEED + 3 + 100000 * i + j, phi)
            for i, phi in enumerate(PHIS) for j in range(R)]
    df = run_chunked("m4_persistence", _one_persist, jobs,
                     chunk=CHUNK_SURR // 2, resume=resume)
    if df.empty:
        return df
    df.to_csv(RESULTS / "m4_persistence_raw.csv", index=False)

    rows = []
    for phi in PHIS:
        d = df[df["phi"] == phi]
        if not len(d):
            continue
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


def block_ews(resume=True):
    R = reps(REP_EWS)
    lengths = (1500, 6000, 20000)
    windows = (20, 30, 60, 120, 240)
    log(f"EWS: {R} reps x {len(lengths)} lengths x {len(windows)} windows x 2")
    jobs = [(SEED + 4 + 1000000 * i + 10000 * wi + 10 * int(d) + j, n, w, d)
            for i, n in enumerate(lengths)
            for wi, w in enumerate(windows)
            for d in (False, True)
            for j in range(R)]
    df = run_chunked("m5_ews", _one_ews, jobs, chunk=CHUNK_CHEAP // 2,
                     resume=resume)
    if df.empty:
        return df
    df.to_csv(RESULTS / "m5_ews_raw.csv", index=False)

    rows = []
    for n in lengths:
        for w in windows:
            for d in (False, True):
                sub = df[(df["n"] == n) & (df["window"] == w)
                         & (df["detrend"] == d)]
                if not len(sub):
                    continue
                for est, pred in (("theory", 0.5), ("ac1", 0.5),
                                  ("variance", -0.5)):
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
    log(f"   theory median exponent {th['median'].median():+.3f} "
        f"(predicted +0.500)")
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


def block_noise(resume=True):
    R = reps(REP_NOISE)
    sigmas = (0.10, 0.20, 0.30, 0.45, 0.60)
    drives = (0.5, 1.0, 1.5)
    log(f"NOISE: {R} reps x {len(sigmas)} sigmas x {len(drives)} drives")
    jobs = [(SEED + 5 + 100000 * i + 1000 * di + j, sg, dr)
            for i, sg in enumerate(sigmas)
            for di, dr in enumerate(drives)
            for j in range(R)]
    df = run_chunked("m6_noise", _one_noise, jobs, chunk=CHUNK_SURR,
                     resume=resume)
    if df.empty:
        return df
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
          "persistence": block_persistence, "ews": block_ews,
          "noise": block_noise}

# Cheapest first, so a run that is interrupted early still leaves the blocks
# the paper depends on most heavily in a finished state.
ORDER = ["recovery", "size", "ews", "noise", "persistence", "power"]


def main():
    global REP_SCALE
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", default="all",
                    help="all, or comma-separated: " + ",".join(BLOCKS))
    ap.add_argument("--rep-scale", type=float, default=1.0,
                    help="scale every replication count (0.02 for a smoke test)")
    ap.add_argument("--resume", action="store_true",
                    help="reuse checkpoints from an interrupted run")
    ap.add_argument("--jobs", type=int, default=N_JOBS)
    args = ap.parse_args()

    REP_SCALE = args.rep_scale
    globals()["N_JOBS"] = args.jobs
    names = ORDER if args.block == "all" else args.block.split(",")

    t0 = time.time()
    log(f"mega_run starting: blocks {names}, {args.jobs} workers, "
        f"rep-scale {REP_SCALE}, N_SURR {N_SURR}")
    for nm in names:
        if nm not in BLOCKS:
            log(f"   unknown block {nm}, skipping")
            continue
        t = time.time()
        try:
            BLOCKS[nm](resume=args.resume)
            log(f"   {nm} finished in {fmt_dur(time.time() - t)}")
        except Exception as exc:
            # One block failing must not cost the blocks after it.
            log(f"   {nm} FAILED after {fmt_dur(time.time() - t)}: "
                f"{type(exc).__name__}: {exc}")
    log(f"ALL DONE in {fmt_dur(time.time() - t0)} -> {RESULTS}")


if __name__ == "__main__":
    main()
