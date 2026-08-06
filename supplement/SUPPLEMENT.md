# Supplementary material

Everything the 5-page conference paper compresses. This is the working document
for the journal version and the place to look when a reviewer asks "how do you
know that?"

Generated from the analysis in `code/`. Every number here has a CSV behind it in
`results/`. Nothing is quoted from memory.

---

## S1. Why a cusp, and not something simpler

The phenomenon to be explained has two features that a linear or additive model
cannot produce together:

1. **Sudden onset.** Load does not rise in proportion to demand. People describe
   a threshold being crossed.
2. **Delayed recovery.** Removing the demand does not restore function. The
   system stays down until demand falls well below the level that caused the
   episode.

An additive model, load = w1·sensory + w2·cognitive + ..., with a threshold,
gives you (1) by fiat and cannot give you (2) at all: cross back over the
threshold and you are immediately fine again. To get both from one mechanism you
need the system to have *two coexisting stable states* over some range of
demand. That is bistability, and the cusp is the minimal smooth geometry that
produces it with two control parameters.

The move that makes it a scientific claim rather than a metaphor: regulatory
capacity enters as the **splitting factor** `a`, not as another additive load
term. Capacity does not push you up the load axis. It decides whether a second
attractor exists at all.

| | additive model | cusp model |
|---|---|---|
| onset | assumed threshold | fold bifurcation |
| recovery lag | not predicted | hysteresis, width `(4/3√3)·a^{3/2}` |
| slowing near threshold | not predicted | `λ_rel → 0`, a theorem |
| "stuck" / "recovering" | vocabulary | geometric regions |
| free parameters in kernel | 20 counted | 9 interpretable |
| can it be refuted? | no | yes, by exponents |

---

## S2. The five states, precisely

Let `B = 4a³ − 27b²` (positive iff two basins coexist), and let `x_s` be the
saddle.

| State | Condition |
|---|---|
| calm | lower basin, `B ≤ 0`, `b ≤ b̃` |
| focused | lower basin, `B ≤ 0`, `b > b̃` |
| **stuck** | lower basin, `B > 0` (an overloaded attractor coexists) |
| overloaded | upper basin, `b > 0` |
| **recovering** | upper basin, `B > 0`, `b ≤ 0` |

`b̃` is the within-series median drive.

The two bolded rows are the contribution. "Stuck" means still functioning while
one perturbation from tipping. "Recovering" means still in the high-load basin
although demand has already fallen below the level that would have put you
there, so you are held up by hysteresis alone. Both words appear constantly in
qualitative accounts of autistic overload. Neither had a formal definition
before.

---

## S3. Estimator derivation

Expanding the drift of the discrete-time model:

```
Δx_t = λ(−x_t³ + a_t x_t + b_t)·dt + σ√dt·ε_t
     = θ₁(−x_t³) + θ₂x_t + θ₃(A_t x_t) + θ₄ + θ₅S_t + θ₆T_t + θ₇U_t + η
```

with `θ₁ = λ`, `θ₂ = λα₀`, `θ₃ = λα_A`, `θ₄..₇ = λβ₀..U`.

`A_t` depends only on `ε`, so **conditional on ε the whole thing is OLS**. The
fit is a one-dimensional profile search over `ε` with an exact linear solve
inside. No bounds, no starting values, no local optima, no discretisation bias
(the Euler map *is* the model, not an approximation to it).

**This replaced** a bounded 9-parameter quasi-Newton fit that returned estimates
pinned at three separate bounds simultaneously. Diagnosis: only the products
`λa` and `λb` enter the drift, so a joint search wanders a ridge. In the
reparameterisation the ridge is gone.

Constraint `θ₁ ≥ 0`: a negative cubic coefficient is not a badly-fitted cusp, it
is outside the model, and it flips the signs of `a = θ₂/θ₁` and `b = θ₄/θ₁`.
Units where the constraint binds are **kept in the denominator**, never dropped,
because dropping them is exactly the survivorship bias that manufactures
positive results.

---

## S4. Identifiability (the load-bearing result)

`m1_recovery_summary.csv`, 600 replicates per cell, 3,600 synthetic series.

Correlation between true and estimated parameter:

| Parameter | n=100 | n=150 | n=200 | n=300 | n=500 | n=1000 |
|---|---|---|---|---|---|---|
| λ relaxation | 0.824 | 0.906 | **0.912** | 0.958 | 0.978 | 0.971 |
| σ diffusion | 0.963 | 0.975 | **0.953** | 0.988 | 0.994 | 0.988 |
| β_S sensory | 0.330 | 0.366 | 0.215 | 0.608 | 0.803 | 0.645 |
| β_T switch | 0.208 | 0.199 | 0.256 | 0.616 | 0.738 | 0.822 |
| β_U uncertainty | 0.213 | 0.162 | 0.288 | 0.516 | 0.649 | 0.696 |
| β₀ intercept | 0.175 | 0.181 | 0.138 | 0.444 | 0.616 | 0.677 |
| α₀ splitting | 0.015 | 0.075 | 0.056 | 0.500 | 0.662 | 0.594 |
| α_A debt gain | 0.052 | −0.033 | −0.066 | 0.036 | 0.073 | 0.162 |
| ε slow rate | 0.013 | 0.067 | 0.065 | 0.127 | 0.205 | 0.268 |

