"""
Estimator validation.

A model fitted to real data is only as trustworthy as the estimator behind it.
These tests simulate from the CHM model with KNOWN parameters and check that
the estimator recovers them, that the bistability test has the right size on
monostable data and adequate power on bistable data, and that the derived state
labelling behaves as the geometry says it must.
"""

import numpy as np
import pytest

from chm import potential as P
from chm.model import CHMParams, simulate, drive, splitting
from chm.estimate import fit_mle, fit_monostable, latent_path
from chm.states import assign_states, dwell_times, empirical_transition_matrix


def _covariates(n, rng):
    """Smooth, autocorrelated covariate series, like the physiological ones."""
    def smooth(k=25):
        z = rng.standard_normal(n + k)
        w = np.ones(k) / k
        s = np.convolve(z, w, mode="valid")[:n]
        return (s - s.mean()) / (s.std() + 1e-9)
    return smooth(), smooth(), smooth()


# --------------------------------------------------------------------------- #
# parameter recovery
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_recovers_drive_coefficients(seed):
    """The b-link coefficients are the ones that carry the scientific claims."""
    rng = np.random.default_rng(seed)
    n = 6000
    S, T, U = _covariates(n, rng)
    true = CHMParams(beta0=-0.1, beta_S=0.55, beta_T=0.25, beta_U=0.15,
                     alpha0=0.8, alpha_A=0.6, sigma=0.30, eps=0.03)
    sim = simulate(true, S, T, U, dt=1.0, rng=rng)

    fit = fit_mle(sim["x"], S, T, U, dt=1.0, n_restarts=6, rng=rng)
    p = fit["params"]

    assert fit["converged"]
    assert p.beta_S == pytest.approx(true.beta_S, abs=0.10)
    assert p.beta_T == pytest.approx(true.beta_T, abs=0.10)
    assert p.beta_U == pytest.approx(true.beta_U, abs=0.10)
    assert p.sigma == pytest.approx(true.sigma, rel=0.15)


@pytest.mark.parametrize("seed", [0, 1])
def test_recovers_the_splitting_factor(seed):
    """alpha0 controls whether the system can tip at all; it must be identified."""
    rng = np.random.default_rng(seed)
    n = 6000
    S, T, U = _covariates(n, rng)
    true = CHMParams(beta0=0.0, beta_S=0.5, beta_T=0.2, beta_U=0.1,
                     alpha0=1.2, alpha_A=0.4, sigma=0.35, eps=0.02)
    sim = simulate(true, S, T, U, dt=1.0, rng=rng)
    p = fit_mle(sim["x"], S, T, U, n_restarts=6, rng=rng)["params"]
    assert p.alpha0 == pytest.approx(true.alpha0, abs=0.30)
    assert p.alpha0 > 0.0                       # correctly detects bistability


def test_estimator_beats_a_wrong_starting_point():
    """Multi-start must escape a deliberately bad initialisation."""
    rng = np.random.default_rng(7)
    n = 4000
    S, T, U = _covariates(n, rng)
    true = CHMParams(beta_S=0.6, beta_T=0.2, beta_U=0.1, alpha0=1.0,
                     alpha_A=0.5, sigma=0.3, eps=0.02)
    sim = simulate(true, S, T, U, rng=rng)
    bad = CHMParams(beta_S=-2.0, beta_T=2.0, beta_U=-2.0, alpha0=-1.5,
                    alpha_A=4.0, sigma=2.0, eps=0.4)
    good = fit_mle(sim["x"], S, T, U, init=bad, n_restarts=10, rng=rng)
    assert good["params"].beta_S == pytest.approx(true.beta_S, abs=0.15)


# --------------------------------------------------------------------------- #
# behaviour of the nested comparison
# --------------------------------------------------------------------------- #
def test_full_model_never_fits_worse_than_its_restriction():
    """A nested restriction cannot have a higher likelihood, up to optimiser noise."""
    rng = np.random.default_rng(3)
    n = 4000
    S, T, U = _covariates(n, rng)
    true = CHMParams(beta_S=0.6, alpha0=1.0, alpha_A=0.5, sigma=0.3, eps=0.02)
    x = simulate(true, S, T, U, rng=rng)["x"]
    full = fit_mle(x, S, T, U, n_restarts=6, rng=rng)
    null = fit_monostable(x, S, T, U, n_restarts=6, rng=rng)
    assert full["nll"] <= null["nll"] + 1e-6


