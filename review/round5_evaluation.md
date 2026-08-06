# Adversarial self-review — Round 5

Scope: submission readiness. Everything a reviewer sees before they reach the
argument — the compiled PDF, the bibliography, the figures — plus a re-run of
the Monte Carlo suite at replication counts high enough to trust.

Prior: 18 → 38 → 40 → 41 → **43/50**.

The theme of this round is that four previous rounds read the *manuscript* and
none of them read the *compiled artefact*. Three of the five defects below are
invisible in the `.tex` source and obvious in the PDF.

---

## Defects found this round

### D1. Two references printed as blank entries — **FIXED**

References [5] and [6] appeared in the compiled PDF as numbered entries with no
content. `adamou2026` and `cano2024`, both cited in the introduction.

Cause: **BibTeX has no comment character.** Eight entries carried a verification
note written as

```bibtex
@article{adamou2026,        % CONFIRMED 2026-07-22
```

BibTeX reads what follows the opening brace as the first field name, so the
record parses to nothing. It emits a `\bibitem` with an empty body rather than
raising an error. The citation therefore counts as *defined*, no warning fires,
and the compile exits zero.

Severity: **highest this round.** A reference list with two blank entries is the
kind of thing that gets noticed in the first thirty seconds of a review. The
irony is that the notes causing it were added by Round 4's citation audit.

Fixed: all eight moved above the `@`, where BibTeX genuinely ignores them.
`compile_paper.py` now parses the `.bbl` and fails on any `\bibitem` with an
empty body, because nothing else in the toolchain reports this.

### D2. Both single-column figures were unreadable in print — **FIXED**

Figs. 2 and 3 were authored 7.16 in wide (double-column) and included at
`\columnwidth` (3.49 in). `\includegraphics[width=...]` scales the entire
graphic, fonts included, so a factor of two came off every label: 8 pt axis text
printed at roughly 4 pt, legends smaller still.

Severity: high, and it would have survived to camera-ready. Nothing in the LaTeX
log mentions it — a scaled graphic is not a warning condition.

Fixed: both authored at the width they are included at, and stacked rather than
side by side, since two panels sharing a 3.5 in column leaves each too narrow
for a log axis plus a legend. `make_figures_v2.py` now records the intended
width per figure and refuses to save one that does not match.

Fig. 2a separately had its legend drawn on top of the data and the "identified"
annotation colliding with the top curve. No recovery curve falls below −0.1, so
the legend moved into the empty band under zero.

### D3. The test suite did not run — **FIXED**

`python -m pytest code/tests`, the command the README gave, failed at collection
with `ModuleNotFoundError: No module named 'chm'`. Nothing put `code/` on
`sys.path`.

Severity: moderate for correctness — the tests pass once they can import — but
high for credibility. "32 tests" in a README that cannot execute them is the
first thing a sceptical reader checks.

Fixed: `pyproject.toml` sets pytest's `pythonpath`. All 32 pass from a clean
checkout. Added `requirements.txt`, `LICENSE`, `CITATION.cff` and a
`reproduce.py` with a `--stage check` that runs tests, citation consistency and
a layout-asserting compile with no data and no network.

### D4. Four more bad references, and two false-positive classes — **FIXED**

Round 4 checked nine entries by hand and found six wrong. This round automated
it over all 46 against Crossref, with a DataCite fallback.

| Entry | Defect |
|---|---|
| `wichers2021` → `helmich2021` | Wrong first author (Helmich, not Wichers — she is fourth) **and** wrong pages (51–58, not 105–110) |
| `kiep2023` → `kiep2025` | Print issue is 55(6), 2025; entry carried those pages with the online-first year |
| `auge2024` → `auge2025` | Same defect, 55(8), 2025 |
| `chen2024ema` → `chen2025ema` | Same defect, 29(6), 2025; also missing its issue number |

The three year corrections **reverse a Round 4 change**. Round 4 moved them from
the print year to the online-first year while keeping the print volume and
pages, which is internally inconsistent: a reader following *JADD* **55**(6),
2075–2084 arrives at a 2025 issue. The reasoning is now recorded in
`REFERENCE_CHECK.md` so a Round 6 does not flip them a third time.

Two of the checker's own findings were **its** bugs, not the bibliography's:

- It read Crossref's `issued` field, which for any journal posting ahead of
  print is the online-first year, and so flagged four correct entries.
- It treated a Crossref 404 as a bad DOI. PhysioNet registers with DataCite, so
  `amin2022exam` looked broken and was not.

Both fixed. A checker that cries wolf gets ignored, which is worse than none.
Final state: 42 verified clean, 4 without a DOI (pre-DOI classics, hand-checked),
0 disagreements.

### D5. The previous Monte Carlo run had crashed, and the supplement cited its
### wreckage — **FIXED**

