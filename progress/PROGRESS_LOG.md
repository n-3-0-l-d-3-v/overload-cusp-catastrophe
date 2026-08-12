# Progress log

A working record of what was done, in order, including the things that broke
and what the failures changed. Kept deliberately unflattering: the decision
points matter more than the outputs, and a reviewer or examiner asking "how did
you arrive at this?" should be able to read this file and get a real answer.

Session date: 2026-07-22.

---

## 0. Starting position

Inherited from earlier work (`research/` parent folder):

- A draft with title, abstract, Introduction, Related Work and 30 references.
- `09. wesad_pipeline.py` — a WESAD analysis script running in demo mode on
  synthetic data.
- `10. evaluation report.txt` — a prior critique scoring the draft **18/50**.

The 18/50 critique raised two objections that turned out to be correct and that
drove most of what follows:

1. The paper was titled "…in Autistic Adults" and contained **zero autistic
   participants**. WESAD is healthy adults in a lab.
2. Early-warning-signal theory needs a system fluctuating freely near a
   self-organised tipping point. In WESAD an experimenter switches the stress
   condition on at a scheduled time. Testing critical slowing down there is a
   methodological mismatch, not a minor limitation.

A third problem was found during this session and was not in the original
critique: **the state assignment was circular.** The old pipeline mapped WESAD
condition labels directly to states (`{1:calm, 2:overloaded, ...}`) and then
estimated a transition matrix. That matrix can only re-describe the block
design of the protocol. Nothing was being discovered.

---

## 1. Datasets — resolving the "Kaggle isn't credible" concern

The concern was half right, and the precise half matters.

- **WESAD itself is fine.** Peer-reviewed at ACM ICMI 2018, in the UCI ML
  Repository (ID 465), hundreds of downstream papers.
- **Citing a Kaggle re-upload is not fine.** No version guarantee, no licence
  guarantee, no checksum, deletable by its uploader.

Action: everything re-downloaded from primary repositories, programmatically,
with URLs and byte counts recorded (`code/experiments/fetch_data.py`).

Two further corpora were added, not for volume but because each answers a
specific objection:

| Corpus | Answers |
|---|---|
| Wearable Exam Stress (PhysioNet, `10.13026/kvkb-aj90`) | naturalistic, self-paced load — the condition EWS theory actually assumes |
| Nurse Stress (Dryad `10.5061/dryad.5hqbzkh6f`, 1250 h) | fully in the wild; also gives large per-unit *n* |

Downloads: WESAD 2 249 444 501 B; exam 85 968 624 B; nurse 1 156 939 542 B.
All HTTP 200, all size-verified.

**Obstacle:** the documented Dryad API returned HTTP 401 without a bearer
token, and 403 to scripted clients on the file-stream endpoint. Resolved by
using the authors' own Zenodo deposit (record 5514277) — same files, same
authors, scriptable. Both DOIs cited.

**Searched for and did not find:** any open wearable dataset of autistic
*adults* at the required density. Checked Scheeren 2025 (osf.io/98jup — holds
preregistration materials, not raw data), openESM, QU autism wearable
(children, not adults), ABIDE (imaging, not dense time series). Systematic
reviews confirm the gap. This absence became a stated finding rather than
something to paper over.

---

## 2. The mathematical formulation — what changed and why

The old formulation was $L_t=\alpha S_t+\beta E_t+\gamma U_t+\delta T_t$ with a
threshold, plus a counted Markov matrix. Two fatal weaknesses: a weighted sum
with a threshold predicts nothing that could be wrong, and a 5×5 counted matrix
accommodates any data whatsoever.

Replaced with a **cusp catastrophe** formulation. The key move: regulatory
capacity is not an additive load term, it is the **splitting factor** — it
changes the geometry rather than the level. Hysteresis, critical slowing down,
abrupt onset and the five states then all *follow* instead of being assumed.

What this buys, concretely — three things the old model could not do:

1. **Hysteresis width $=\frac{4}{3\sqrt3}a^{3/2}$.** Not "recovery is delayed"
   but an exponent of exactly 3/2 that data can contradict.
