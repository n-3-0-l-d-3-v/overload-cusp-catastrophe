# Supplementary material

Everything the six-page conference paper compresses. This is the working document
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

`m1_recovery_summary.csv`, 2000 replicates per cell, 12,000 synthetic series.

Two correlations, because they answer different questions and the gap between
them is the result. **Spearman ρ** asks whether the ordering is recovered.
**Pearson r** asks whether the value is.

**Spearman ρ — is the ordering recovered?**

| Parameter | n=100 | n=150 | n=200 | n=300 | n=500 | n=1000 |
|---|---|---|---|---|---|---|
| λ relaxation | 0.833 | 0.909 | **0.936** | 0.960 | 0.978 | 0.975 |
| σ diffusion | 0.969 | 0.978 | **0.985** | 0.990 | 0.994 | 0.997 |
| β_S sensory | 0.462 | 0.584 | 0.643 | 0.762 | 0.829 | 0.906 |
| β_T switch | 0.389 | 0.485 | 0.575 | 0.671 | 0.799 | 0.877 |
| β_U uncertainty | 0.342 | 0.435 | 0.526 | 0.621 | 0.692 | 0.831 |
| β₀ intercept | 0.516 | 0.549 | 0.595 | 0.697 | 0.776 | 0.863 |
| α₀ splitting | 0.327 | 0.446 | 0.569 | 0.683 | 0.780 | 0.879 |
| α_A debt gain | 0.189 | 0.246 | 0.316 | 0.389 | 0.534 | 0.720 |
| ε slow rate | 0.047 | 0.080 | 0.103 | 0.209 | 0.316 | 0.439 |

**Pearson r — is the value recovered?**

| Parameter | n=100 | n=150 | n=200 | n=300 | n=500 | n=1000 |
|---|---|---|---|---|---|---|
| λ relaxation | 0.820 | 0.902 | **0.930** | 0.957 | 0.977 | 0.970 |
| σ diffusion | 0.954 | 0.977 | **0.973** | 0.982 | 0.990 | 0.993 |
| β_S sensory | 0.155 | 0.229 | 0.264 | 0.669 | 0.794 | 0.755 |
| β_T switch | 0.213 | 0.186 | 0.342 | 0.482 | 0.718 | 0.831 |
| β_U uncertainty | 0.186 | 0.151 | 0.287 | 0.512 | 0.631 | 0.699 |
| β₀ intercept | 0.225 | 0.097 | 0.175 | 0.498 | 0.578 | 0.240 |
| α₀ splitting | 0.072 | 0.051 | 0.145 | 0.504 | 0.638 | **0.102** |
| α_A debt gain | 0.027 | 0.004 | 0.026 | 0.013 | 0.054 | 0.184 |
| ε slow rate | 0.023 | 0.022 | 0.041 | 0.129 | 0.201 | 0.251 |

**Read these tables before believing any cusp result on wearable data.**

At n=200, the median in these corpora, only λ and σ score well on both. The
splitting factor — the entire scientific content of the model — has ρ = 0.57 and
r = 0.15. You could rank people by it, badly. You could not report a number.

### Why the two disagree

`a = θ₂/θ₁`, and nothing bounds `θ₁` away from zero. Dividing by a small number
**preserves order and destroys scale**, which is exactly the pattern above.

The tail of the recovered splitting factor makes it concrete:

| n | 99th pct \|α̂₀\| | max \|α̂₀\| |
|---|---|---|
| 100 | 12.15 | 76.8 |
| 200 | 4.25 | 68.5 |
| 500 | 2.39 | 7.5 |
| 1000 | 2.10 | **139.2** |

At n=1000 the 99th percentile is 2.1 and the maximum is 139. One replicate in
two thousand is enough to drag Pearson from 0.88 to 0.10. This is not an
outlier to be trimmed away — it is the estimator doing what the model says it
must, and trimming it would hide the finding.

**The practical consequence is narrower than "collect more data".** Length buys
a defensible *ranking* of participants by α₀: ρ climbs 0.33 → 0.88 from n=100 to
n=1000. Length never buys a reportable *value*: r is 0.15 at n=200 and 0.10 at
n=1000. A study that needs the value needs a parameterisation estimating `a` and
`b` directly, not a longer recording.

### The real fits sit outside the simulated range