`log_mega.txt` showed the run dying 20 minutes in with a
`TerminatedWorkerError` partway through the power block. Recovery and size had
completed; power, persistence, EWS and noise had not. The leftover
`m3`–`m6` files held **two- and three-replicate smoke output**, and
`SUPPLEMENT.md` cited `m3_power_summary.csv` and `m5_ews_summary.csv` as though
they were the high-replication results. The paper itself was safe — it quoted
the older, valid `e0` and `e12` files — but a reviewer opening the supplement's
data would have found the power claim resting on three simulations.

Two causes, both fixed:

- **BLAS oversubscription.** Each loky worker spawned its own OpenMP/MKL thread
  pool: ten workers on a twelve-thread machine requesting over a hundred
  threads. The limit variables are now set before numpy is imported, which is
  the only point they take effect.
- **No checkpointing.** Work is now chunked; each chunk runs in a fresh pool,
  appends to a partial CSV and marks itself done, so a crash costs one chunk and
  `--resume` continues. A chunk whose worker dies is bisected to the individual
  replicate.

Smoke files deleted rather than shipped. Replication raised now that a long run
survives: size 2000 → 5000, power and recovery → 2000, persistence and noise →
1000, EWS → 500.

---

## What the re-run changed in the science

### The identifiability result got sharper, via an apparent regression

At 2000 replicates, Pearson correlation for α₀ at n=1000 came back at **0.10**,
down from 0.59 at 600 replicates. That looks like a broken run. It is not.

The recovered α̂₀ at n=1000 spans [−140, 3.3] against a 99th percentile of 2.0.
One replicate in two thousand drags the linear correlation to the floor.
Spearman on the same data is **0.88**.

That gap is the paper's own thesis appearing in its own diagnostics: `a = θ₂/θ₁`
with nothing bounding θ₁ away from zero. Dividing by a small number preserves
order and destroys scale. Reporting Pearson alone understates recovery;
reporting Spearman alone overstates what can be published from it.

Both are now reported, and the claim is stronger and more precise than it was:

> Length buys a defensible **ranking** of participants by α₀ (ρ: 0.33 → 0.88).
> Length never buys a reportable **value** (r: 0.15 at n=200, 0.10 at n=1000).
> A study wanting the value needs a parameterisation estimating `a` and `b`
> directly, not a longer recording.

This also corrected an overstatement in S4, which had said α_A "never becomes
identified". In rank it reaches 0.72 at n=1000. The value never does. The
earlier phrasing would have been easy for a reviewer to falsify.

### The full grid refuted one of our own claims

The paper said the rolling estimators return the wrong sign "in every
configuration tested". At 500 replicates across all ninety configurations that
is **false**: 16 of 60 rolling configurations carry the correct sign, every one
of them at the longest window.

The corrected statement is stronger. There are two regimes. At windows 20–120
the sign is inverted and near-totally so — 99% of replicates wrong for variance
at window 30, with several configurations inverting in all 500. At window 240
both indicators collapse onto zero (medians −0.018 to +0.027), so the sign
becomes a coin flip and the "correct" cases are correct by accident at a
twentieth of the predicted magnitude.

So widening the window does not rescue the estimator. It trades a confident
wrong answer for no answer. That is a sharper indictment of the method than the
overclaim was, and unlike the overclaim it survives contact with 15,000 series.

Worth recording as the fourth claim in this project to survive one round of
checking and fail the next.

### A gap in the pre-registration

Table I shows ε reaching only ρ = 0.44 at n=1000 and α_A's value never
recovering, yet the pre-registered design justified itself solely on
`n ≳ 500` rescuing α₀. P3–P5 depend on exactly the two parameters that length
does not fix. The limitations and the validation section now say so, and name
what would be needed instead: experimental control over recovery intervals, or
a hierarchical fit pooling those parameters across participants.

---

## Rescoring

| Dimension | R4 | R5 | Why |
|---|---|---|---|
| Novelty | 8 | 8 | Unchanged |
| Rigour | 10 | 10 | Held. The Spearman/Pearson split and the two-regime EWS correction are real gains, but three of five defects this round were visible in the PDF and four rounds had not looked |
| Empirical support | 7 | 8 | Recovery and size at 2–5× replication; the identifiability claim is now decomposed rather than asserted |
| Clarity | 8 | 9 | Figures legible; Table I carries the argument instead of restating it |
| Impact | 8 | 8 | Unchanged |

## Total: 43/50

Still capped by the same thing since Round 1: no autistic participants, and a
null rather than a positive result. Neither is fixable before the EMA study.

## Standing open items

- [ ] Contact a.m.scheeren@vu.nl about autistic-adult EMA raw data
- [ ] Power, persistence, EWS and noise blocks at full replication (running)
- [ ] Refresh Fig. 3 and the power sentence once the power block lands
- [ ] Decide venue; the paper is at exactly 5 pages with zero overfull boxes
- [ ] The journal draft (`main_full_journal.tex`) has not had the Spearman
      treatment and still carries the single-correlation framing