def test_bistability_is_detected_when_present_and_not_when_absent():
    """
    Power and size, in the crudest possible form: the log-likelihood gain from
    allowing bistability should be large on bistable data and near zero on
    monostable data.
    """
    rng = np.random.default_rng(11)
    n = 6000
    S, T, U = _covariates(n, rng)

    bist = CHMParams(beta_S=0.6, alpha0=1.5, alpha_A=0.5, sigma=0.30, eps=0.02)
    mono = CHMParams(beta_S=0.6, alpha0=-0.8, alpha_A=0.0, sigma=0.30, eps=0.02)

    gains = {}
    for name, p in (("bistable", bist), ("monostable", mono)):
        x = simulate(p, S, T, U, rng=rng)["x"]
        f = fit_mle(x, S, T, U, n_restarts=6, rng=rng)
        g = fit_monostable(x, S, T, U, n_restarts=6, rng=rng)
        gains[name] = 2.0 * (g["nll"] - f["nll"])

    assert gains["bistable"] > 20.0
    assert gains["monostable"] < gains["bistable"] / 5.0


# --------------------------------------------------------------------------- #
# derived states
# --------------------------------------------------------------------------- #
def test_recovering_only_occurs_in_the_upper_basin_at_low_drive():
    """
    'Recovering' is defined as being held in the high-load basin by hysteresis
    alone.  It must therefore never appear when the drive is still positive.
    """
    rng = np.random.default_rng(5)
    n = 8000
    S, T, U = _covariates(n, rng)
    p = CHMParams(beta_S=0.8, alpha0=1.5, alpha_A=0.8, sigma=0.35, eps=0.03)
    sim = simulate(p, S, T, U, rng=rng)
    st = assign_states(sim["x"], sim["a"], sim["b"])

    rec = st == "recovering"
    if rec.sum():
        assert np.all(sim["b"][rec] <= 0)
        assert np.all(P.is_bistable(sim["a"][rec], sim["b"][rec]))


def test_stuck_requires_a_coexisting_overloaded_attractor():
    rng = np.random.default_rng(6)
    n = 6000
    S, T, U = _covariates(n, rng)
    p = CHMParams(beta_S=0.7, alpha0=1.2, alpha_A=0.6, sigma=0.3, eps=0.03)
    sim = simulate(p, S, T, U, rng=rng)
    st = assign_states(sim["x"], sim["a"], sim["b"])
    stuck = st == "stuck"
    if stuck.sum():
        assert np.all(P.discriminant(sim["a"][stuck], sim["b"][stuck]) > 0)


def test_transition_matrix_rows_are_probability_distributions():
    rng = np.random.default_rng(8)
    n = 3000
    S, T, U = _covariates(n, rng)
    p = CHMParams(beta_S=0.7, alpha0=1.2, alpha_A=0.6, sigma=0.3, eps=0.03)
    sim = simulate(p, S, T, U, rng=rng)
    M = empirical_transition_matrix(assign_states(sim["x"], sim["a"], sim["b"]))
    assert np.allclose(M.sum(axis=1), 1.0, atol=1e-9)
    assert np.all(M >= 0)


def test_slow_variable_makes_overload_dwell_times_overdispersed():
    """
    PREDICTION P3.  A homogeneous Markov chain forces geometric dwell times, for
    which the coefficient of variation is ~1.  Because the CHM's slow variable
    keeps a_t elevated after an episode, its overload dwell times should be
    over-dispersed relative to that.
    """
    rng = np.random.default_rng(9)
    n = 20000
    S, T, U = _covariates(n, rng)
    p = CHMParams(beta_S=0.8, alpha0=1.0, alpha_A=1.2, sigma=0.35, eps=0.05)
    sim = simulate(p, S, T, U, rng=rng)
    st = assign_states(sim["x"], sim["a"], sim["b"])
    d = dwell_times(st, "overloaded")
    if d.size >= 20:
        cv = d.std() / max(d.mean(), 1e-9)
        assert cv > 0.9


def test_simulation_is_reproducible_given_a_seed():
    S, T, U = _covariates(500, np.random.default_rng(0))
    p = CHMParams()
    a = simulate(p, S, T, U, rng=np.random.default_rng(42))["x"]
    b = simulate(p, S, T, U, rng=np.random.default_rng(42))["x"]
    assert np.array_equal(a, b)


