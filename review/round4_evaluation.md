# Adversarial self-review — Round 4

A fresh critical read of the manuscript, followed by implementation. Unlike
Rounds 1–3, this round was asked to *find and fix*, so every item below is
either fixed or explicitly deferred with a reason.

Prior: **18/50** (inherited) → 38 → 40 → **41/50**.

---

## Defects found this round

### D1. A baseline was silently reporting nothing — **FIXED**

The multinomial-logistic row of the model-comparison table was empty. Cause:
`LogisticRegression(multi_class=...)`, an argument scikit-learn removed in 1.7.
The resulting `TypeError` was caught by a bare `except: pass` in the caller, so
the baseline contributed zero folds and the table simply showed a blank.

Severity: high. A reviewer comparing against a baseline that was never actually
run is being misled, and the bare-except idiom meant nothing would ever have
surfaced it.

Fixed: argument removed (multinomial is the default for the lbfgs solver, so
behaviour is unchanged), **and every silent except in E4 replaced with a logged
one**, and per-model fold counts now recorded so an absent baseline shows as a
zero rather than a gap.

### D2. The model comparison conditioned on the outcome — **FIXED**

E4 ran only on units where the cusp geometry was identified: 37 of 157. But
CHM, OU, HMM and GBM need only the series; the geometry is irrelevant to
one-step-ahead prediction. Restricting to identified units is precisely the
survivorship bias that was identified and closed in `e2_fit_all` — reintroduced
one function later.

Severity: high, and embarrassing given the paper makes a point of having closed
that exact bias elsewhere.

Fixed: all units scored; state-based baselines scored where states exist; per
model *n* reported.

### D3. The nurse corpus was sampled from 5 of 15 people — **FIXED**

`nurse_subjects()` sorted by path and the runner truncated. Because sessions
are named `<nurseID>_<timestamp>`, path order returns every session of one
nurse before any of the next, so a cap of 150 sessions drew 112 recordings from
**5 nurses**, while the paper's Corpora section described "15 nurses,
\SI{1250}{\hour}".

Severity: high. That is a mismatch between what the paper says was analysed and
what was analysed.

Fixed: session ordering is now round-robin by nurse, so any cap spans all 15.
Verified: caps of 60, 150 and 300 all now return sessions from 15 nurses. The
Methods section documents the choice and why the naive one fails. **All
analyses re-run.**

### D4. Three predictions were stated and never resolved — **FIXED**

P3 (dwell over-dispersion), P4 (re-entry hazard) and P5 (larger $\alpha_A$,
longer recovery) appeared in Sec. III and then never again in Results. A
reviewer notices this immediately.

Fixed: new Sec. V-F states plainly that all three are defined on the derived
state sequence, which exists only where the geometry is identified — and that
among those units the median $\hat\lambda$ is $0.0059$, so the states are not
measurements of anything. The dwell-time number the pipeline does produce
(excess CV $+0.74$) is reported *and explicitly declined* as support, with the
reasons. P3–P5 are returned to the "awaiting adequate data" pile rather than
left dangling.

### D5. Six references had wrong authors or venues — **FIXED**

Verified all flagged entries against the Crossref API. Findings:

| Entry | Defect |
|---|---|
| `millidge2023` | Wrong authors — the paper is by Arthur, Vine, Buckingham, Brosnan, Wilson & Harris |
| `bos2021` | **Wrong paper entirely** — that DOI is Squarcina et al. on deep learning for treatment response, not an EWS paper |
| `turanbirol2023` | Wrong authors — Li, Henning & Camerer |
| `can2024` | Wrong authors *and* venue — Cano et al. in *Sensors*, not Can et al. in *IEEE RBME* |
| `kirtley2025openesm` | Wrong authors — openESM is Siepe, Haslbeck, Kloft & Büchner |
| `auge2025`, `kiep2025`, `chen2025ema` | Wrong years, wrong first name, missing volume/pages |

Severity: **highest of anything found in four rounds.** Six of nine
spot-checked entries were wrong, including one that cited a completely
different paper. Submitting that would have been a serious credibility problem
and is the kind of thing that gets a paper desk-rejected or retracted.

Fixed: all nine corrected against publisher metadata, citation keys renamed
throughout, `REFERENCE_CHECK.md` rewritten with a corrections table.

### D6. Configuration C's non-replication — **RESOLVED, and my hypothesis was wrong**

Round 3 left this open with a hypothesis and no test: that the random-walk
surrogate is an inadequate null for a trended signal. I implemented IAAFT
surrogates (Schreiber & Schmitz 1996) to test it, then tested two further
explanations when that one failed. **All three were refuted.**

| Explanation | Test | Result |
|---|---|---|
| Inadequate null (trend not in surrogates) | IAAFT preserves spectrum + marginal | C goes $0.149 \to 0.161$. **Refuted** |
| Clipping at $\pm4$ induces false cubic | Compare clip rates | B clips most ($5.1\%$) and is *nominal*; C clips least ($0.8\%$) and is elevated. **Refuted** |
| Test mis-sized away from unit root | Size on AR(1), $\phi=0.3\ldots1.0$ | size $\le 0.075$ everywhere, usually $<0.03$. **Refuted** |

What the evidence actually supports: configurations A and C contain genuine
nonlinear structure that neither surrogate ensemble reproduces. But **config A
is the negative control** — a coordinate independently shown to be dominated by
beat-detection error — so nonlinearity there is far better explained by motion
artefact and peak-detection failure than by a fold. The same class of
explanation covers skin temperature (warm-up transients, contact loss).

A test that fires on the negative control is telling us that "significant" does
not mean "cusp" in those configurations. That is exactly the job a negative
control exists to do, and it is the reason the paper's conclusion rests on
configuration B alone.

**Config B is unaffected and now stronger**: $0.046$ against the random-walk
ensemble and $0.069$ against the considerably harder IAAFT ensemble — nominal
under both.

Recorded here because publishing a speculative cause (Round 3) and then
refuting it with three experiments is the useful part of the record.

---

## What did not change

- **The result is still a bounded null.** None of the above turns it positive.
- **Still no autistic participants.** Unchanged and unchangeable today.
- **Section III is still dense.** Deferred; it is a presentation issue, not a
  correctness one, and shortening it risks the derivation's completeness.

---

## Rescoring

| Dimension | R3 | R4 | Why |
|---|---|---|---|
| Novelty | 8 | 8 | Unchanged |
| Rigour | 10 | 10 | Held: three real biases found and closed, but finding them this late is itself evidence earlier rounds were not thorough |
| Empirical support | 6 | 7 | Comparison now on the full corpus with a working baseline set; sampling covers all 15 nurses; clustering handled |
| Clarity | 8 | 8 | P3–P5 resolved; Methods documents sampling |
| Impact | 8 | 8 | Unchanged |

## Total: 41/50

Unchanged in total, and that is the honest number. The work is materially more
trustworthy than it was this morning — a broken baseline, a survivorship bias,
a sampling defect and six bad citations are all gone — but none of those fixes
adds a finding. They remove ways the paper could have been wrong.

The score is capped by the same thing it has been capped by since Round 1: no
autistic participants, and a null rather than a positive result.

## Standing open items

- [ ] Complete the IAAFT comparison across configs B/C/A (running)
- [ ] Contact a.m.scheeren@vu.nl about the autistic-adult EMA raw data
- [ ] Trim to 8 pages if targeting a conference
- [ ] Spot-check the 31 "canonical" references; four rounds of experience say
      the base rate of citation error in this project is not low
