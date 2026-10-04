"""
CHM -- Cusp-Hysteretic Markov model of sensory-executive overload.

Reference implementation for the paper

    "Identifiability and Early-Warning Reliability of Cusp Catastrophe
     Dynamics in Wearable Electrodermal Recordings"

Modules
-------
potential   closed-form cusp geometry: folds, bistability, Kramers rates
model       parameters, driver links, fast-slow simulator
states      derivation of the five functional states and the transition kernel
estimate    maximum-likelihood fitting, bistability LRT, UKF variant
ews         early-warning indicators and the scaling-exponent tests
baselines   competing models, all scored on held-out predictive log-density
signals     physiological feature extraction with disjoint sensor assignment
datasets    loaders for WESAD, PhysioNet exam stress, Dryad nurse stress
"""

__version__ = "1.0.0"

from . import potential, model, states, estimate, ews, baselines, signals  # noqa: F401

__all__ = ["potential", "model", "states", "estimate", "ews", "baselines", "signals"]