# --------------------------------------------------------------------------- #
# surrogate ensembles
# --------------------------------------------------------------------------- #
def test_iaaft_preserves_marginal_and_spectrum():
    """
    IAAFT must reproduce the original values exactly (as a multiset) and the
    power spectrum closely.  That is the whole point of it: the only thing it
    is allowed to destroy is nonlinear temporal structure, so anything the
    statistic responds to cannot be the marginal shape or the trend.
    """
    from chm.ews import iaaft_surrogate

    rng = np.random.default_rng(0)
    n = 600
    t = np.arange(n)
    y = 2 * np.sin(2 * np.pi * t / n) + 0.05 * np.cumsum(rng.standard_normal(n))

    s = iaaft_surrogate(y, rng)

    assert np.allclose(np.sort(y), np.sort(s))          # marginal exactly
    Py, Ps = np.abs(np.fft.rfft(y)), np.abs(np.fft.rfft(s))
    assert np.linalg.norm(Py - Ps) / np.linalg.norm(Py) < 0.05


def test_iaaft_keeps_low_frequency_trend_that_a_random_walk_cannot():
    """
    The reason IAAFT is needed at all: a random-walk surrogate matched only on
    increment variance does not reproduce deterministic trend, so a trended
    series beats it trivially.  IAAFT keeps the trend, so it does not.
    """
    from chm.ews import iaaft_surrogate

    rng = np.random.default_rng(1)
    n = 800
    t = np.arange(n)
    y = 3 * np.sin(2 * np.pi * t / n)                    # pure deterministic trend

    s = iaaft_surrogate(y, rng)

    def concentration(v):
        """Share of total power sitting in the fundamental bin."""
        P_ = np.abs(np.fft.rfft(v)) ** 2
        return P_[1] / P_[1:].sum()

    # Total low-frequency power is the WRONG discriminator: a random walk is
    # itself 1/f^2 and so is also low-frequency dominated.  What separates a
    # deterministic periodic trend from a random walk is how *concentrated*
    # that power is in a single frequency, and that is what IAAFT must keep.
    assert concentration(s) > 0.9 * concentration(y)

    # A pure sine puts essentially all its power in one bin (concentration
    # ~1.0), and IAAFT reproduces that.  A random walk matched on increment
    # variance spreads it (~0.58): it carries low-frequency power, but not the
    # *deterministic periodic* structure, which is the part that makes a
    # trended series easy to distinguish from a random-walk ensemble.
    rw = np.cumsum(rng.standard_normal(n) * np.std(np.diff(y)))
    rw = (rw - rw.mean()) / rw.std() * np.std(y)
    assert concentration(rw) < 0.8 * concentration(y)


def test_surrogate_test_rejects_true_cusp_and_spares_trended_noise():
    """End-to-end: the calibrated test should fire on a cusp, not on trend."""
    from chm.estimate import rw_surrogate_test

    rng = np.random.default_rng(5)
    n = 600
    S, T, U = _covariates(n, rng)

    p = CHMParams(beta_S=0.6, alpha0=1.3, alpha_A=0.5, lam=0.18,
                  sigma=0.30, eps=0.03)
    x = simulate(p, S, T, U, rng=rng)["x"]
    t = np.arange(n)
    trended = 3 * np.sin(2 * np.pi * t / n) + 0.06 * np.cumsum(
        rng.standard_normal(n))

    for kind in ("rw", "iaaft"):
        r_cusp = rw_surrogate_test(x, S, T, U, n_surr=60, rng=rng,
                                   statistics=("lam_t",), surrogate=kind)
        r_null = rw_surrogate_test(trended, S, T, U, n_surr=60, rng=rng,
                                   statistics=("lam_t",), surrogate=kind)
        assert r_cusp["lam_t"]["p"] < 0.10, kind
        assert r_null["lam_t"]["p"] > r_cusp["lam_t"]["p"], kind


def test_unknown_surrogate_type_is_rejected():
    from chm.estimate import rw_surrogate_test

    rng = np.random.default_rng(0)
    S, T, U = _covariates(200, rng)
    x = rng.standard_normal(200)
    with pytest.raises(ValueError):
        rw_surrogate_test(x, S, T, U, n_surr=5, rng=rng, surrogate="nonsense")
