"""
chm.potential
=============
Geometry of the cusp potential that underlies the Cusp-Hysteretic Markov (CHM)
model.

The latent functional-load coordinate x obeys

    dx = -dV/dx (x; a, b) dt + sigma dW,     V(x;a,b) = x^4/4 - a x^2/2 - b x

where
    b  ("normal factor")   = instantaneous exogenous drive  (sensory + task demand)
    a  ("splitting factor")= regulatory-capacity depletion; controls BISTABILITY.

Everything the paper claims about hysteresis, critical slowing down and the
five functional states is a *consequence* of this geometry, not an assumption.
This module supplies the closed-form quantities used throughout.

Key closed forms (derived in the paper, Sec. III):
    equilibria      roots of   x^3 - a x - b = 0
    bistability     D(a,b) = 4 a^3 - 27 b^2 > 0
    fold points     x_pm = +/- sqrt(a/3)
    fold drives     b_up = +2/(3 sqrt 3) a^{3/2},  b_dn = -b_up      (a > 0)
    hysteresis      dB(a) = b_up - b_dn = 4/(3 sqrt 3) a^{3/2}   <-- 3/2 scaling law
    curvature       V''(x) = 3 x^2 - a
    relaxation rate lam(x*) = V''(x*) = 3 x*^2 - a
    OU limit        AC1 = exp(-lam dt),  Var = sigma^2 / (2 lam)
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "FOLD_CONST",
    "potential",
    "drift",
    "curvature",
    "discriminant",
    "is_bistable",
    "fold_drive",
    "hysteresis_width",
    "equilibria",
    "stable_equilibria",
    "saddle",
    "attractor_for",
    "relaxation_rate",
    "ou_ac1",
    "ou_variance",
    "barrier_height",
    "kramers_rate",
    "distance_to_fold",
]

# 2 / (3 * sqrt(3)) -- the constant in the fold-drive law
FOLD_CONST: float = 2.0 / (3.0 * np.sqrt(3.0))

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# potential, drift, curvature
# --------------------------------------------------------------------------- #
def potential(x, a, b):
    """V(x; a, b) = x^4/4 - a x^2/2 - b x."""
    x, a, b = np.asarray(x, float), np.asarray(a, float), np.asarray(b, float)
    return 0.25 * x**4 - 0.5 * a * x**2 - b * x


def drift(x, a, b):
    """f(x) = -dV/dx = -x^3 + a x + b."""
    x, a, b = np.asarray(x, float), np.asarray(a, float), np.asarray(b, float)
    return -(x**3) + a * x + b


def curvature(x, a):
    """V''(x) = 3 x^2 - a.  Positive at stable equilibria, negative at the saddle."""
    x, a = np.asarray(x, float), np.asarray(a, float)
    return 3.0 * x**2 - a


# --------------------------------------------------------------------------- #
# bistability / folds
# --------------------------------------------------------------------------- #
def discriminant(a, b):
    """
    Cubic discriminant D = 4 a^3 - 27 b^2 of  x^3 - a x - b = 0.

    D > 0  -> three distinct real roots -> two stable basins + one saddle (BISTABLE)
    D <= 0 -> single real root                                   (MONOSTABLE)

    We call D the *bistability index* B_t in the paper.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    return 4.0 * a**3 - 27.0 * b**2


def is_bistable(a, b):
    """Boolean mask: does an alternative attractor coexist right now?"""
    return discriminant(a, b) > 0.0


def fold_drive(a):
    """
    Critical drive magnitude at the fold:  b_c(a) = 2/(3 sqrt 3) * a^{3/2}, a > 0.

    Upward jump (into overload) when b >  +b_c.
    Downward jump (out of overload) when b < -b_c.
    Returns 0 for a <= 0 (no folds; system is monostable for every b).
    """
    a = np.asarray(a, float)
    out = np.zeros_like(a)
    pos = a > 0
    out[pos] = FOLD_CONST * np.power(a[pos], 1.5)
    return out if out.ndim else float(out)


def hysteresis_width(a):
    """
    Width of the hysteresis loop in drive units:

        dB(a) = b_up - b_dn = 2 * b_c(a) = 4/(3 sqrt 3) * a^{3/2}

    PREDICTION P1 of the paper: the loop width scales with the 3/2 power of the
    splitting factor.  This is the sharp, falsifiable form of "recovery is
    delayed"; it replaces the purely descriptive statement that the exit load is
    lower than the entry load.
    """
    return 2.0 * np.asarray(fold_drive(a), float)


def distance_to_fold(a, b):
    """
    Signed distance of the current drive to the upward fold, mu = b_up - b.

    mu -> 0+  means the system is approaching the tipping point from the safe
    side; the early-warning scaling laws (P2) are stated in terms of mu.
    """
    return np.asarray(fold_drive(a), float) - np.asarray(b, float)


# --------------------------------------------------------------------------- #
# equilibria
# --------------------------------------------------------------------------- #
def equilibria(a, b):
    """
    Real roots of x^3 - a x - b = 0, ascending, padded with NaN to length 3.

    Scalar a, b -> array shape (3,).  Array a, b -> shape (n, 3).
    """
    a_arr = np.atleast_1d(np.asarray(a, float))
    b_arr = np.atleast_1d(np.asarray(b, float))
    a_arr, b_arr = np.broadcast_arrays(a_arr, b_arr)
    n = a_arr.size
    out = np.full((n, 3), np.nan)

    for i in range(n):
        r = np.roots([1.0, 0.0, -a_arr.flat[i], -b_arr.flat[i]])
        real = np.sort(r[np.abs(r.imag) < 1e-8].real)
        # Collapse repeated roots.  At the cusp point (a = b = 0) the cubic has
        # a triple root at the origin, and on a fold it has a double root; both
        # are a *single* equilibrium physically, and reporting them as three
        # would make the degenerate case look bistable.
        if real.size > 1:
            keep = [real[0]]
            for v in real[1:]:
                if v - keep[-1] > 1e-7:
                    keep.append(v)
            real = np.array(keep)
        out[i, : real.size] = real

    if np.ndim(a) == 0 and np.ndim(b) == 0:
        return out[0]
    return out