2. **EWS exponents $-1/2$ (variance) and $+1/2$ ($-\log$AC1).** Point
   hypotheses, not the directional claim ("it goes up") that the sceptical
   literature shows arises spuriously on any autocorrelated series.
3. **`stuck` and `recovering` get exact definitions.** `stuck` = lower basin
   while an overloaded attractor coexists. `recovering` = still in the upper
   basin though demand has already fallen below the level that would put you
   there — held up purely by hysteresis. These were previously vocabulary; now
   they are geometry.

---

## 3. Implementation, and the four bugs worth recording

**Bug 1 — degenerate cusp point.** `equilibria(0,0)` returned three roots
(a triple root at the origin) and was read downstream as bistable. Fixed by
collapsing repeated roots. *Caught by:* `test_monostable_below_the_cusp`.

**Bug 2 — Euler instability.** Explicit Euler on a cubic drift diverges for
$\lambda\,\dd t\gtrsim0.35$; simulation overflowed. Fixed by adding an explicit
rate parameter $\lambda$ and, more importantly, by **declaring the discrete-time
map to be the model** rather than an approximation to the SDE. That removes
discretisation bias entirely and makes the likelihood exact — which is what
makes the parameter-recovery test meaningful in the first place.

**Bug 3 — off-by-one in an IIR filter.** The slow variable was rewritten from a
Python loop to `lfilter` for speed; the filter coefficients `b=[0,c]` already
apply the one-step lag, so pre-shifting the input double-lagged it. Max
absolute error 0.081 against the reference loop. Fixed; now agrees to
$10^{-15}$. *Caught by:* an explicit equivalence check written before trusting
the optimisation.

**Bug 4 — non-identifiability, found in the pilot run.** The first real fit
returned `alpha0` pinned at its upper bound, `lam` at its lower bound and `eps`
at its upper bound simultaneously. Diagnosis: only the *products* $\lambda a$
and $\lambda b$ enter the drift, so a bounded joint search over nine parameters
is searching a ridge.

Fix, and it is the single best change in the codebase: conditional on the slow
variable, the drift is **linear in a reparameterised coefficient vector**, so
fitting is ordinary least squares profiled over one scalar. No bounds, no
starting values, no local optima, exact.

Result: parameter recovery correlations $r>0.95$ on 8 of 9 parameters, biases
$<0.02$; test suite 27 s → 4.3 s.

---

## 4. The sensor-assignment decision (a result that changed the design)

A model that reads the latent load *and* its drivers off the same signal is
unfalsifiable — shared measurement noise alone would produce coupling. So load
and drivers were put on disjoint sensors. The first attempt used a cardiac load
index, $z(\mathrm{HR})-z(\mathrm{RMSSD})$.

Measured lag-1 autocorrelation of the candidate load coordinates on WESAD:

| window | tonic EDA | cardiac index |
|---|---|---|
| 10 s | 0.998 | 0.142 |
| 30 s | 0.985 | 0.188 |
| 60 s | 0.958 | 0.234 |

The cardiac index is essentially white noise: RMSSD over ~10–30 beats is
dominated by beat-detection error. A relaxation process must have a slow
coordinate, so:

- **config B (tonic EDA) became primary** — not a preference, a measurement.
- **config C (skin temperature)** is the genuine robustness check.
- **config A (cardiac) was kept as a negative control.** A pipeline that
  reported bistability there would be reporting it for anything. This is now
  one of the more informative results in the paper, because it could have
  invalidated the method at no benefit to us.

Window fixed at 30 s: the best available trade between a slow enough coordinate
and enough samples per unit (607 → 202 → 101 windows at 10/30/60 s).

---

## 5. The confound that reshaped the inference (most important item here)

First real fit with config B looked like a strong positive: likelihood ratios
of 21–101 against the monostable restriction, $p=0.032$, all five states
populated, marginal distribution clearly bimodal (GMM BIC favouring two
components by 185–382).

Then the obvious question: **is tonic EDA just a random walk?** ADF $p>0.05$ on
every subject checked. And a random walk over a finite window spends time in
two places — it looks bimodal, and a flat-bottomed bistable potential fits it
better than a single well, with no bistability present at all.

