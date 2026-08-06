# Adversarial self-review — Round 1

Written in the voice of a hostile Q1 reviewer (target: IEEE JBHI / IEEE TAFFC).
The job here is to find reasons to reject, not reasons to like it.

Scoring, 50 points: Novelty 10 · Rigour 10 · Empirical support 10 ·
Clarity 10 · Impact 10.

---

## Prior state, for comparison

The earlier draft scored **18/50**. Two fatal objections: a paper titled "in
Autistic Adults" analysing zero autistic participants, and early-warning theory
applied to a dataset where the transition is an experimenter flipping a switch.
A third, not previously identified: states were assigned from condition labels
and then "predicted," which is circular.

---

## Novelty — 8/10

The cusp formulation is, as far as the searches conducted here go, new to this
problem. Specifically new:

- Regulatory capacity as the **splitting factor** rather than an additive load
  term. That is a substantive theoretical claim, not a reparameterisation: it
  predicts threshold behaviour and memory instead of proportional degradation.
- Exact geometric definitions for **stuck** and **recovering**, which the
  qualitative literature names but no model defines.
- A transition kernel **generated** by Kramers rates from nine parameters
  rather than counted as twenty frequencies.

*Deductions.* The cusp itself is 1970s mathematics, and catastrophe theory has
an unhappy history in psychology (Zeeman's overreach; the Sussmann–Zahler
critique). Van der Maas & Molenaar and Grasman et al. already fit cusps to
behavioural data. The novelty is the dynamic, time-series application with
derived scaling laws — real, but incremental on a known framework, not a new
mathematics. A reviewer who knows this literature will say so, and should.

**The paper must cite the catastrophe-theory backlash explicitly and say why
this application avoids it** (answer: because it predicts exponents and tests
them against calibrated nulls, which is exactly what the 1970s applications did
not do). Currently it does not. *Action item.*

## Rigour — 9/10

This is the strongest part and it is genuinely strong.

- Estimator is exact, not approximate; the discretisation-bias problem is
  removed by construction rather than bounded.
- The non-identifiability that broke the first estimator was diagnosed and
  fixed structurally, not patched with tighter bounds.
- Power **and size** are both established by simulation. Most papers report
  neither.
- The $\theta_1 \ge 0$ constraint is enforced as a model property, and
  non-identified units are retained in the denominator rather than dropped —
  the survivorship bias that would have manufactured a positive result was
  found and closed.
- 28 tests check the analytic claims against independent numerics.

*Deductions.* $\varepsilon$ recovers at only $r \approx 0.51$, so P4 rests on a
weakly identified parameter. The UKF variant is implemented but not run at
scale, so the measurement-error argument is asserted rather than demonstrated.
The one-dimensional load coordinate is a strong assumption defended only by
parsimony.

## Empirical support — 6/10

Here is where the paper is vulnerable, and no amount of writing fixes it.

The result is a null. A well-powered, carefully calibrated null, which is worth
more than most weak positives — but a null. The honest reading:

- The **methodological** finding (nominal test size $\approx 0.35$ on
  near-unit-root physiological series) is solid, quantified, and genuinely
  useful to the field. This carries the paper.
- The **empirical** finding (no cusp signature in 157 recordings) is credible
  and well-controlled, but it is evidence against the author's own hypothesis
  in these data.

A reviewer will ask the obvious question: **is this a null about the model, or
about the proxy?** The paper cannot fully answer that. Wrist EDA at 30 s may
simply be too coarse and too artefact-laden to carry a latent load coordinate.
The paper must not overclaim that overload is *not* a cusp — only that these
signals show no such signature.

*The single biggest threat:* a reviewer says "you tested your theory on the
wrong population with the wrong instrument and found nothing; come back with
autistic adults and better sensing." That is a fair critique and it is
unanswerable with current open data.

## Clarity — 8/10

Structure is sound; propositions are stated before they are tested; scope is
declared early and repeatedly. The derivation is compact and followable.

*Deductions.* Section III is dense — a reader without dynamical-systems
background will struggle around the Kramers bridge. The five-state table needs
a worked example. Some sentences are doing too much work at once.

## Impact — 7/10

The size-calibration finding should change practice: early-warning and
bistability claims on wearable physiology are being made without surrogate
calibration, and this paper shows the nominal test is wrong by roughly
sevenfold. That is citable and actionable.

The framework itself has clear onward use if autistic-adult data arrives. The
pre-registered protocol makes that concrete rather than aspirational.

*Deductions.* Impact is capped by the null. Nobody builds a just-in-time
intervention on a mechanism that was not detected.

---

## Total: 38/50

Up from 18/50. The gain came from three things, in order of importance:
fixing the circularity, fixing the scope claim, and taking the statistical
nulls seriously enough to find that the standard test does not work here.

### What would move it higher

| Action | Gain | Feasible today? |
|---|---|---|
| Autistic-adult data | +6–8 | **No** — no public dataset exists |
| Cite and address the catastrophe-theory backlash | +1 | Yes |
| Run the UKF at scale to test the measurement-error explanation | +1 | Yes |
| Higher-resolution or multi-site sensing to test the proxy explanation | +2 | No |
| Join nurse survey labels to sessions for momentary ground truth | +1 | Yes |
| Worked example through the five states | +0.5 | Yes |

### Verdict on venue

Not a Q1 autism paper — there are no autistic participants and there is no
positive finding. Realistic targets, in order:

1. **IEEE EMBC / IEEE BHI** (conference) — good fit; methods contribution plus
   an honest null is publishable and useful.
2. **IEEE JBHI** (Q1 journal) — plausible as a methods paper *if* the
   size-calibration result is made the headline contribution rather than a
   supporting analysis. Reviewers will be more interested in "the standard test
   is wrong by 7x on this data class" than in the cusp model itself.
3. **arXiv preprint immediately**, to establish priority on the formulation.

The honest framing is also the strategically better one: a paper that says
"here is a derivation, here is why the usual inference fails, here is a
well-powered null" is a paper a reviewer can accept. A paper that claimed a
positive cusp finding from this data would be caught.
