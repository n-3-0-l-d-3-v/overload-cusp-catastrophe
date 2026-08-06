"""
Correctness tests for the closed-form cusp geometry.

These are not smoke tests.  Every analytic claim the paper makes about the
potential is checked here against an independent numerical computation, so that
a reviewer can see the derivations are right rather than take them on trust.
"""

import numpy as np
import pytest

from chm import potential as P


# --------------------------------------------------------------------------- #
# equilibria and folds
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("a,b", [(1.0, 0.0), (2.0, 0.1), (0.5, 0.05), (3.0, -0.4)])
def test_equilibria_are_roots_of_the_drift(a, b):
    eq = P.equilibria(a, b)
    eq = eq[~np.isnan(eq)]
    assert eq.size >= 1
    assert np.allclose(P.drift(eq, a, b), 0.0, atol=1e-8)


def test_monostable_below_the_cusp():
    """a <= 0 admits exactly one equilibrium for every drive."""
    for a in (-1.0, -0.2, 0.0):
        for b in (-2.0, -0.3, 0.0, 0.3, 2.0):
            eq = P.equilibria(a, b)
            assert np.sum(~np.isnan(eq)) == 1
            assert not P.is_bistable(a, b)


def test_fold_drive_matches_the_discriminant_boundary():
    """
    b_c(a) = 2/(3 sqrt 3) a^{3/2} must be exactly where D = 4a^3 - 27b^2 changes
    sign.  This is the single most load-bearing formula in the paper.
    """
    for a in (0.3, 1.0, 2.5, 4.0):
        bc = float(P.fold_drive(np.array([a]))[0])
        assert P.discriminant(a, bc * 0.999) > 0     # inside  -> bistable
        assert P.discriminant(a, bc * 1.001) < 0     # outside -> monostable
        assert P.discriminant(a, bc) == pytest.approx(0.0, abs=1e-9)


def test_fold_points_are_where_curvature_vanishes():
    """At the fold the stable and unstable equilibria merge: V'' = 0 at x = +-sqrt(a/3)."""
    for a in (0.5, 1.0, 3.0):
        x_fold = np.sqrt(a / 3.0)
        assert P.curvature(x_fold, a) == pytest.approx(0.0, abs=1e-12)
        assert P.curvature(-x_fold, a) == pytest.approx(0.0, abs=1e-12)


def test_hysteresis_width_follows_the_three_halves_law():
    """
    PREDICTION P1.  Doubling a must multiply the loop width by 2^{1.5}.
    A regression of log-width on log-a must return a slope of exactly 1.5.
    """
    a = np.linspace(0.2, 4.0, 60)
    w = P.hysteresis_width(a)
    slope = np.polyfit(np.log(a), np.log(w), 1)[0]
    assert slope == pytest.approx(1.5, abs=1e-6)
    assert P.hysteresis_width(np.array([4.0]))[0] == pytest.approx(
        2 ** 1.5 * P.hysteresis_width(np.array([2.0]))[0], rel=1e-9
    )


def test_no_hysteresis_without_bistability():
    assert np.all(P.hysteresis_width(np.array([-1.0, -0.1, 0.0])) == 0.0)


# --------------------------------------------------------------------------- #
# the early-warning scaling exponents
# --------------------------------------------------------------------------- #
def test_relaxation_rate_vanishes_at_the_fold():
    """Critical slowing down, in closed form."""
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    rates = []
    for frac in (0.5, 0.9, 0.99, 0.999):
        lo, _ = P.stable_equilibria(a, bc * frac)
        rates.append(P.relaxation_rate(lo, a))
    assert all(r > 0 for r in rates)
    assert rates == sorted(rates, reverse=True)      # monotone decrease
    assert rates[-1] < 0.05 * rates[0]


def test_relaxation_rate_has_square_root_scaling_near_the_fold():
    """
    PREDICTION P2, upstream half: lambda ~ mu^{1/2} with mu = b_c - b.
    Everything the paper says about Var ~ mu^{-1/2} follows from this exponent,
    so it is worth pinning down directly.
    """
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    mu = np.logspace(-5, -2, 40)
    lam = np.array([P.relaxation_rate(P.stable_equilibria(a, bc - m)[0], a) for m in mu])
    slope = np.polyfit(np.log(mu), np.log(lam), 1)[0]
    assert slope == pytest.approx(0.5, abs=0.02)


def test_variance_and_ac1_inherit_the_predicted_exponents():
    """Var ~ mu^{-1/2} and -log AC1 ~ mu^{+1/2}."""
    a, sigma = 2.0, 0.3
    bc = float(P.fold_drive(np.array([a]))[0])
    mu = np.logspace(-5, -2, 40)
    lam = np.array([P.relaxation_rate(P.stable_equilibria(a, bc - m)[0], a) for m in mu])

    var_slope = np.polyfit(np.log(mu), np.log(P.ou_variance(lam, sigma)), 1)[0]
    ac1_slope = np.polyfit(np.log(mu), np.log(-np.log(P.ou_ac1(lam, 1.0))), 1)[0]

    assert var_slope == pytest.approx(-0.5, abs=0.02)
    assert ac1_slope == pytest.approx(+0.5, abs=0.02)


# --------------------------------------------------------------------------- #
# barrier crossing
# --------------------------------------------------------------------------- #
def test_barrier_shrinks_as_the_drive_approaches_the_fold():
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    heights = [P.barrier_height(a, bc * f, "up") for f in (0.3, 0.6, 0.9, 0.99)]
    assert all(h > 0 for h in heights)
    assert heights == sorted(heights, reverse=True)


def test_kramers_rate_increases_with_drive_and_with_noise():
    a = 2.0
    bc = float(P.fold_drive(np.array([a]))[0])
    r_low = P.kramers_rate(a, 0.3 * bc, 0.3, "up")
    r_high = P.kramers_rate(a, 0.9 * bc, 0.3, "up")
    assert r_high > r_low
    assert P.kramers_rate(a, 0.5 * bc, 0.6, "up") > P.kramers_rate(a, 0.5 * bc, 0.3, "up")


def test_saddle_lies_between_the_two_stable_states():
    a, b = 2.0, 0.1
    lo, hi = P.stable_equilibria(a, b)
    s = P.saddle(a, b)
    assert lo < s < hi
    assert P.curvature(lo, a) > 0 and P.curvature(hi, a) > 0
    assert P.curvature(s, a) < 0