Tested it directly against matched unit-root surrogates:

| Subject | statistic | observed | RW null median | RW null p95 | p |
|---|---|---|---|---|---|
| S2 | GMM BIC diff | 185 | 20 | 136 | 0.020 |
| S2 | LR | 21.1 | 1.6 | 10.7 | 0.049 |
| S3 | GMM BIC diff | 382 | 24 | 109 | 0.005 |
| S3 | LR | 101.3 | 6.4 | 44.4 | 0.024 |

The observed values do exceed the null — but the null is *large*, and the
nested LRT alone would have massively overstated the evidence.

**Consequence:** the random-walk surrogate, not the nested monostable
restriction, became the paper's **primary null**. This is the kind of thing
that, left unchecked, produces a confident and wrong paper.

---

## 5b. The finding that changed the paper's identity

Running the end-to-end demo on **simulated data with known ground truth** — a
system that genuinely contains a cusp — produced this:

```
5. Early-warning exponent: +0.052 [+0.021, +0.088], predicted -0.500
```

The early-warning test returned the wrong answer on data where the right answer
was known by construction. That is not a negative result about physiology; it
is a broken instrument.

Investigated properly (`experiments/ews_validation.py`, E12):

| estimator | window | detrend | predicted | median | sign |
|---|---|---|---|---|---|
| theory: λ(μ) | — | — | +0.50 | **+0.565** | ✓ |
| rolling −logAC1 | 30 | no | +0.50 | −0.262 | ✗ |
| rolling −logAC1 | 30 | yes | +0.50 | −0.030 | ✗ |
| rolling −logAC1 | 60 | no | +0.50 | −0.185 | ✗ |
| rolling −logAC1 | 120 | no | +0.50 | −0.035 | ✗ |
| rolling variance | 30 | no | −0.50 | +0.311 | ✗ |
| rolling variance | 120 | yes | −0.50 | +0.036 | ✗ |

**12 of 12 rolling-window configurations returned the wrong sign**, at series
lengths from 1,500 to 20,000. The theory reproduces its own exponent exactly.

Why: critical slowing down means the relaxation time diverges at the fold, so a
fixed-width window autocorrelation saturates towards 1 — and −log AC1 towards 0
— exactly where the effect is largest. The estimator is censored precisely in
the regime it exists to measure. Detrending then removes the low-frequency
power carrying what remains, which is why detrended variants are *worse*.

**Consequences.** The earlier "P2 fails on real data" claim was withdrawn as
uninterpretable — it was a statement about the instrument, not the physiology.
And the paper gained its strongest result: a ground-truth demonstration that
the standard early-warning toolkit, used across the psychopathology literature,
can report a trend opposite in sign to the truth.

This is the clearest argument in the whole project for validating an estimator
on known ground truth before believing its output on real data. Had the demo
not been written, the paper would have shipped a confident and wrong claim.

## 6. Experimental protocol

Ten experiments, one entry point, everything seeded:

E1 parameter recovery · E2 per-unit fits · E3 bistability against both nulls ·
E4 held-out comparison against 5 baselines · E5 hysteresis / P1 ·
E6 EWS exponents / P2 · E7 dwell-time over-dispersion / P3 ·
E8 re-entry hazard / P4 · E9 external validation against protocol labels ·
E10 prospective onset AUC.

Run across 3 sensor configurations × 3 corpora; 157 units fitted in config B
(15 WESAD + 30 exam + 112 nurse).

---

## 7. Verification

- 28 automated tests, all passing.
- Every analytic claim in the model section is checked against an independent
  numerical computation — the 3/2 law, the $\pm1/2$ exponents, the vanishing
  relaxation rate at the fold, monotone Kramers rates, saddle ordering.
- Parameter recovery from simulated data with known ground truth.
- Estimator is deterministic; no seed-dependence in the fits.

---

## 7b. Deliverables produced

