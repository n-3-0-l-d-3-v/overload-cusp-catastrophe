"""
chm.ews
=======
Early-warning signals, and -- the part that is new here -- tests of the
*scaling laws* the cusp geometry predicts for them.

Prior EWS work in psychopathology reports that lag-1 autocorrelation and
variance "rise" before a transition and supports that with a t-test against a
control window.  A rise is weak evidence: almost any nonstationarity produces
one.  The cusp normal form predicts the functional form.  Near the upward fold,
with mu = b_up - b the distance to the fold,

    lam(mu) ~ mu^{1/2}                     (relaxation rate)
    Var(x)  = sigma^2 / (2 lam) ~ mu^{-1/2}          <-- exponent -1/2
    -log AC1 = lam dt          ~ mu^{+1/2}           <-- exponent +1/2

So the paper tests two point hypotheses about exponents, not a direction.  That
is a far more demanding test, and it can fail.

Everything here is also run against surrogate nulls (AR(1)-matched and
phase-randomised), because rolling-window statistics on autocorrelated data
generate spurious trends.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

__all__ = [
    "rolling_ac1",
    "rolling_variance",
    "detrend",
    "kendall_tau_trend",
    "ar1_surrogate",
    "phase_randomised_surrogate",
    "surrogate_pvalue",
    "fit_scaling_exponent",
    "onset_indices",
    "lead_time_auc",
]

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# basic indicators
# --------------------------------------------------------------------------- #
def detrend(y, window):
    """Gaussian-kernel detrending; removes slow drift that inflates variance."""
    from scipy.ndimage import gaussian_filter1d

    y = np.asarray(y, float)
    return y - gaussian_filter1d(y, sigma=max(window / 4.0, 1.0), mode="nearest")


def rolling_ac1(y, window):
    """Rolling lag-1 autocorrelation; NaN for the first `window` samples."""
    y = np.asarray(y, float)
    out = np.full(y.shape, np.nan)
    for i in range(window, len(y)):
        seg = y[i - window : i]
        if np.std(seg) < 1e-9:
            out[i] = 0.0
        else:
            out[i] = np.corrcoef(seg[:-1], seg[1:])[0, 1]
    return out


def rolling_variance(y, window):
    y = np.asarray(y, float)
    out = np.full(y.shape, np.nan)
    for i in range(window, len(y)):
        out[i] = np.var(y[i - window : i])
    return out


def kendall_tau_trend(y):
    """Kendall tau of an indicator against time -- the standard EWS trend stat."""
    y = np.asarray(y, float)
    m = np.isfinite(y)
    if m.sum() < 5:
        return np.nan
    t = np.arange(len(y))[m]
    return float(stats.kendalltau(t, y[m]).statistic)


# --------------------------------------------------------------------------- #
# surrogate nulls
# --------------------------------------------------------------------------- #
def ar1_surrogate(y, rng=None):
    """Surrogate with the same mean, variance and lag-1 autocorrelation."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y, float)
    y = y[np.isfinite(y)]
    if len(y) < 3:
        return y.copy()
    phi = np.corrcoef(y[:-1], y[1:])[0, 1]
    phi = float(np.clip(phi, -0.99, 0.99))
    resid_sd = np.std(y) * np.sqrt(max(1 - phi**2, 1e-6))
    out = np.empty(len(y))
    out[0] = y[0]
    for i in range(1, len(y)):
        out[i] = phi * out[i - 1] + resid_sd * rng.standard_normal()
    return out - out.mean() + y.mean()