**Read this table before believing any cusp result on wearable data.**

At n=200 (the median in these corpora) only λ and σ are identified. The
splitting factor, which is the entire scientific content of the model, is at
r = 0.06. It is not measured. It is noise.

Consequence: `a = θ₂/θ₁` inflates without bound as `θ₁ → 0`. In the real fits
the median `λ̂` is **0.0059**, and the median recovered `α̂₀` is **12**, which
would put attractors at roughly ±2 on a unit-variance coordinate. Those are not
weakly bistable people. They are people with no restoring cubic term, divided by
a number close to zero.

The real `λ̂` is *below the entire simulated range*. The recordings sit further
into non-identifiability than any of the 3,600 synthetic series used to map it.

**α_A never becomes identified**, even at n=1000 (r=0.16). Any claim resting on
the recovery-debt gain is unsupported at any length we tested.

---

## S5. Test size and power

`m2_size_summary.csv`: 12,000 random-walk replicates (nominal), 3,000
(calibrated).

| n | nominal size | 95% CI | calibrated size | 95% CI |
|---|---|---|---|---|
| 100 | 0.368 | [0.347, 0.389] | 0.056 | [0.039, 0.080] |
| 150 | 0.404 | [0.382, 0.425] | 0.056 | [0.039, 0.080] |
| 200 | 0.422 | [0.400, 0.443] | 0.056 | [0.039, 0.080] |
| 300 | 0.429 | [0.407, 0.450] | 0.060 | [0.042, 0.084] |
| 500 | 0.455 | [0.433, 0.477] | 0.050 | [0.034, 0.073] |
| 1000 | 0.444 | [0.422, 0.465] | 0.064 | [0.046, 0.089] |

Two things matter here.

1. **The nominal test is wrong by roughly eightfold**, and Wilson intervals
   exclude 0.05 by an enormous margin at every length.
2. **It gets worse with more data**, 0.368 → 0.444. Spurious regression on
   integrated series does not wash out asymptotically. Anyone who assumes "more
   data will fix it" is assuming the wrong thing.

Calibrated size sits at 0.050 to 0.064, every interval covering 0.05.

Power (`m3_power_summary.csv`) is reported for the calibrated test, since that
is the one with valid size. Quoting nominal power would be quoting the
sensitivity of a test that fires on noise 42% of the time.

---

## S6. The early-warning estimator failure

`m5_ews_summary.csv`. Data simulated from a model that **genuinely contains a
fold**, so the correct answer is known by construction.

- Closed-form theory recovers **+0.565** against a predicted +0.50. Theory and
  implementation agree.
- Rolling-window `−log AC1` returns **negative** slopes where +0.5 is predicted.
- Rolling variance returns **positive** slopes where −0.5 is predicted.
- Holds across windows 20 to 240 samples, with and without detrending, at series
  lengths 1,500 / 6,000 / 20,000.

**Mechanism.** Critical slowing down means the relaxation time diverges at the
fold. A fixed-width window therefore saturates precisely where the effect is
strongest: windowed AC1 → 1, so −log AC1 → 0, exactly in the regime the
indicator exists to measure. Detrending then strips the low-frequency power
carrying what is left, which is why detrended variants are *worse*, not better.

This is structural. More data does not fix it. Raising n by an order of
magnitude does not recover the sign.

**Why this matters beyond this paper.** Rolling AC1 and variance are the
standard early-warning indicators, applied across ecology and psychopathology.
This does not show published findings are wrong. It shows that this class of
estimator, on a system with a real fold, can report a trend opposite in sign to
the truth, so a directional result from it is weak evidence in either direction.

**Recommendation:** fit the dynamical model and test its parameters, rather than
measuring indicators derived from an assumed local equilibrium. A model-based
test can be validated on ground truth before you believe it. A rolling-window
indicator usually is not.

---

## S7. Empirical results

147 recordings, 40 people, configuration B (tonic EDA).

**Primary test** (calibrated, cubic term):

| Corpus | units | rejection rate |
|---|---|---|
| WESAD | 15 | 0.000 |
| Exam stress | 30 | 0.000 |
| Nurse stress | 102 | 0.039 |
| **Pooled** | **147** | **0.027** |

Nominal target 0.05. Clustered one-vote-per-person: **0.015**, Wilson
[0.000, 0.031]. 10% of people show ≥1 significant session, which is what chance
produces across several sessions each.

**Structure that IS present** (this is why the null is specific, not vacuous):

| Statistic | rejection vs surrogates |
|---|---|
| likelihood ratio vs monostable | 0.408 |
| marginal bimodality | 0.497 |
| **cubic term (the mechanism)** | **0.027** |

The same recordings look decisively non-random-walk by two measures and exactly
like chance by the one that tests the mechanism. A study reporting only the
bimodality would have concluded the opposite of the correct answer.