| Artefact | Location |
|---|---|
| IEEE manuscript (LaTeX) | `paper/main.tex` — 45 references, all resolving |
| Overleaf-ready bundle | `paper/overleaf_bundle.zip` — compiles on upload |
| Word version | `paper/paper.docx` — readable equivalent, not IEEE layout |
| Figures | `figures/` — 8 paper figures + demo, PDF + PNG at 600 dpi |
| Results | `results/` — every CSV/JSON the paper cites |
| Model package | `code/chm/` — 8 modules |
| Test suite | `code/tests/` — 28 tests, all passing |
| Experiments | `code/experiments/` — one entry point per experiment |
| Reviews | `review/` — three adversarial rounds, scored |

Automated pre-submission checks (`build_paper.py`) pass clean: abstract 249
words (IEEE limit 250), every `\ref` resolves, every figure present, no
placeholders left.

## 7c. Configurations C and A (completed after the main write-up)

| config | load coordinate | role | cubic p<.05 |
|---|---|---|---|
| B | tonic EDA | primary | 0.051 |
| C | skin temperature | robustness | **0.115** |
| A | z(HR) − z(RMSSD) | negative control | 0.051 |

The negative control passed: chance rejection on the cubic term, and marginal
bimodality of 0.006 — *below* nominal, which is what a near-white signal should
give. Good evidence the pipeline isn't manufacturing structure.

Configuration C did **not** replicate (0.115, about 3.7 SE above nominal). The
paper reports it as a non-replication. Most likely cause: skin temperature has
strong deterministic circadian and ambient trend, which a random-walk surrogate
does not reproduce, so the surrogates are too easy to beat. That is the paper's
own headline problem one level up — a calibrated test is only as good as its
null model. A circadian-preserving surrogate is needed and was not built.

## 7d. Evaluation round: six more defects, all found late

Asked for a fresh critical read and fixes, not another summary. What that
turned up is a useful record of how much survives three rounds of review.

**Six of nine spot-checked references were wrong.** Verified against the
Crossref API rather than by eye:

| Cited as | Actually |
|---|---|
| Millidge et al. | **Arthur, Vine, Buckingham, Brosnan, Wilson & Harris** |
| Bos et al. 2021, *J. Affect. Disord.* | **A different paper entirely** — Squarcina et al. on deep learning for treatment response |
| Turan Birol & Singh | **Li, Henning & Camerer** |
| Can et al., *IEEE RBME* | **Cano et al., *Sensors*** |
| Kirtley et al. (openESM) | **Siepe, Haslbeck, Kloft & Büchner** |
| Kiep 2025 / Augé "Pauline" 2025 | 2023 / **Pierre** 2024 |

This was the single worst thing in the project. A carried-over citation list
from notes is not a bibliography, and one entry pointed at a completely
unrelated paper. All corrected; `REFERENCE_CHECK.md` now carries the table.

**A baseline had been reporting nothing.** `LogisticRegression(multi_class=…)`
— an argument scikit-learn removed in 1.7 — raised `TypeError`, which a bare
`except: pass` swallowed. The comparison table showed an empty row for a
baseline that had never run. Every silent except in that function now logs, and
per-model fold counts are recorded.

**The model comparison conditioned on the outcome.** It ran on 37 of 157
units — only those where the geometry was identified — though CHM/OU/HMM/GBM
need only the series. That is the same survivorship bias closed in
`e2_fit_all`, reintroduced one function later. Now 108 units.

**The nurse corpus was sampled from 5 of 15 people.** Sessions are named
`<nurseID>_<timestamp>`, so sorting by path returns all of one nurse's sessions
before any of the next; a 150-session cap drew from 5 nurses while the paper
said "15 nurses, 1250 h". `nurse_subjects()` now interleaves round-robin by
nurse: caps of 60/150/300 all span 15. **Everything was re-run.** New totals:
147 units from 40 people, and the headline rejection rate fell from 5.1% to
2.7%.

**P1 turned out to be confounded, not merely underpowered.** With the better
sampling the hysteresis regression became tight — exponent 1.07, CI
[0.86, 1.29], R² = 0.58 — and appeared to *reject* the 3/2 law. It does not.
Both axes are recovered as θ_k/θ₁, so both inflate as λ̂ → 0, and a shared
divisor produces a log–log slope near 1 by construction. Partialling
log(1/λ̂) out moves the slope only 1.13 → 1.09, so the confound is not the
whole story, but a ratio of two near-zero quantities is not a measurement
either. P1 joins P2–P5 as not testable here.

