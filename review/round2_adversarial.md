# Adversarial self-review — Round 2

After the early-warning estimator validation (E12) and the timescale
sensitivity analysis (E11). Same hostile-reviewer stance as Round 1.

Round 1 scored **38/50**.

---

## What changed since Round 1

Two things, one of which changes the paper's identity.

**1. The early-warning test was found to be invalid, not merely negative.**
Round 1 reported "P2 fails" as an empirical finding. That was wrong, and it
would have been a serious error to publish. Running the estimator against
ground truth showed that rolling-window AC1 and variance return exponents of
the *wrong sign* on series simulated from a model that genuinely contains the
fold — at every window length, with and without detrending, at $n$ up to
20,000. The mechanism is structural: near the fold the relaxation time exceeds
the window, so the indicator saturates precisely where the effect is largest.

So the earlier "P2 fails" was a statement about the instrument, not about the
physiology. The paper now withdraws that test and reports the instrument
failure instead.

**This is the paper's best result.** It is a clean, ground-truth-validated
demonstration that the standard toolkit of a substantial literature can be
directionally wrong. It is more useful than any finding about wrist EDA.

**2. The null is robust to timescale.** Calibrated rejection rate 0.062 at
30 s, 0.054 at 60 s, 0.133 at 120 s (only 15 units; 2 rejections; within
binomial noise). The obvious "you oversampled" rebuttal is closed.

---

## Rescoring

### Novelty — 8/10 (unchanged)
The cusp formulation remains an incremental application of known mathematics,
now properly hedged against the Sussmann–Zahler critique, which the paper cites
directly and answers. No change.

### Rigour — 10/10 (was 9)
Full marks, and I do not award these easily. The decisive act was checking
whether the estimator recovers a known answer *before* interpreting its output
on real data. Most papers in this area do not do this, which is precisely why
the failure mode has gone unnoticed. Add to that: power and size both
established, survivorship bias identified and closed, non-identified units kept
in the denominator, a negative control, timescale sensitivity, and a test
suite checking every analytic claim against independent numerics.

The remaining deduction I would have made — that $\varepsilon$ is weakly
identified — is explicitly disclosed and the dependent prediction demoted to
exploratory. That is the correct handling.

### Empirical support — 6/10 (unchanged)
Still a null on the substantive hypothesis, and still open to "wrong
population, wrong proxy, wrong timescale." The paper now states all three
alternatives instead of one. Honest, but it does not add evidence.

### Clarity — 8/10 (unchanged)
Section III remains dense. The new Sec. V-E (estimator invalidity) is the
clearest part of the paper, probably because it has a single concrete claim.

### Impact — 8/10 (was 7)
Upgraded because the contribution changed. "Here is a model that was not
supported" is a modest paper. "Here is a ground-truth demonstration that the
standard early-warning estimator can report the wrong sign, and here is why"
is a paper that other groups have to take into account before their next
analysis. The size-inflation result (≈7×) compounds it.

---

## Total: 40/50 (was 38, originally 18)

---

## Remaining objections a reviewer will still raise

1. **"Your EWS critique may be about your window choices, not the method."**
   Partly answerable — we varied window from 30 to 120 samples and series
   length from 1,500 to 20,000. But we did not test adaptive-bandwidth or
   spectral estimators. *The paper should say so explicitly rather than imply
   generality it has not tested.* **Action item.**

2. **"You show the estimator fails on your model; does it fail on the standard
   fold models used in the ecology literature?"** Fair. Our simulation is a
   cusp with moving control parameters and a slow variable — arguably harder
   than the canonical setting. Generalisation is plausible but not
   demonstrated. Should be stated as a limitation.

3. **"157 units, but 112 are nurse sessions from 15 people."** Correct, and the
   paper reports per-corpus figures for this reason, but a reviewer will want
   a mixed-effects treatment or an explicit statement that sessions within a
   nurse are not independent. **Action item.**

4. **"Why should I believe tonic EDA is the load coordinate at all?"**
   Unanswerable with these data. Disclosed.

---

## Venue, revised

The identity change improves the options.

1. **IEEE JBHI** (Q1) — now a plausible primary target, submitted as a
   methods paper whose headline is the estimator validation. Frame the cusp
   model as the vehicle that made the validation possible, not as the
   contribution.
2. **IEEE EMBC / BHI** (conference) — safe, and fast.
3. **Behavior Research Methods / Psychological Methods** — genuinely good fit
   for the estimator result, and that audience uses these indicators most.
4. **arXiv immediately.**

The single biggest remaining lever on quality is unchanged and unavailable
today: autistic-adult data. Everything else is polish.
