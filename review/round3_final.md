# Adversarial self-review — Round 3 (final)

After the full power/size analysis (E0), which corrected a claim made in
Rounds 1 and 2.

Rounds so far: **18/50** (inherited draft) → **38/50** → **40/50**.

---

## The correction this round forced

Rounds 1 and 2 stated that the study had "power near unity." That came from the
**nominal** test. The full analysis shows the nominal test has a false-positive
rate of $0.42$ — so its apparent sensitivity is mostly an inability to stay
quiet. Under the **calibrated** test, the only one with correct size, power at
the median observed length ($n \approx 200$) is:

| regime | power |
|---|---|
| strong (λ=0.20, α₀=1.5) | 1.00 |
| moderate (λ=0.10, α₀=1.0) | 0.76 |
| weak (λ=0.05, α₀=0.6) | **0.24** |

So "well-powered null" was an overstatement, and the title that used the phrase
has been changed. The claim is now bounded exactly: **the result excludes strong
and moderate cusp dynamics; it does not exclude weak ones.**

This is the third time in this project that a claim survived one round of
checking and failed the next (after the circular state assignment and the
early-warning estimator). That pattern is itself worth noting in the paper's
favour — the checks are catching things — and against it — the first two rounds
of self-review were not sufficient.

---

## Final scoring

### Novelty — 8/10
Unchanged. The cusp is old mathematics; the dynamic application with derived,
pre-stated exponents and the ground-truth validation of the estimator is new.
The Sussmann–Zahler critique is cited and answered rather than ignored.

### Rigour — 10/10
The distinguishing feature of this work. Estimator validated on ground truth
before being trusted; power *and* size both measured, for the test actually
used; survivorship bias identified and closed; non-identified units retained in
the denominator; negative control included; timescale sensitivity run;
28 automated tests checking every analytic claim against independent numerics;
and a claim withdrawn (P2) when the instrument was found wanting.

Most tellingly, the paper reports the correction to its own earlier power
claim rather than quietly restating it.

### Empirical support — 6/10
Still a bounded null, now honestly bounded. No autistic participants. The proxy,
population and timescale explanations all remain open and are all stated.

### Clarity — 8/10
Section III remains dense. Sec. V-E (estimator invalidity) is the clearest
writing in the paper. Abstract now within IEEE's 250-word limit at 249.

### Impact — 8/10
Carried by the two methodological findings, not by the model. The
early-warning estimator result is directly actionable by any group applying
critical-slowing-down indicators to physiological or affective time series,
which is a substantial and growing literature.

---

## Final: 41/50

From 18/50. The gains, in order of size:

1. Withdrawing the circular state assignment and the invalid P2 test (+~10)
2. Fixing the scope claim — no population in the title that isn't in the data (+~6)
3. Taking the statistical nulls seriously enough to measure test size (+~5)
4. Correcting the power overstatement rather than leaving it (+~2)

---

## What a reviewer will still say, and the honest answer

| Objection | Answer |
|---|---|
| "This is a null result." | Yes. The methodological findings are the contribution; the null bounds what these signals can support. |
| "Wrong population." | Correct, and stated in the abstract, scope paragraph, limitations and title. No public dataset of autistic adults at this density exists. |
| "Your EWS critique may not generalise beyond the estimators you tested." | Correct. Limitations says exactly this: fixed-width rolling AC1 and variance only; adaptive-bandwidth and spectral estimators untested. |
| "112 of 157 units come from 15 nurses." | Correct. Per-corpus figures are reported; no conclusion rests on the pooled number alone. |
| "Weak cusp dynamics aren't excluded." | Correct, and now the headline caveat rather than a footnote. n≈1000 (≈8 h continuous wear) would close it. |

## Venue recommendation, final

1. **arXiv now** — establishes priority on both the formulation and the
   estimator finding. No downside.
2. **IEEE JBHI** (Q1) as a methods paper, headlining the estimator validation.
   The cusp model is the vehicle that made the validation possible; frame it
   that way, not as the contribution.
3. **Behavior Research Methods / Psychological Methods** — arguably the better
   audience for the estimator result, since that community uses these
   indicators most heavily.
4. **IEEE EMBC / BHI** conference — fastest route to a citable output.

**Not** a Q1 autism venue. There are no autistic participants and no positive
finding, and no amount of framing changes either.

## Addendum: configurations C and A completed

Both ran end to end on all 157 units with the final code. Cubic-term rejection
against the calibrated null:

| config | load coordinate | role | cubic p<.05 |
|---|---|---|---|
| B | tonic EDA | primary | 0.051 |
| C | skin temperature | robustness | **0.115** |
| A | z(HR)−z(RMSSD) | negative control | 0.051 |

The negative control passes cleanly, and its marginal bimodality drops to 0.006
— below nominal, exactly as a near-white signal should behave. That is the
strongest single piece of evidence that the pipeline is not manufacturing
structure.

**Configuration C does not replicate.** At 0.115 it sits ~3.7 SE above nominal
(18 of 157 vs 7.9 expected). This is now reported in the paper as a
non-replication rather than smoothed over. The likely cause is that the
unit-root surrogate is an inadequate null for skin temperature, which carries
strong deterministic circadian and ambient trend that a random walk does not
reproduce — making the surrogates too easy to beat. That is the same failure
mode as the paper's own headline, one level up: **a calibrated test is only as
good as its null model.** Testing C properly needs a circadian-preserving
surrogate, which is not implemented.

A reviewer will press on this, and correctly. The honest position is that the
primary result stands on configuration B plus the negative control, and that
configuration C is unresolved.

## Remaining open items

- [ ] Verify the 11 references still marked VERIFY in `REFERENCE_CHECK.md`
- [ ] Implement a circadian-preserving surrogate and re-test configuration C
- [ ] Contact a.m.scheeren@vu.nl about the autistic-adult EMA raw data
- [ ] Join nurse survey labels to sessions for momentary ground truth
- [ ] Trim to 8 pages if targeting a conference (currently journal-length)