Net effect on the claims: **exactly one of the five predictions is evaluable
with these data, and it returns a null.** That is now said plainly instead of
four numbers being presented as tests.

**Config C resolved, and my Round-3 hypothesis was wrong.** I had guessed the
random-walk surrogate was an inadequate null for a trended signal. Implemented
IAAFT surrogates (preserve spectrum *and* marginal) to test it, then tested two
more explanations when that failed:

| Explanation | Test | Result |
|---|---|---|
| Inadequate null | IAAFT preserves trend | C goes 0.149 → 0.161. **Refuted** |
| Clipping at ±4 | compare clip rates | B clips most (5.1%) and is nominal; C clips least (0.8%) and is elevated. **Refuted** |
| Mis-sized off unit root | size on AR(1), φ = 0.3…1.0 | ≤0.075 everywhere. **Refuted** |

Conclusion supported by the evidence: configs A and C carry genuine nonlinear
structure no surrogate reproduces — but **config A is the negative control**, a
coordinate already shown to be beat-detection-noise dominated, so nonlinearity
there means artefact, not fold. The negative control firing is what tells us
"significant" ≠ "cusp" in those configurations. That is the job it exists for.

**Config B (primary) is unaffected and stronger than before**: 0.046 against
random-walk surrogates, 0.069 against the much harder IAAFT ensemble.

Four new tests; suite now 32.

## 8. Open items

- [ ] Verify the 12 references marked `VERIFY` in `refs.bib` against their DOIs.
- [ ] Contact a.m.scheeren@vu.nl regarding the autistic-adult EMA raw data.
- [ ] Nurse survey labels (`SurveyResults.xlsx`) not yet joined to sessions —
      would add momentary ground truth to the corpus that most needs it.
- [ ] UKF estimator implemented but not yet run at scale as a robustness check.

---

## 8b. The power claim, corrected

The first two self-review rounds asserted the study had "power near unity."
That was taken from the **nominal** test, which the same analysis shows has a
false-positive rate of 0.42 — so its sensitivity was largely an inability to
stay quiet. Under the **calibrated** test at the median observed length
(n ≈ 200):

| regime | calibrated power |
|---|---|
| strong (λ=0.20, α₀=1.5) | 1.00 |
| moderate (λ=0.10, α₀=1.0) | 0.76 |
| weak (λ=0.05, α₀=0.6) | **0.24** |

The claim was corrected throughout — abstract, results, limitations,
conclusion, and the title, which no longer contains "well-powered null." The
result excludes strong and moderate cusp dynamics and does **not** exclude weak
ones. Reaching power 1.00 in every regime needs n ≈ 1000, about eight hours of
continuous wear per unit at a 30 s window.

Three claims in this project survived one round of checking and failed the
next: the circular state assignment, the early-warning estimator, and this
power figure. Worth recording in both directions — the checks are working, and
two rounds of review were not enough.

## 9. Honest standing assessment

The mathematical contribution is real and, as far as the searches conducted
here found, new: nobody has derived overload states from a fitted cusp
potential and tested the resulting scaling laws on physiological time series.
The estimator is exact and validated. The inference is more conservative than
the norm in this literature.

The paper's ceiling is set by one thing that no amount of analysis fixes: the
target population is not in the data. That is stated in the abstract, the
scope paragraph, the limitations and the title — which no longer names a
population it does not measure.

---

# Session: 2026-08-07 — submission readiness

Goal: get the artefact into a state that can be published as a repository and
submitted as a paper. Everything except acquiring autistic-participant data.

## The pattern this session exposed

Four rounds of self-review read the **manuscript**. None read the **compiled
PDF**, and none ran the **test suite**. Three of the five defects below are
invisible in the `.tex` source, and all three would have reached a reviewer.

The lesson is cheap to state and was expensive to learn: a LaTeX run that exits
zero is not evidence of anything. Overfull boxes, scaled-down figures and empty
`\bibitem`s are all warnings or silence, never errors.

