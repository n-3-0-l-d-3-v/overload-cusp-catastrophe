"""
chm.baselines
=============
Competing models the CHM must beat, all evaluated with the same held-out
one-step-ahead predictive log-density so that the comparison is like-for-like
and does not reward parameter count.

B1  Homogeneous first-order Markov chain over the five states.
    This is the model used in the first draft of this work and, in effect, in
    most descriptive state-transition papers.  It cannot depend on covariates
    and it forces geometric dwell times.

B2  Covariate-driven multinomial logistic (non-homogeneous but memoryless).
    Answers the reviewer question "do you need the dynamical system, or just a
    regression on the same covariates?"

B3  Gaussian hidden Markov model with K latent states.
    The standard latent-state method in cognitive modelling.

B4  Linear (Ornstein-Uhlenbeck) SDE with covariate-driven mean.
    The monostable special case; nested inside the CHM.  This is the honest
    null for "is the cubic term doing any work?"

B5  Gradient-boosted regression on lagged features.
    A deliberately strong black-box upper bound on one-step predictability.  We
    expect it to win on raw prediction; the point of reporting it is that the
    CHM should come close while remaining interpretable and while producing
    thresholds, a hysteresis width and exponents that B5 cannot produce at all.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

__all__ = [
    "markov_chain_loglik",
    "multinomial_logistic_loglik",
    "hmm_loglik",
    "ou_fit_predict",
    "gbm_predict_loglik",
    "gaussian_loglik",
]

_EPS = 1e-12


def gaussian_loglik(resid, sd):
    """Mean per-step Gaussian log-density -- the common currency of comparison."""
    resid = np.asarray(resid, float)
    sd = max(float(sd), 1e-6)
    return float(np.mean(-0.5 * resid**2 / sd**2 - 0.5 * np.log(2 * np.pi * sd**2)))


# --------------------------------------------------------------------------- #
# B1 homogeneous Markov chain
# --------------------------------------------------------------------------- #
def markov_chain_loglik(train_states, test_states, n_states=5, laplace=1.0):
    """Mean held-out log-probability per transition under a counted chain."""
    train_states = np.asarray(train_states, int)
    test_states = np.asarray(test_states, int)

    C = np.full((n_states, n_states), float(laplace))
    for i in range(len(train_states) - 1):
        C[train_states[i], train_states[i + 1]] += 1.0
    Pm = C / C.sum(axis=1, keepdims=True)

    ll = [np.log(max(Pm[test_states[i], test_states[i + 1]], _EPS))
          for i in range(len(test_states) - 1)]
    return float(np.mean(ll)) if ll else np.nan


# --------------------------------------------------------------------------- #
# B2 covariate-driven multinomial logistic
# --------------------------------------------------------------------------- #
def multinomial_logistic_loglik(Xtr, ytr, Xte, yte, n_states=5):
    """Next-state ~ current covariates + current state (one-hot)."""
    from sklearn.linear_model import LogisticRegression

    Xtr, Xte = np.asarray(Xtr, float), np.asarray(Xte, float)
    ytr, yte = np.asarray(ytr, int), np.asarray(yte, int)
    if len(np.unique(ytr)) < 2:
        return np.nan

    # NB: no multi_class= argument. It was deprecated and removed in
    # scikit-learn 1.7; passing it raises TypeError, which was silently
    # swallowed by the caller's except-block and left this baseline reporting
    # nothing at all. Multinomial is the default for multiclass targets with
    # the lbfgs solver, so the behaviour is unchanged.
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)
    cls = list(clf.classes_)

    ll = []
    for i, y in enumerate(yte):
        j = cls.index(y) if y in cls else None
        ll.append(np.log(max(proba[i, j], _EPS)) if j is not None else np.log(_EPS))
    return float(np.mean(ll))


# --------------------------------------------------------------------------- #
# B3 Gaussian HMM
# --------------------------------------------------------------------------- #
def hmm_loglik(train_obs, test_obs, n_components=5, seed=0):
    """Per-sample held-out log-likelihood of a Gaussian HMM."""
    try:
        from hmmlearn.hmm import GaussianHMM
    except ImportError:
        return np.nan

    tr = np.asarray(train_obs, float).reshape(len(train_obs), -1)
    te = np.asarray(test_obs, float).reshape(len(test_obs), -1)
    try:
        m = GaussianHMM(n_components=n_components, covariance_type="diag",
                        n_iter=200, random_state=seed)
        m.fit(tr)
        return float(m.score(te) / len(te))
    except Exception:
        return np.nan


# --------------------------------------------------------------------------- #
# B4 linear OU with covariate-driven mean  (the monostable null)
# --------------------------------------------------------------------------- #
def ou_fit_predict(x_tr, C_tr, x_te, C_te, dt=1.0):
    """
    dx = theta (mu(C) - x) dt + s dW, with mu(C) = c0 + c' C.

    Fitted by OLS on the Euler increments, which is the exact MLE for this
    (conditionally linear) model.  Returns the held-out predictive log-density.
    """
    x_tr, x_te = np.asarray(x_tr, float), np.asarray(x_te, float)
    C_tr, C_te = np.asarray(C_tr, float), np.asarray(C_te, float)

    # dx = (-theta) x dt + (theta c0) dt + (theta c') C dt
    D = np.column_stack([x_tr[:-1], np.ones(len(x_tr) - 1), C_tr[:-1]])
    dx = x_tr[1:] - x_tr[:-1]
    coef, *_ = np.linalg.lstsq(D * dt, dx, rcond=None)
    resid_tr = dx - (D * dt) @ coef
    sd = np.sqrt(max(np.mean(resid_tr**2), 1e-9))

    Dte = np.column_stack([x_te[:-1], np.ones(len(x_te) - 1), C_te[:-1]])
    resid = (x_te[1:] - x_te[:-1]) - (Dte * dt) @ coef
    return {"loglik": gaussian_loglik(resid, sd), "coef": coef, "sd": float(sd)}


# --------------------------------------------------------------------------- #
# B5 gradient boosting on lagged features
# --------------------------------------------------------------------------- #
def gbm_predict_loglik(Xtr, ytr, Xte, yte, seed=0):
    """Strong black-box reference for one-step-ahead prediction of the load."""
    from sklearn.ensemble import HistGradientBoostingRegressor

    m = HistGradientBoostingRegressor(max_iter=300, random_state=seed)
    m.fit(np.asarray(Xtr, float), np.asarray(ytr, float))
    pred_tr = m.predict(np.asarray(Xtr, float))
    sd = np.sqrt(max(np.mean((np.asarray(ytr, float) - pred_tr) ** 2), 1e-9))
    resid = np.asarray(yte, float) - m.predict(np.asarray(Xte, float))
    return {"loglik": gaussian_loglik(resid, sd), "rmse": float(np.sqrt(np.mean(resid**2)))}
