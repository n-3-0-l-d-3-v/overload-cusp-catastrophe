"""
demo.py
=======
A five-minute demonstration that the model works, end to end, on data where
the ground truth is known.

This exists because "the model works" and "the model found something in my
data" are different claims, and only the first is demonstrable here. It
simulates a system that genuinely has a cusp, recovers the parameters, recovers
the five functional states, shows the hysteresis loop and the early-warning
rise, and then runs the same pipeline on a random walk to show it returns
nothing.

    python experiments/demo.py

Writes figures/demo_walkthrough.png.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from chm import potential as P                                  # noqa: E402
from chm import ews as E                                        # noqa: E402
from chm.model import CHMParams, simulate, STATES               # noqa: E402
from chm.estimate import fit_mle, latent_path, rw_surrogate_test  # noqa: E402
from chm.states import assign_states, empirical_transition_matrix  # noqa: E402

FIGS = Path(__file__).resolve().parents[2] / "figures"
FIGS.mkdir(exist_ok=True, parents=True)

COL = {"calm": "#4C72B0", "focused": "#55A868", "stuck": "#DD8452",
       "overloaded": "#C44E52", "recovering": "#8172B3"}


def smooth(n, rng, k=40):
    z = rng.standard_normal(n + k)
    s = np.convolve(z, np.ones(k) / k, mode="valid")[:n]
    return (s - s.mean()) / (s.std() + 1e-9)


def main():
    rng = np.random.default_rng(20260722)
    n = 1500

    print("=" * 66)
    print("CHM demonstration")
    print("=" * 66)

    # ---------------- 1. simulate a system that really has a cusp --------- #
    S, T, U = smooth(n, rng), smooth(n, rng), smooth(n, rng)
    true = CHMParams(beta0=-0.05, beta_S=0.65, beta_T=0.25, beta_U=0.15,
                     alpha0=1.30, alpha_A=0.55, lam=0.18, sigma=0.30, eps=0.03)
    sim = simulate(true, S, T, U, rng=rng)
    x = sim["x"]

    print("\n1. Simulated a system with known cusp dynamics")
    print(f"   n = {n},  lag-1 autocorrelation = "
          f"{np.corrcoef(x[:-1], x[1:])[0, 1]:.3f}")

    # ---------------- 2. recover the parameters --------------------------- #
    fit = fit_mle(x, S, T, U)
    est = fit["params"]
    print("\n2. Recovered the parameters (profiled least squares)")
    print(f"   {'param':8s} {'true':>8s} {'estimated':>10s}")
    for k in ("beta_S", "beta_T", "beta_U", "alpha0", "alpha_A", "lam", "sigma"):
        print(f"   {k:8s} {getattr(true, k):8.3f} {getattr(est, k):10.3f}")
    print(f"   cusp identified: {fit['cusp_identified']}")

    # ---------------- 3. derive the states -------------------------------- #
    A, a, b = latent_path(x, S, T, U, est)
    st = assign_states(x, a, b)
    print("\n3. Derived the five functional states from the fitted geometry")
    for s in STATES:
        print(f"   {s:11s} {np.mean(st == s):6.1%}")

    # ---------------- 4. the calibrated test on both inputs --------------- #
    print("\n4. Surrogate-calibrated test")
    r_cusp = rw_surrogate_test(x, S, T, U, n_surr=150, rng=rng,
                               statistics=("lam_t",))
    rw = np.cumsum(rng.standard_normal(n) * float(np.std(np.diff(x))))
    rw = (rw - rw.mean()) / rw.std() * float(np.std(x))
    r_rw = rw_surrogate_test(rw, S, T, U, n_surr=150, rng=rng,
                             statistics=("lam_t",))
    print(f"   true cusp   -> p = {r_cusp['lam_t']['p']:.4f}   "
          f"{'DETECTED' if r_cusp['lam_t']['p'] < 0.05 else 'not detected'}")
    print(f"   random walk -> p = {r_rw['lam_t']['p']:.4f}   "
          f"{'DETECTED' if r_rw['lam_t']['p'] < 0.05 else 'correctly rejected'}")

    # ---------------- 5. figure ------------------------------------------- #
    fig, axes = plt.subplots(2, 2, figsize=(7.16, 4.6), constrained_layout=True)

    ax = axes[0, 0]
    t = np.arange(n)
    for s in STATES:
        m = st == s
        if m.any():
            ax.scatter(t[m], x[m], s=1.2, color=COL[s], label=s)
    ax.set_xlabel("time step")
    ax.set_ylabel("load $x_t$")
    ax.set_title("(a) simulated load, coloured by derived state", fontsize=8)
    ax.legend(frameon=False, fontsize=5.5, markerscale=4, ncol=2)

    ax = axes[0, 1]
    ax.plot(t, a, color="#333", lw=0.8, label=r"$a_t$ (capacity depletion)")
    ax.plot(t, b, color="#C44E52", lw=0.6, alpha=0.7, label=r"$b_t$ (demand)")
    ax.plot(t, P.fold_drive(a), "--", color="#4C72B0", lw=0.8,
            label=r"fold $b_c(a_t)$")
    ax.set_xlabel("time step")
    ax.set_title("(b) control parameters and the moving threshold", fontsize=8)
    ax.legend(frameon=False, fontsize=5.5)

    ax = axes[1, 0]
    up = np.isin(st, ["overloaded", "recovering"])
    entry = [b[i] for i in range(1, n) if up[i] and not up[i - 1]]
    exit_ = [b[i] for i in range(1, n) if up[i - 1] and not up[i]]
    if entry and exit_:
        ax.hist(entry, bins=20, alpha=0.65, color=COL["overloaded"],
                label=f"entry (mean {np.mean(entry):.2f})")
        ax.hist(exit_, bins=20, alpha=0.65, color=COL["recovering"],
                label=f"exit (mean {np.mean(exit_):.2f})")
        ax.legend(frameon=False, fontsize=6)
    ax.set_xlabel(r"drive $b$ at basin change")
    ax.set_ylabel("count")
    ax.set_title("(c) hysteresis: exit threshold below entry", fontsize=8)

    ax = axes[1, 1]
    win = 40
    xd = E.detrend(x, win)
    var = E.rolling_variance(xd, win)
    mu = P.distance_to_fold(a, b)
    m = np.isfinite(var) & np.isfinite(mu) & (mu > 1e-3) & (var > 0)
    if m.sum() > 20:
        ax.scatter(mu[m], var[m], s=1.5, alpha=0.35, color="#333")
        f = E.fit_scaling_exponent(mu, var, predicted=-0.5, rng=rng, n_boot=500)
        xs = np.logspace(np.log10(mu[m].min()), np.log10(mu[m].max()), 50)
        ax.plot(xs, np.exp(np.log(xs) * f["gamma"] + np.log(np.median(var[m]))
                           - f["gamma"] * np.log(np.median(mu[m]))),
                color="#C44E52", lw=1.2,
                label=f"fitted {f['gamma']:+.2f}")
        ax.plot(xs, np.exp(np.log(xs) * -0.5 + np.log(np.median(var[m]))
                           + 0.5 * np.log(np.median(mu[m]))),
                "--", color="#4C72B0", lw=1.0, label="predicted $-1/2$")
        ax.legend(frameon=False, fontsize=6)
        print(f"\n5. Early-warning exponent: {f['gamma']:+.3f} "
              f"[{f['ci'][0]:+.3f}, {f['ci'][1]:+.3f}], predicted -0.500")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"distance to fold $\mu$")
    ax.set_ylabel("rolling variance")
    ax.set_title("(d) early-warning scaling law", fontsize=8)

    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"demo_walkthrough.{ext}", dpi=300)
    plt.close(fig)
    print(f"\nwrote figures/demo_walkthrough.png")
    print("=" * 66)


if __name__ == "__main__":
    main()