The median `λ̂` is **0.0059** and the median recovered `α̂₀` is **12**, which would
put attractors at roughly ±2 on a unit-variance coordinate. Those are not weakly
bistable people. They are people with no restoring cubic term, divided by a
number close to zero.

That `λ̂` is *below the entire simulated range*, so the recordings sit further
into non-identifiability than any of the 12,000 synthetic series used to map it.

**ε is never identified** even in rank (ρ = 0.44 at n=1000), and **α_A only
reaches ρ = 0.72 there while r stays at 0.18**. Any claim resting on the
recovery-debt mechanism is unsupported at any length we tested, and more data
alone will not rescue it.

---

## S5. Test size and power

`m2_size_summary.csv`: 30,000 random-walk replicates (nominal), 7,500
(calibrated).

| n | nominal size | 95% CI | calibrated size | 95% CI |
|---|---|---|---|---|
| 100 | 0.363 | [0.350, 0.377] | 0.050 | [0.040, 0.064] |
| 150 | 0.404 | [0.391, 0.418] | 0.054 | [0.042, 0.068] |
| 200 | 0.426 | [0.412, 0.440] | 0.050 | [0.040, 0.064] |
| 300 | 0.438 | [0.425, 0.452] | 0.042 | [0.032, 0.054] |
| 500 | 0.440 | [0.427, 0.454] | 0.047 | [0.037, 0.060] |
| 1000 | 0.444 | [0.430, 0.458] | 0.057 | [0.045, 0.071] |

Two things matter here.

1. **The nominal test is wrong by roughly eightfold**, and Wilson intervals
   exclude 0.05 by an enormous margin at every length.
2. **It gets worse with more data**, 0.363 → 0.444. Spurious regression on
   integrated series does not wash out asymptotically. Anyone who assumes "more
   data will fix it" is assuming the wrong thing.

Calibrated size sits at 0.042 to 0.057, every interval covering 0.05.

Power (`m3_power_summary.csv`) is reported for the calibrated test, since that
is the one with valid size. Quoting nominal power would be quoting the
sensitivity of a test that fires on noise 42% of the time.

---

## S6. The early-warning estimator failure

`m5_ews_summary.csv`. Data simulated from a model that **genuinely contains a
fold**, so the correct answer is known by construction. Ninety configurations
— five window lengths × two detrending choices × three series lengths — at 500
replicates each, 15,000 series in total.

Closed-form theory recovers **+0.565** against a predicted +0.50. Theory and
implementation agree.

The rolling estimators fail in **two distinct regimes**, and it matters which
one you are in.

**Regime 1, windows 20–120: the sign is inverted, and not marginally.**

| Estimator | Window | Predicted | Median | Replicates with wrong sign |
|---|---|---|---|---|
| −log AC1 | 30 | +0.5 | **−0.216** | 95% |
| −log AC1 | 120 | +0.5 | −0.043 | 66% |
| variance | 30 | −0.5 | **+0.307** | 99% |
| variance | 120 | −0.5 | +0.028 | 68% |

Several configurations invert in **all 500** replicates.

**Regime 2, window 240: the estimate collapses onto zero.**

| Estimator | Window | Predicted | Median | Replicates with wrong sign |
|---|---|---|---|---|
| −log AC1 | 240 | +0.5 | +0.026 | 32% |
| variance | 240 | −0.5 | −0.014 | 40% |

Here the median finally carries the *right* sign — at a magnitude of roughly
5% of the predicted one, with the sign close to a coin flip. It is right by
accident, not by measurement.

An earlier draft of this work claimed the sign was wrong "in every
configuration tested". At 500 replicates that is false: 16 of the 60 rolling
configurations carry the correct sign, all of them at window 240. The corrected
claim is stronger, not weaker. **Nowhere on the grid does an estimate come near
±0.5.** Widening the window does not rescue the estimator; it trades a
confident wrong answer for no answer at all.

**Mechanism.** Critical slowing down means the relaxation time diverges at the
fold. A fixed-width window therefore saturates precisely where the effect is
strongest: windowed AC1 → 1, so −log AC1 → 0, exactly in the regime the
indicator exists to measure. Detrending then strips the low-frequency power
carrying what is left, which is why detrended variants are *worse*, not better.

This is structural. More data does not fix it: raising n by an order of
magnitude leaves the sign where it was, and widening the window only drives the
estimate towards zero.

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