def stable_equilibria(a, b):
    """
    (x_lower, x_upper) stable equilibria.  If monostable both entries are the
    single attractor, so downstream code never has to special-case.
    """
    eq = equilibria(a, b)
    eq2 = np.atleast_2d(eq)
    lo = np.empty(eq2.shape[0])
    hi = np.empty(eq2.shape[0])
    for i in range(eq2.shape[0]):
        real = eq2[i][~np.isnan(eq2[i])]
        if real.size == 3:
            lo[i], hi[i] = real[0], real[2]          # middle root is the saddle
        else:
            lo[i] = hi[i] = real[0]
    if np.ndim(a) == 0 and np.ndim(b) == 0:
        return float(lo[0]), float(hi[0])
    return lo, hi


def saddle(a, b):
    """Unstable (middle) equilibrium; NaN when monostable."""
    eq = np.atleast_2d(equilibria(a, b))
    out = np.full(eq.shape[0], np.nan)
    for i in range(eq.shape[0]):
        real = eq[i][~np.isnan(eq[i])]
        if real.size == 3:
            out[i] = real[1]
    if np.ndim(a) == 0 and np.ndim(b) == 0:
        return float(out[0])
    return out


def attractor_for(x, a, b):
    """
    Which basin does x currently sit in?  Returns 0 (lower/functional) or
    1 (upper/overloaded).  Monostable -> always 0 except when the single
    attractor itself is high, which the caller resolves via the drive.
    """
    s = saddle(a, b)
    x = np.asarray(x, float)
    s = np.asarray(s, float)
    upper = np.where(np.isnan(s), x > 0.0, x > s)
    return upper.astype(int)


# --------------------------------------------------------------------------- #
# linear response: the analytic early-warning signals
# --------------------------------------------------------------------------- #
def relaxation_rate(x_star, a):
    """
    lam = V''(x*) = 3 x*^2 - a  -- the rate at which small perturbations decay.

    lam -> 0 at a fold: this IS critical slowing down, derived rather than
    postulated.  Near the fold the normal form gives lam ~ sqrt(mu) with
    mu = b_up - b, which yields the paper's scaling exponents.
    """
    return curvature(x_star, a)


def ou_ac1(lam, dt=1.0):
    """Lag-1 autocorrelation of the locally linearised (OU) process."""
    lam = np.maximum(np.asarray(lam, float), _EPS)
    return np.exp(-lam * dt)


def ou_variance(lam, sigma):
    """Stationary variance of the locally linearised process: sigma^2 / (2 lam)."""
    lam = np.maximum(np.asarray(lam, float), _EPS)
    return np.asarray(sigma, float) ** 2 / (2.0 * lam)


# --------------------------------------------------------------------------- #
# barrier crossing: the bridge from the SDE to a Markov chain
# --------------------------------------------------------------------------- #
def barrier_height(a, b, direction="up"):
    """
    dV = V(saddle) - V(origin basin).  NaN when monostable (no barrier).
    direction='up'   : escape from the lower (functional) basin
    direction='down' : escape from the upper (overloaded) basin
    """
    lo, hi = stable_equilibria(a, b)
    s = saddle(a, b)
    start = lo if direction == "up" else hi
    return potential(s, a, b) - potential(start, a, b)


def kramers_rate(a, b, sigma, direction="up"):
    """
    Kramers escape rate over the barrier:

        r = sqrt(|V''(x_start) V''(x_saddle)|) / (2 pi) * exp(-2 dV / sigma^2)

    Discrete-time transition probability over a step dt is then
    P = 1 - exp(-r dt)  (see chm.states.transition_matrix_from_params).

    This is the structural core of the paper: the 5x5 transition matrix stops
    being 20 free counted parameters and becomes a deterministic function of
    the ~8 interpretable dynamical parameters evaluated at the current
    covariates.
    """
    a_a = np.atleast_1d(np.asarray(a, float))
    b_a = np.atleast_1d(np.asarray(b, float))
    sig = np.atleast_1d(np.asarray(sigma, float))
    a_a, b_a, sig = np.broadcast_arrays(a_a, b_a, sig)

    lo, hi = stable_equilibria(a_a, b_a)
    s = saddle(a_a, b_a)
    start = lo if direction == "up" else hi

    dV = potential(s, a_a, b_a) - potential(start, a_a, b_a)
    curv_start = np.abs(curvature(start, a_a))
    curv_saddle = np.abs(curvature(s, a_a))

    pref = np.sqrt(curv_start * curv_saddle) / (2.0 * np.pi)
    rate = pref * np.exp(-2.0 * dV / np.maximum(sig**2, _EPS))

    # monostable -> no barrier -> deterministic slide, represented as a very
    # large rate so that P = 1 - exp(-r dt) saturates at 1.
    rate = np.where(np.isnan(s), 1e6, rate)
    rate = np.where(np.isfinite(rate), rate, 1e6)

    if np.ndim(a) == 0 and np.ndim(b) == 0:
        return float(rate[0])
    return rate
