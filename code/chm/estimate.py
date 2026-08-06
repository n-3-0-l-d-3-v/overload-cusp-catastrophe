"""
chm.estimate
============
Estimation and inference for the CHM model.

The estimator: profiled least squares
-------------------------------------
The model is discrete-time by definition (see chm.model), so the transition
density is exactly Gaussian:

    x_{t+1} - x_t = lam ( -x_t^3 + a_t x_t + b_t ) dt + sigma sqrt(dt) e_t
    a_t = alpha0 + alpha_A A_t,   b_t = beta0 + beta_S S + beta_T T + beta_U U

Expanding, the mean increment is LINEAR in a reparameterised coefficient vector

    dx_t = th1 (-x_t^3) + th2 x_t + th3 (A_t x_t)
           + th4 + th5 S_t + th6 T_t + th7 U_t + noise                     (*)

with   th1 = lam,          th2 = lam*alpha0,   th3 = lam*alpha_A,
       th4 = lam*beta0,    th5 = lam*beta_S,   th6 = lam*beta_T,
       th7 = lam*beta_U.

A_t depends only on the single parameter eps.  So conditional on eps, (*) is
ordinary least squares -- exact, instantaneous, with no bounds, no starting
values and no local optima -- and the fit reduces to a one-dimensional search
over eps.  The structural parameters come back as

    lam = th1,   alpha0 = th2/th1,   alpha_A = th3/th1,   beta_k = th_k/th1.

This replaces an earlier bounded multi-start L-BFGS-B fit over nine parameters,
which was returning estimates pinned at three separate bounds: lam and the
alphas are badly non-identified when searched jointly (only their products
appear in the drift), but perfectly identified in this parameterisation.

Sign convention: th1 = lam > 0 is required for the cubic term to be restoring.
A fitted th1 <= 0 means the series is not a relaxation process at all, and is
reported as such rather than being silently clipped.

Inference
---------
Two nulls, in increasing order of severity.

    monostable   alpha_A = 0 and alpha0 <= 0, i.e. th3 = 0 and th2 <= 0.
                 Nested; tested by likelihood ratio with a parametric-bootstrap
                 null distribution (the restriction is on the boundary, so the
                 chi-squared reference is invalid).

    random walk  The serious one.  Tonic electrodermal activity is highly
                 persistent (ADF p > 0.05 on WESAD subjects), and a random walk
                 observed over a finite window spends time in two places and so
                 looks bimodal and looks bistable.  `rw_surrogate_test` refits
                 the whole pipeline to unit-root surrogates matched on length
                 and increment variance.  We treat THIS, not the monostable
                 restriction, as the primary test: a result that a random walk
                 reproduces is not a result.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import lfilter

from .model import CHMParams, softplus

__all__ = [
    "FREE",
    "slow_path",
    "design_matrix",
    "fit_mle",
    "fit_monostable",
    "neg_log_likelihood",
    "lrt_bistability",
    "rw_surrogate_test",
    "latent_path",
    "one_step_predictive_loglik",
    "ukf_negloglik",
]

FREE = ("beta0", "beta_S", "beta_T", "beta_U", "alpha0", "alpha_A",
        "lam", "sigma", "eps")

EPS_GRID = (1e-3, 0.30)          # search range for the slow-variable rate
_TINY = 1e-12


# --------------------------------------------------------------------------- #
# slow variable
# --------------------------------------------------------------------------- #
def slow_path(x, eps, x_ref=0.0, dt=1.0):
    """
    A_t = (1-c) A_{t-1} + c softplus(x_{t-1} - x_ref),  c = eps*dt.

    A first-order IIR filter, so lfilter rather than a Python loop: this is
    called on every objective evaluation.  b = [0, c] supplies the one-step
    lag, so the input must not be pre-shifted.  softplus >= 0 and A_0 = 0, so
    A_t >= 0 automatically.
    """
    c = float(eps) * float(dt)
    u = softplus(np.asarray(x, float) - x_ref)
    return lfilter([0.0, c], [1.0, -(1.0 - c)], u)


_slow_path = slow_path        # backwards-compatible alias


def latent_path(x, S, T, U, p: CHMParams, dt=1.0):
    """(A, a, b) implied by a parameter set and the observed series."""
    A = slow_path(x, p.eps, p.x_ref, dt)
    a = p.alpha0 + p.alpha_A * A
    b = (p.beta0 + p.beta_S * np.asarray(S, float)
         + p.beta_T * np.asarray(T, float) + p.beta_U * np.asarray(U, float))
    return A, a, b


# --------------------------------------------------------------------------- #
# design matrix and the conditional OLS solve
# --------------------------------------------------------------------------- #
def design_matrix(x, S, T, U, A, dt=1.0):
    """Columns of (*), aligned so row t predicts x_{t+1} - x_t."""
    x = np.asarray(x, float)
    return np.column_stack([
        -(x[:-1] ** 3) * dt,          # th1 = lam
        x[:-1] * dt,                  # th2 = lam alpha0
        A[:-1] * x[:-1] * dt,         # th3 = lam alpha_A
        np.ones(len(x) - 1) * dt,     # th4 = lam beta0
        np.asarray(S, float)[:-1] * dt,
        np.asarray(T, float)[:-1] * dt,
        np.asarray(U, float)[:-1] * dt,
    ])


def _solve_cusp(X, y):
    """
    OLS subject to th1 >= 0.

    th1 = lam must be positive for the cubic term to be restoring; a negative
    value is not a badly-fitted cusp, it is outside the model space entirely
    (and it flips the sign of a = th2/th1 and b = th4/th1, making the geometry
    meaningless).  The constraint is part of the model, not a convenience.

    Since only one coefficient is constrained, the KKT solution is: take the
    unconstrained OLS; if th1 < 0 the constraint is active, so set th1 = 0 and
    refit the rest.  th1 = 0 collapses the model onto its monostable
    (Ornstein-Uhlenbeck) special case, and the caller is told via
    `cusp_identified`.
    """
    th, *_ = np.linalg.lstsq(X, y, rcond=None)
    if th[0] >= 0:
        return th, True
    rest = [1, 2, 3, 4, 5, 6]
    th_r, *_ = np.linalg.lstsq(X[:, rest], y, rcond=None)
    full = np.zeros(X.shape[1])
    full[rest] = th_r
    return full, False


def _solve(X, y, monostable=False):
    """OLS, or the constrained solve for the monostable restriction."""
    if monostable:
        # th3 = 0 (drop the A*x column) and th2 <= 0
        keep = [0, 1, 3, 4, 5, 6]
        Xm = X[:, keep]
        th, *_ = np.linalg.lstsq(Xm, y, rcond=None)
        if th[1] > 0:                     # active constraint: refit with th2 = 0
            keep2 = [0, 3, 4, 5, 6]
            th2, *_ = np.linalg.lstsq(X[:, keep2], y, rcond=None)
            full = np.zeros(7)
            full[[0, 3, 4, 5, 6]] = th2
        else:
            full = np.zeros(7)
            full[keep] = th
        return full
    return _solve_cusp(X, y)[0]


def _profile_nll(eps, x, S, T, U, dt, monostable):
    """Concentrated negative log-likelihood at a given eps."""
    A = slow_path(x, eps, 0.0, dt)
    X = design_matrix(x, S, T, U, A, dt)
    y = np.diff(np.asarray(x, float))
    if monostable:
        th, identified = _solve(X, y, True), False
    else:
        th, identified = _solve_cusp(X, y)
    resid = y - X @ th
    n = len(y)
    s2 = max(float(np.mean(resid ** 2)), _TINY)
    nll = 0.5 * n * (np.log(2 * np.pi * s2) + 1.0)
    return nll, th, s2, A, identified


def _to_params(th, s2, eps, dt, base: CHMParams | None = None):
    """Map the regression coefficients back to structural parameters."""
    p = CHMParams(**{k: v for k, v in (base or CHMParams()).as_dict().items()})
    lam = float(th[0])
    p.lam = lam
    p.eps = float(eps)
    p.sigma = float(np.sqrt(max(s2, _TINY) / dt))
    if abs(lam) < 1e-8:
        # degenerate: no restoring cubic term, so (a, b) are not defined
        p.alpha0 = p.alpha_A = p.beta0 = p.beta_S = p.beta_T = p.beta_U = np.nan
        return p
    p.alpha0 = float(th[1] / lam)
    p.alpha_A = float(th[2] / lam)
    p.beta0 = float(th[3] / lam)
    p.beta_S = float(th[4] / lam)
    p.beta_T = float(th[5] / lam)
    p.beta_U = float(th[6] / lam)
    return p


# --------------------------------------------------------------------------- #
# public fitting interface
# --------------------------------------------------------------------------- #
def fit_mle(x, S, T, U, dt=1.0, monostable=False, eps_grid=EPS_GRID,
            n_grid=40, refine=True, **_ignored):
    """
    Profiled maximum likelihood.

    Grid then Brent refinement over eps, with OLS solved exactly inside.  The
    **_ignored keyword catches n_restarts / rng / init from the earlier API so
    existing call sites keep working; this estimator is deterministic and needs
    none of them.
    """
    x = np.asarray(x, float)
    grid = np.linspace(eps_grid[0], eps_grid[1], n_grid)
    vals = [_profile_nll(e, x, S, T, U, dt, monostable)[0] for e in grid]
    best_i = int(np.argmin(vals))
    eps_hat = float(grid[best_i])

    if refine:
        lo = grid[max(best_i - 1, 0)]
        hi = grid[min(best_i + 1, n_grid - 1)]
        if hi > lo:
            r = minimize_scalar(
                lambda e: _profile_nll(e, x, S, T, U, dt, monostable)[0],
                bounds=(lo, hi), method="bounded",
                options={"xatol": 1e-5},
            )
            if np.isfinite(r.fun) and r.fun <= min(vals):
                eps_hat = float(r.x)

    nll, th, s2, A, identified = _profile_nll(eps_hat, x, S, T, U, dt, monostable)
    p = _to_params(th, s2, eps_hat, dt)

    # One-sided t-test for a restoring cubic term, H0: th1 <= 0.
    # A positive point estimate is not evidence: a random walk fitted with this
    # design also returns small positive th1 about half the time.  The question
    # is whether th1 is distinguishable from zero, so the standard error is
    # what the paper reports.
    X = design_matrix(x, S, T, U, A, dt)
    y = np.diff(np.asarray(x, float))
    lam_t = lam_p = np.nan
    lam_t_error = None
    try:
        XtX_inv = np.linalg.pinv(X.T @ X)
        se = float(np.sqrt(max(s2 * XtX_inv[0, 0], _TINY)))
        lam_t = float(th[0] / se)
        from scipy.stats import t as _tdist
        lam_p = float(_tdist.sf(lam_t, df=max(len(y) - X.shape[1], 1)))
    except Exception as exc:
        # Do NOT swallow this silently. If the t-statistic cannot be formed,
        # lam_p stays NaN and `lam_significant` below evaluates to False --
        # which is indistinguishable from a unit that was tested and found
        # non-significant. A systematic failure here would therefore
        # manufacture exactly the null result this paper reports, and no
        # caller would see anything wrong. Recording the reason lets callers
        # count failures instead of absorbing them into the denominator.
        lam_t_error = f"{type(exc).__name__}: {exc}"

    k = (6 if monostable else 7) + 2          # coefficients + sigma + eps
    n = len(x) - 1
    return {
        "params": p,
        "theta": th,
        "nll": float(nll),
        "aic": float(2 * k + 2 * nll),
        "bic": float(k * np.log(max(n, 2)) + 2 * nll),
        "n_obs": int(n),
        "converged": bool(np.isfinite(nll)),
        # The central diagnostic.  False means the th1 >= 0 constraint was
        # active, i.e. the data supply no restoring cubic term and the CHM has
        # collapsed onto its monostable special case.  Downstream geometry
        # (a, b, folds, hysteresis, states) is undefined for such units and
        # must not be computed.
        "cusp_identified": bool(identified and th[0] > 0),
        "lam_positive": bool(th[0] > 0),
        "lam_t": lam_t,
        "lam_p": lam_p,
        "lam_significant": bool(np.isfinite(lam_p) and lam_p < 0.05),
        # None when the t-statistic was computed. A string when it could not
        # be, in which case `lam_significant` is False for want of a test
        # rather than for want of an effect. Callers that aggregate
        # significance rates must treat these as missing, not as negatives.
        "lam_t_error": lam_t_error,
        "free": FREE,
    }


def fit_monostable(x, S, T, U, dt=1.0, **kw):
    """Restricted fit: alpha_A = 0 and alpha0 <= 0, so the system never tips."""
    kw.pop("monostable", None)
    return fit_mle(x, S, T, U, dt=dt, monostable=True, **kw)


def neg_log_likelihood(vec, x, S, T, U, dt=1.0, free=FREE,
                       base: CHMParams | None = None):
    """Negative log-likelihood at an explicit parameter vector (used in tests)."""
    p = (base or CHMParams()).with_vector(vec, free)
    if p.sigma <= 0 or p.eps <= 0:
        return 1e12
    x = np.asarray(x, float)
    A, a, b = latent_path(x, S, T, U, p, dt)
    f = -(x[:-1] ** 3) + a[:-1] * x[:-1] + b[:-1]
    resid = x[1:] - x[:-1] - p.lam * f * dt
    var = p.sigma ** 2 * dt
    nll = 0.5 * np.sum(resid ** 2) / var + 0.5 * len(resid) * np.log(2 * np.pi * var)
    return float(nll) if np.isfinite(nll) else 1e12


# --------------------------------------------------------------------------- #
# inference
# --------------------------------------------------------------------------- #
def lrt_bistability(x, S, T, U, dt=1.0, n_boot=200, rng=None, **_ignored):
    """
    Likelihood-ratio test of bistability against the nested monostable model,
    with a parametric-bootstrap null (boundary restriction -> no chi-squared).
    """
    from .model import simulate

    rng = np.random.default_rng(rng)
    full = fit_mle(x, S, T, U, dt=dt)
    null = fit_monostable(x, S, T, U, dt=dt)
    stat = 2.0 * (null["nll"] - full["nll"])

    boots = []
    p0 = null["params"]
    if np.all(np.isfinite([p0.alpha0, p0.beta_S, p0.lam, p0.sigma])):
        for _ in range(n_boot):
            xs = simulate(p0, S, T, U, dt=dt, rng=rng)["x"]
            if not np.all(np.isfinite(xs)):
                continue
            s = 2.0 * (fit_monostable(xs, S, T, U, dt=dt)["nll"]
                       - fit_mle(xs, S, T, U, dt=dt)["nll"])
            if np.isfinite(s):
                boots.append(s)

    boots = np.array(boots, float)
    p = ((np.sum(boots >= stat) + 1) / (boots.size + 1)) if boots.size else np.nan
    return {"stat": float(stat), "p": float(p), "n_boot": int(boots.size),
            "full": full, "null": null, "boot_null": boots}


def rw_surrogate_test(x, S, T, U, dt=1.0, n_surr=200, rng=None,
                      statistics=("lam_t", "lr", "bimodality", "alpha0"),
                      surrogate="rw"):
    """
    PRIMARY test.  Compare the observed statistics against unit-root surrogates
    matched on length, increment variance and marginal scale.

    Rationale: a highly persistent series observed over a finite window will
    look bimodal and will be better fitted by a flat-bottomed (bistable)
    potential than by a single well, purely because it wanders.  Unless the
    observed statistic exceeds what a random walk produces, there is no
    evidence for bistability, however small the nested-LRT p-value is.

    `surrogate` selects the null ensemble:

        "rw"    unit-root walk matched on length, increment variance and
                marginal scale. The default, and the right null for a signal
                whose persistence is the concern.
        "iaaft" amplitude-adjusted Fourier surrogate preserving BOTH the power
                spectrum and the marginal distribution. Required for signals
                carrying deterministic low-frequency structure (circadian or
                ambient drift in skin temperature, say), which a random walk
                cannot reproduce and which therefore inflates the "rw" test.

    Returns observed values, surrogate p-values and the surrogate ensembles.
    """
    from sklearn.mixture import GaussianMixture

    rng = np.random.default_rng(rng)
    x = np.asarray(x, float)
    n = len(x)
    sd_incr = float(np.std(np.diff(x)))
    sd_lvl = float(np.std(x))

    def _bimodality(v):
        V = np.asarray(v, float).reshape(-1, 1)
        try:
            b1 = GaussianMixture(1, random_state=0).fit(V).bic(V)
            b2 = GaussianMixture(2, random_state=0).fit(V).bic(V)
            return float(b1 - b2)          # > 0 favours two components
        except Exception:
            return np.nan

    want = set(statistics)

    def _stats(v):
        # Only compute what the caller asked for. The monostable refit and the
        # Gaussian-mixture fit each cost about as much as the main fit, and
        # when only `lam_t` is requested -- the common case, since it is the
        # decisive statistic -- skipping them makes the surrogate loop roughly
        # three times faster with no change to the result.
        out = {}
        f = fit_mle(v, S, T, U, dt=dt)
        if "lr" in want:
            g = fit_monostable(v, S, T, U, dt=dt)
            out["lr"] = 2.0 * (g["nll"] - f["nll"])
        if "alpha0" in want:
            out["alpha0"] = f["params"].alpha0
        if "bimodality" in want:
            out["bimodality"] = _bimodality(v)
        # t-statistic on the cubic restoring coefficient.  Its nominal
        # t-distribution is invalid here -- on unit-root data the naive test
        # rejects at ~35% rather than 5% (the classical spurious-regression
        # problem).  Calibrating it against this surrogate ensemble restores
        # correct size, which is why this, and not the nominal p-value, is the
        # statistic the paper reports.
        out["lam_t"] = f.get("lam_t", np.nan)
        return out

    if surrogate == "iaaft":
        from .ews import iaaft_surrogate

        def _draw():
            return iaaft_surrogate(x, rng)
    elif surrogate == "rw":
        def _draw():
            w = np.cumsum(rng.standard_normal(n) * sd_incr)
            sd = np.std(w)
            return (w - w.mean()) / (sd if sd > _TINY else 1.0) * sd_lvl
    else:
        raise ValueError(f"unknown surrogate type: {surrogate!r}")

    obs = _stats(x)
    null = {k: [] for k in statistics}
    for _ in range(n_surr):
        st = _stats(_draw())
        for k in statistics:
            if np.isfinite(st.get(k, np.nan)):
                null[k].append(st[k])

    res = {}
    for k in statistics:
        arr = np.array(null[k], float)
        o = obs.get(k, np.nan)
        res[k] = {
            "observed": float(o) if np.isfinite(o) else np.nan,
            "null_median": float(np.median(arr)) if arr.size else np.nan,
            "null_p95": float(np.percentile(arr, 95)) if arr.size else np.nan,
            "p": float((np.sum(arr >= o) + 1) / (arr.size + 1))
            if arr.size and np.isfinite(o) else np.nan,
            "n_surr": int(arr.size),
        }
    return res


# --------------------------------------------------------------------------- #
# out-of-sample comparison
# --------------------------------------------------------------------------- #
def one_step_predictive_loglik(p: CHMParams, x, S, T, U, dt=1.0):
    """Mean one-step-ahead predictive log-density on held-out data."""
    x = np.asarray(x, float)
    A, a, b = latent_path(x, S, T, U, p, dt)
    f = -(x[:-1] ** 3) + a[:-1] * x[:-1] + b[:-1]
    resid = x[1:] - x[:-1] - p.lam * f * dt
    var = p.sigma ** 2 * dt
    ll = -0.5 * resid ** 2 / var - 0.5 * np.log(2 * np.pi * var)
    return float(np.mean(ll))


# --------------------------------------------------------------------------- #
# UKF variant (measurement-error-aware; robustness check)
# --------------------------------------------------------------------------- #
def ukf_negloglik(vec, y, S, T, U, dt=1.0, free=FREE, base: CHMParams | None = None,
                  alpha=1e-3, beta_ut=2.0, kappa_ut=0.0):
    """
    Marginal negative log-likelihood under the CHM model, via an unscented
    Kalman filter over the latent state (x, A) with y_t = c0 + c1 x_t + noise.

    Reported as a robustness check: plug-in estimation of a nonlinear drift from
    a noisy proxy is biased towards the linear (monostable) model, i.e. against
    our own hypothesis, which is the safe direction for the bias to run.
    """
    p = (base or CHMParams()).with_vector(vec, free)
    if p.sigma <= 0 or p.eps <= 0 or p.obs_sd <= 0:
        return 1e12

    y = np.asarray(y, float)
    S, T, U = (np.asarray(v, float) for v in (S, T, U))
    b = p.beta0 + p.beta_S * S + p.beta_T * T + p.beta_U * U

    L = 2
    lam_ut = alpha ** 2 * (L + kappa_ut) - L
    Wm = np.full(2 * L + 1, 1.0 / (2 * (L + lam_ut)))
    Wc = Wm.copy()
    Wm[0] = lam_ut / (L + lam_ut)
    Wc[0] = lam_ut / (L + lam_ut) + (1 - alpha ** 2 + beta_ut)

    m = np.array([float(y[0] - p.c0) / max(p.c1, 1e-6), 0.0])
    Pcov = np.diag([1.0, 0.5])
    Q = np.diag([p.sigma ** 2 * dt, (p.eps * 0.1) ** 2 * dt])
    R = p.obs_sd ** 2

    nll = 0.0
    for t in range(1, len(y)):
        try:
            Sq = np.linalg.cholesky((L + lam_ut) * (Pcov + 1e-9 * np.eye(L)))
        except np.linalg.LinAlgError:
            return 1e12
        sig = np.vstack([m, m + Sq.T, m - Sq.T])

        prop = np.empty_like(sig)
        for i, (xi, Ai) in enumerate(sig):
            a_i = p.alpha0 + p.alpha_A * Ai
            xn = xi + p.lam * (-(xi ** 3) + a_i * xi + b[t - 1]) * dt
            An = max(0.0, Ai + p.eps * (softplus(xi - p.x_ref) - Ai) * dt)
            prop[i] = (np.clip(xn, -50, 50), An)

        m = Wm @ prop
        d = prop - m
        Pcov = (d.T * Wc) @ d + Q

        yhat = p.c0 + p.c1 * m[0]
        Pyy = p.c1 ** 2 * Pcov[0, 0] + R
        innov = y[t] - yhat
        K = (p.c1 * Pcov[:, 0]) / Pyy
        m = m + K * innov
        Pcov = Pcov - np.outer(K, K) * Pyy
        m[1] = max(0.0, m[1])

        nll += 0.5 * (np.log(2 * np.pi * Pyy) + innov ** 2 / Pyy)

    return float(nll) if np.isfinite(nll) else 1e12