def phase_randomised_surrogate(y, rng=None):
    """Fourier surrogate: identical power spectrum, destroyed nonlinearity."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y, float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 4:
        return y.copy()
    F = np.fft.rfft(y)
    ph = rng.uniform(0, 2 * np.pi, len(F))
    ph[0] = 0.0
    if n % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(np.abs(F) * np.exp(1j * ph), n=n)


def iaaft_surrogate(y, rng=None, n_iter=200, tol=1e-8):
    """
    Iterative Amplitude Adjusted Fourier Transform surrogate
    (Schreiber & Schmitz, 1996).

    Preserves BOTH the power spectrum and the marginal distribution of the
    original series, while destroying any nonlinear temporal structure. The
    null it encodes is therefore "a monotonic transform of a linear Gaussian
    process with this spectrum" -- which is exactly the null we want, and a
    considerably harder one than a random walk.

    Why it matters here: a random-walk surrogate is matched only on length,
    increment variance and marginal scale. It cannot reproduce deterministic
    low-frequency structure such as the circadian and ambient drift in wrist
    skin temperature, so such a series beats the random-walk ensemble easily
    and the calibrated test inflates. IAAFT keeps that drift (it is
    low-frequency power) and keeps the marginal shape (so bimodality alone
    cannot drive a rejection), leaving nonlinearity as the only thing the
    statistic can be responding to.

    Note the asymmetry: passing an IAAFT test is strong evidence, failing it
    is weak, because IAAFT also preserves some structure a genuine cusp would
    produce. It is the conservative choice, which is what we want for a
    result that would otherwise look positive.
    """
    rng = np.random.default_rng(rng)
    y = np.asarray(y, float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 8:
        return y.copy()

    target_amp = np.abs(np.fft.rfft(y))
    sorted_vals = np.sort(y)

    s = rng.permutation(y)
    prev = None
    for _ in range(n_iter):
        # (1) impose the original power spectrum, keep the current phases
        F = np.fft.rfft(s)
        phase = np.angle(F)
        s = np.fft.irfft(target_amp * np.exp(1j * phase), n=n)
        # (2) impose the original marginal by rank-ordering
        ranks = np.argsort(np.argsort(s))
        s = sorted_vals[ranks]
        if prev is not None:
            change = np.mean((s - prev) ** 2)
            if change < tol:
                break
        prev = s.copy()
    return s


def surrogate_pvalue(y, statistic, n_surr=500, kind="ar1", rng=None):
    """
    One-sided p-value of `statistic(y)` against a surrogate ensemble.

    Returns (observed, p, surrogate_array).
    """
    rng = np.random.default_rng(rng)
    gen = ar1_surrogate if kind == "ar1" else phase_randomised_surrogate
    obs = statistic(y)
    null = np.array([statistic(gen(y, rng)) for _ in range(n_surr)], float)
    null = null[np.isfinite(null)]
    if not np.isfinite(obs) or null.size == 0:
        return obs, np.nan, null
    p = (np.sum(null >= obs) + 1) / (null.size + 1)
    return float(obs), float(p), null


# --------------------------------------------------------------------------- #
# THE SCALING-LAW TEST  (prediction P2)
# --------------------------------------------------------------------------- #
def fit_scaling_exponent(mu, indicator, predicted=None, min_points=20,
                         mu_floor=1e-3, n_boot=2000, rng=None):
    """
    Fit  log(indicator) = c + gamma * log(mu)  and test gamma against the
    exponent the cusp geometry predicts.

    Parameters
    ----------
    mu        : distance to the fold, b_up - b  (only mu > mu_floor is used)
    indicator : rolling variance, or -log(AC1)
    predicted : theoretical exponent (-0.5 for variance, +0.5 for -log AC1)

    Returns
    -------
    dict with gamma, its bootstrap 95% CI, r^2, n, and -- when `predicted` is
    given -- a two-sided bootstrap p-value for H0: gamma = predicted.

    A wide CI that excludes the prediction is a *failure* of the theory and is
    reported as such; that is the point of stating the exponent in advance.
    """
    rng = np.random.default_rng(rng)
    mu = np.asarray(mu, float)
    ind = np.asarray(indicator, float)

    m = np.isfinite(mu) & np.isfinite(ind) & (mu > mu_floor) & (ind > 0)
    x = np.log(mu[m])
    y = np.log(ind[m])
    n = x.size
    if n < min_points:
        return {"gamma": np.nan, "ci": (np.nan, np.nan), "r2": np.nan,
                "n": int(n), "p_vs_predicted": np.nan, "predicted": predicted}

    lr = stats.linregress(x, y)
    gamma = float(lr.slope)

    boots = np.empty(n_boot)
    idx = np.arange(n)
    for i in range(n_boot):
        s = rng.choice(idx, size=n, replace=True)
        if np.std(x[s]) < 1e-12:
            boots[i] = np.nan
            continue
        boots[i] = stats.linregress(x[s], y[s]).slope
    boots = boots[np.isfinite(boots)]
    ci = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))

    p = np.nan
    if predicted is not None and boots.size:
        # two-sided bootstrap p-value for H0: gamma = predicted
        centred = boots - gamma
        p = float(
            2.0
            * min(
                (np.sum(centred >= predicted - gamma) + 1) / (boots.size + 1),
                (np.sum(centred <= predicted - gamma) + 1) / (boots.size + 1),
            )
        )
        p = min(p, 1.0)

    return {"gamma": gamma, "ci": ci, "r2": float(lr.rvalue**2), "n": int(n),
            "p_vs_predicted": p, "predicted": predicted}


# --------------------------------------------------------------------------- #
# onsets and prospective prediction
# --------------------------------------------------------------------------- #
def onset_indices(states, target="overloaded", min_gap=5):
    """Indices where the series first enters `target` after being elsewhere."""
    s = np.asarray(states).astype(str)
    out = []
    for i in range(1, len(s)):
        if s[i] == target and s[i - 1] != target:
            if not out or i - out[-1] >= min_gap:
                out.append(i)
    return np.array(out, int)


def lead_time_auc(indicator, onsets, n, lead, control_offset=None, rng=None):
    """
    Prospective test: can the indicator, evaluated `lead` steps BEFORE an
    onset, discriminate pre-onset windows from matched control windows?

    Reports AUC with a bootstrap CI.  Unlike a paired t-test on group means,
    this answers the question a deployed system actually poses: at time t, is
    an overload coming?
    """
    rng = np.random.default_rng(rng)
    ind = np.asarray(indicator, float)
    onsets = np.asarray(onsets, int)
    if control_offset is None:
        control_offset = 4 * lead

    pos, neg = [], []
    for o in onsets:
        i = o - lead
        j = o - control_offset
        if 0 <= i < n and np.isfinite(ind[i]):
            pos.append(ind[i])
        if 0 <= j < n and np.isfinite(ind[j]):
            neg.append(ind[j])

    pos, neg = np.array(pos, float), np.array(neg, float)
    if pos.size < 3 or neg.size < 3:
        return {"auc": np.nan, "ci": (np.nan, np.nan), "n_pos": pos.size,
                "n_neg": neg.size, "lead": lead}

    def _auc(p, q):
        u = stats.mannwhitneyu(p, q, alternative="greater").statistic
        return float(u / (len(p) * len(q)))

    auc = _auc(pos, neg)
    boots = np.array(
        [
            _auc(rng.choice(pos, pos.size, True), rng.choice(neg, neg.size, True))
            for _ in range(1000)
        ]
    )
    return {"auc": auc,
            "ci": (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))),
            "n_pos": int(pos.size), "n_neg": int(neg.size), "lead": int(lead)}
