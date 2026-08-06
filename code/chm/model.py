"""
chm.model
=========
The Cusp-Hysteretic Markov (CHM) model: parameters, driver link functions,
the fast-slow simulator, and the derived five-state labelling.

Full system (paper Sec. III):

    fast   dx_t = lam [ -x_t^3 + a_t x_t + b_t ] dt + sigma dW_t
    slow   dA_t = eps [ kappa * softplus(x_t - x_ref) - nu A_t ] dt

    drive        b_t = beta0 + beta_S S_t + beta_T T_t + beta_U U_t
    splitting    a_t = alpha0 + alpha_A A_t

Discrete time is primary
------------------------
We take the Euler map itself as the model,

    x_{t+1} = x_t + lam ( -x_t^3 + a_t x_t + b_t ) dt + sigma sqrt(dt) eps_t,

rather than treating it as an approximation to the SDE.  Two reasons.  First,
the data are sampled at a fixed window rate, so a discrete-time process is what
we actually observe.  Second, and more importantly, it makes the transition
density exactly Gaussian, so the likelihood in chm.estimate is exact and the
parameter estimates carry no discretisation bias -- which matters here because
an explicit scheme applied to a cubic drift is unstable for lam*dt >~ 0.35, and
a mismatch between the generating and fitting schemes would otherwise show up
as bias in exactly the coefficients that carry the scientific claims.

The rate constant lam sets the timescale only.  All the geometry -- folds,
bistability, the hysteresis width, the early-warning exponents -- depends on
(a, b) alone and is untouched by it.

x   latent functional-load coordinate (high = overloaded)
A   allostatic / recovery-debt variable, a SLOW state that carries history
S_t sensory drive, T_t task-switch cost, U_t contextual uncertainty  (observed)

Why the slow variable matters
-----------------------------
Because a_t rises with A_t, an overload episode *itself* widens the hysteresis
loop (width ~ a^{3/2}).  The system therefore stays bistable long after the
demand that caused the episode has gone.  That is a mechanistic explanation of
the clinically reported refractory period, and it makes the observable state
sequence non-Markovian in a specific, testable way (P3, P4).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field

import numpy as np

from . import potential as P

__all__ = ["CHMParams", "drive", "splitting", "softplus", "simulate", "STATES"]

STATES = ["calm", "focused", "stuck", "overloaded", "recovering"]

# Safety bound on the latent coordinate.  The cusp's operating range is |x| <~ 3;
# this only prevents the cubic term overflowing on an extreme noise draw.
X_MAX = 8.0


def softplus(z, beta=4.0):
    """Smooth max(0, z); the accumulation nonlinearity for recovery debt."""
    z = np.asarray(z, float)
    return np.where(
        beta * z > 30, z, np.log1p(np.exp(np.clip(beta * z, -30, 30))) / beta
    )


@dataclass
class CHMParams:
    """Free parameters of the CHM model (per subject)."""

    # drive (normal factor) link  b_t = beta0 + beta_S S + beta_T T + beta_U U
    beta0: float = 0.0
    beta_S: float = 0.6
    beta_T: float = 0.3
    beta_U: float = 0.2
    # splitting factor link  a_t = alpha0 + alpha_A A_t
    alpha0: float = 0.4
    alpha_A: float = 1.0
    # relaxation rate: sets the timescale, leaves the geometry untouched
    lam: float = 0.20
    # diffusion
    sigma: float = 0.35
    # slow subsystem
    eps: float = 0.02       # timescale separation (eps << 1)
    kappa: float = 1.0      # debt accumulation gain
    nu: float = 1.0         # debt decay rate  (effective decay = eps * nu)
    x_ref: float = 0.0      # load level above which debt accrues
    # observation model  y_t = c0 + c1 x_t + noise
    c0: float = 0.0
    c1: float = 1.0
    obs_sd: float = 0.2

    names: tuple = field(
        default=(
            "beta0", "beta_S", "beta_T", "beta_U",
            "alpha0", "alpha_A", "lam", "sigma", "eps", "kappa", "nu",
        ),
        repr=False,
        compare=False,
    )

    # -- vector <-> dataclass helpers used by the optimiser ------------------ #
    def to_vector(self, which=None):
        which = which or self.names
        return np.array([getattr(self, n) for n in which], float)

    def with_vector(self, vec, which=None):
        which = which or self.names
        new = CHMParams(**{k: v for k, v in asdict(self).items() if k != "names"})
        for n, v in zip(which, np.asarray(vec, float)):
            setattr(new, n, float(v))
        return new

    def as_dict(self):
        return {k: v for k, v in asdict(self).items() if k != "names"}


# --------------------------------------------------------------------------- #
# link functions
# --------------------------------------------------------------------------- #
def drive(params: CHMParams, S, T, U):
    """b_t -- the normal (asymmetry) factor of the cusp."""
    S, T, U = (np.asarray(v, float) for v in (S, T, U))
    return params.beta0 + params.beta_S * S + params.beta_T * T + params.beta_U * U


def splitting(params: CHMParams, A):
    """a_t -- the splitting (bifurcation) factor of the cusp."""
    return params.alpha0 + params.alpha_A * np.asarray(A, float)


# --------------------------------------------------------------------------- #
# forward simulation (Euler-Maruyama on the fast-slow system)
# --------------------------------------------------------------------------- #
def simulate(params: CHMParams, S, T, U, dt=1.0, x0=None, A0=0.0, rng=None):
    """
    Simulate the CHM system driven by observed covariate series.

    Returns dict with x, A, a, b, and the derived discrete state sequence.
    """
    rng = np.random.default_rng(rng)
    S, T, U = (np.asarray(v, float) for v in (S, T, U))
    n = len(S)

    b = drive(params, S, T, U)
    x = np.empty(n)
    A = np.empty(n)

    A[0] = A0
    a0 = splitting(params, A0)
    if x0 is None:
        lo, _ = P.stable_equilibria(float(a0), float(b[0]))
        x0 = lo
    x[0] = x0

    sq = params.sigma * np.sqrt(dt)
    for t in range(1, n):
        a_prev = params.alpha0 + params.alpha_A * A[t - 1]
        f = -(x[t - 1] ** 3) + a_prev * x[t - 1] + b[t - 1]
        xn = x[t - 1] + params.lam * f * dt + sq * rng.standard_normal()
        # X_MAX is far outside the operating range (|x| <~ 3); it only stops a
        # freak noise draw from sending the cubic term to infinity, and it is
        # applied identically in the likelihood so the two stay consistent.
        x[t] = min(max(xn, -X_MAX), X_MAX)
        dA = params.eps * (
            params.kappa * softplus(x[t - 1] - params.x_ref) - params.nu * A[t - 1]
        )
        A[t] = max(0.0, A[t - 1] + dA * dt)

    a = splitting(params, A)
    return {"x": x, "A": A, "a": a, "b": b}


def observe(params: CHMParams, x, rng=None):
    """Observation model y = c0 + c1 x + N(0, obs_sd^2)."""
    rng = np.random.default_rng(rng)
    x = np.asarray(x, float)
    return params.c0 + params.c1 * x + params.obs_sd * rng.standard_normal(x.shape)