**Model comparison** (held-out one-step log-density, 108 units): the full model
does not beat its own nested monostable (OU) special case. Wins on 33.8% of
units, median −0.25 nats, Wilcoxon p = 8×10⁻⁵ favouring the simpler model. Since
OU is this model with the cubic term switched off, that is the cleanest
statement that the cubic term does no work.

**Prospective prediction:** AUC 0.50 / 0.49 / 0.46 at leads of 3 / 6 / 12
windows. Chance.

---

## S8. Robustness, including what failed

| Config | coordinate | AC1 | RW | IAAFT | role |
|---|---|---|---|---|---|
| B | tonic EDA | 0.98 | 0.046 | 0.069 | primary |
| C | skin temperature | 1.00 | 0.149 | 0.161 | robustness |
| A | cardiac index | 0.31 | 0.115 | 0.138 | negative control |

Configurations A and C are elevated. **Three explanations were tested and all
three were refuted:**

1. *Inadequate null (trend not in surrogates).* IAAFT preserves spectrum and
   marginal, so circadian trend survives into the null. C went 0.149 → 0.161.
   Refuted.
2. *Clipping at ±4 induces a false cubic.* B clips most (5.1%) and is nominal;
   C clips least (0.8%) and is elevated. Runs backwards. Refuted.
3. *Test mis-sized off the unit root.* Direct size study on AR(1), φ from 0 to
   1: size ≤ 0.075 everywhere. Refuted.

What remains: A and C carry nonlinear structure no surrogate reproduces. But
**A is the negative control**, a coordinate independently shown to be
beat-detection-noise dominated (AC1 = 0.31), so nonlinearity there means
artefact, from motion, contact loss and peak-detection failure. A test firing on
the negative control is telling you "significant ≠ cusp" in that configuration.
That is what a negative control is for, and it is why the conclusion rests on B.

**Timescale:** calibrated rejection 0.062 (30s, n=48), 0.054 (60s, n=37), 0.133
(120s, n=15, i.e. 2 of 15, within binomial noise). Null is not a windowing
artefact.

---

## S9. Fate of the five predictions

| | Prediction | Status | Why |
|---|---|---|---|
| P1 | hysteresis width ∝ a^{3/2} | **not evaluable** | both axes are ratios over λ̂; a shared divisor forces slope ≈ 1 |
| P2 | EWS exponents ∓1/2 | **not evaluable** | the estimator returns the wrong sign on ground truth (S6) |
| P3 | dwell over-dispersion | **not evaluable** | requires identified geometry |
| P4 | re-entry hazard ∝ ε | **not evaluable** | ε has r = 0.07 at n=200 |
| P5 | recovery scales with α_A | **not evaluable** | α_A never identified, r = 0.16 even at n=1000 |
| ★ | restoring cubic term exists | **testable → NULL** | λ is identified (r = 0.91) |

Exactly one of five is evaluable, and it returns a null. Stating this
structure, rather than reporting four numbers that would look like tests, is the
single most important honesty decision in the paper.

On P1 specifically: with better sampling the regression *tightened* to exponent
1.07, CI [0.86, 1.29], R² = 0.58, apparently rejecting 3/2. We do **not** report
that as a refutation. Both axes carry a 1/λ̂ factor, which forces a log-log slope
near 1 by construction; partialling log(1/λ̂) out moves it only 1.13 → 1.09. A
ratio of two near-zero quantities is not a measurement.

---

## S10. Threats to validity

- **Population.** No autistic participants. The motivating claim is untested,
  not refuted. No public wearable dataset of autistic adults exists at this
  density (checked: Scheeren 2025 OSF holds preregistration only; openESM has no
  autism-specific dense series; QU wearable is children).
- **Proxy.** Tonic EDA is peripheral, one-dimensional, and sensitive to
  temperature, hydration, electrode drift and movement.
- **Effect size.** Weak cusp dynamics (calibrated power 0.24 at n=200) remain
  compatible with the data.
- **Clustering.** 102 of 147 units come from 15 nurses. Per-corpus and clustered
  figures reported alongside pooled.
- **Scope of the estimator critique.** Fixed-width rolling AC1 and variance,
  with and without Gaussian detrending. Not adaptive-bandwidth or spectral
  estimators, which we did not test.
- **Dimensionality.** A 1-D load coordinate is a strong simplification. The cusp
  is the minimal geometry producing the target phenomena, not a claim that the
  true system is one-dimensional.

---

## S11. What would change the conclusion

In descending order of leverage:

1. **Autistic-adult data.** The only thing that lifts the ceiling. Contact
   a.m.scheeren@vu.nl regarding the 87-participant EMA dataset.
2. **Longer records.** n ≥ 500 windows per unit (≈4 h continuous wear at 30 s)
   moves the control parameters into the identifiable regime. Below that, no
   cusp analysis of this kind can succeed, ours or anyone's.
3. **A slower timescale.** Overload may resolve over hours or days rather than
   seconds. Daily EMA, not wristband seconds, may be the right sampling rate.
4. **A reparameterisation** estimating `a` and `b` directly rather than as
   ratios over `θ₁`, which would remove the failure mode in S4 entirely.

Item 4 is the most tractable purely methodological improvement and is the
obvious next paper.