## Defects

| # | Defect | How it hid |
|---|---|---|
| D1 | References [5] and [6] printed blank | BibTeX has no comment character; `@article{key, % note` makes the note the first field name. Empty `\bibitem`, no warning, exit 0 |
| D2 | Figs. 2 and 3 unreadable in print | Authored 7.16in, included at `\columnwidth`; LaTeX scaled fonts by 0.5. Not a warning condition |
| D3 | Test suite could not run | `code/` never on `sys.path`; the README's own command failed at collection |
| D4 | Four more bad references | Only caught by checking all 46 against Crossref/DataCite rather than spot-checking |
| D5 | Previous Monte Carlo run had crashed | BLAS oversubscription killed a worker; no checkpointing, so four blocks were lost and the supplement cited their 2–3 replicate remains |

D1 is the one to remember. The notes that broke those entries were added *by
Round 4's citation audit* — a fix that introduced a worse defect than the one it
repaired, in a file format where the mistake is silent.

## What the re-run changed in the science

Recovery went from 600 to 2000 replicates per length. Pearson correlation for
α₀ at n=1000 **fell from 0.59 to 0.10**, which looked like a broken run.

It was not. The recovered α̂₀ at that length spans [−140, 3.3] against a 99th
percentile of 2.0. One replicate in two thousand drags the linear correlation to
the floor. Spearman on the same data is **0.88**.

That gap is the paper's own thesis appearing in its own diagnostics: `a = θ₂/θ₁`
with nothing bounding θ₁ away from zero. **Dividing by a small number preserves
order and destroys scale.** Reporting Pearson alone understates recovery;
Spearman alone overstates what can be published from it. Both are now reported.

The claim is consequently sharper than it was:

> Length buys a defensible **ranking** by α₀ (ρ: 0.33 → 0.88).
> Length never buys a reportable **value** (r: 0.15 at n=200, 0.10 at n=1000).

Two corrections followed. S4 had said α_A "never becomes identified" — in rank it
reaches 0.72, and the old phrasing was easy to falsify. And the pre-registration
justified itself entirely on `n ≳ 500` rescuing α₀, without noticing that P3–P5
rest on the two parameters length does *not* fix.

## A contradiction between our own two documents

`main_full_journal.tex` opened its results with "The estimator recovers what it
should": α₀ at r = 0.98. The conference paper's central finding is that α₀ is
not recoverable. Both were in the repository.

The journal number is not wrong; it answers an easier question. E1 simulates at
**n = 4000** windows against a median of **194** in the corpora, and draws true
λ from [0.10, 0.28] against a median of **0.0059** in the real fits. Two
compounding optimisms, neither disclosed where the claim was made.

Kept the number and explained why it misleads, rather than deleting it. A reader
learns more from the contrast than from a clean page.

## Infrastructure

- `mega_run.py` rewritten: thread limits set before numpy import, work chunked
  and checkpointed, dying chunks bisected to isolate one poison replicate,
  `--resume` continues an interrupted run. Replication raised 2–5×.
- `compile_paper.py` now asserts page count, reports overfull boxes with source
  lines, and **fails on empty bibliography entries** — the only tool in the
  chain that catches D1.
- `make_figures_v2.py` records each figure's intended width and refuses to save
  a mismatch, which is D2 made impossible.
- `check_citations.py` verifies every DOI against Crossref with a DataCite
  fallback. Two of its own findings turned out to be checker bugs, both fixed;
  a checker that cries wolf gets ignored.
- Added `pyproject.toml`, `requirements.txt`, `LICENSE`, `CITATION.cff`,
  `reproduce.py`, and CI asserting all three defect classes on every push.

## State

Conference paper: 5 pages at the time of this entry (six as of 2026-08-12,
after the reviewer-requested settings, availability and scoping text went in),
zero overfull boxes, no unresolved references,
`--strict` clean. Journal draft: 14 pages, same. 32 tests pass. 42 of 46
references verified against publisher metadata, 0 disagreements.

Unchanged, and unchangeable today: no autistic participants, and a null result.
