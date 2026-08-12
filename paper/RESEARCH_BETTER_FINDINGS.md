# research-better findings — `main.tex` (six-page IEEE conference version)

Tool: `research-better 0.3.0`, full 10-pass run on 2026-08-10.
Command: `research-better --verbose run main.tex`
Raw artifacts: `.research-better/` (grounding.md, novelty.md, reviewer-questions.md, trace.md, report.md/html/json).

## Status board (updated 2026-08-12, final)

| Item | What | Status |
|---|---|---|
| 1 | No contribution claim | **done** — claim sentence added, `main.tex` |
| 2 | Twelve citation year mismatches | **won't fix — refuted.** See the note under item 2 |
| 2b | Low author-match scores | **done** — eight author lists expanded from Crossref |
| 3a | "Outperforms what?" | **done** — negative control named as a reference channel |
| 3b | Hyperparameters never stated | **done** — new `\subsection{Settings}` |
| 3c | Hardware never stated | **done** — in the same subsection |
| 4a | Which component produces the gain | **done** — stated plainly, with the reason |
| 4b | No availability statement | **done** — new Code and Data Availability section |
| 5a | Ungrounded critical-slowing sentence | **done** — grounded in Sec. II and Table II |
| 5b | "never" doing unsupported work | **done** — pinned to the Sec. IV numbers |
| 5c | Introduction hedging density | **done** — re-measured; mostly a matcher artefact |
| B1 | Non-identifiability is the result | **done** — title, abstract, introduction and contributions all lead with the bound |
| B2 | The identifiable prediction fails | **done** — the two losses now stated jointly |
| B3 | EWS failure oversold in the title | **done** — scoped to rolling-window estimators in text and title |
| B4 | Motivation vs. data mismatch | **done** — corpora justified, framing kept |
| B5 | Scope and residual arbitrariness | **done** — remaining knobs named in Limitations |
| B6 | What works — preserve | n/a |
| B7 | The durable residue | **done** — the residue sentence now opens the discussion |

**Page budget: resolved as six pages, on the author's decision.** Earlier
passes of this file said the paper could not be compiled because `pdflatex` is
absent. That was wrong: `tools/tectonic.exe` is in the repository and builds it
fine. Measured on 2026-08-11:

| build | pages | body characters |
|---|---|---|
| `HEAD` (committed) | 5 | 34,006 |
| working tree, after four fix passes | **6** | 38,464 (+13%) |

The committed version had no slack --- its page 5 was already 6,550
characters --- so the +4,458 characters of reviewer-requested text spills onto
a sixth. Holding five would have meant cutting essentially all of it, or
dropping the geometry figure. The author chose six on the condition that the
content justifies it. Page 6 comes out nearly full, so it is not a wasted page.
**The venue's page limit was confirmed by the author on 2026-08-12: six pages
is within budget.**

Changed to make six pages real, rather than leaving assertions that lie:

- `reproduce.py` and `compile_paper.py` asserted 5 pages; both now assert 6.
- `compile_paper.py` wrote `paper_5page.pdf`. It now writes
  `paper_conference.pdf` --- a filename with a page count in it goes stale
  silently. The stale PDF has since been removed from the tree.
- `README.md` updated for both.
- `main.tex` preamble records why it is six and that the venue needs checking.

Three defects surfaced while compiling, all fixed:

- A `%` comment placed inside the `demetriou2018` entry silently voided it.
  BibTeX has no in-entry comments, and the entry was rendering with empty
  author, title, journal and year. The comment now sits outside the braces.
- `IEEEtranBSTCTL` now truncates author lists at six names and "et al.", which
  is IEEE style and keeps the full lists in `refs.bib` for checking.
- `check_citations.py` counted the new control entry as an uncited reference.
  It now skips `@IEEEtranBSTCTL`, so the count is 46 entries again.

Current state: **6 pages, 0 overfull boxes, no empty references, 16/16 cited
keys resolving, and all 18 cited claims verified against source.**

The claim-level audit is the substantive outcome of this whole exercise. The
`trace` pass flagged three sentences as citing claims their sources do not
carry. Checking those by hand turned up four such sentences in total, across
six citations; all four are fixed and the audit is recorded in
`REFERENCE_CHECK.md`. The tool could only retrieve three full texts, so it
found the minority of the problem. The rest came from reading the sources.

**The journal draft is synced.** `main_full_journal.tex` carried the same
defects; it now has the contribution claim sentence, a `Settings` subsection
with the hyperparameters and hardware, a Code and Data Availability section,
the negative-control clarification, the general-stress-corpora justification,
and a title in the same frame as the conference paper. It compiles clean at 14
pages. The supplement was not touched.

## Round 2 of the tool: rerun on 2026-08-11, after the fixes

`research-better` is installed (`~/AppData/Roaming/Python/Python312/Scripts`),
so the fixes are verified rather than assumed. Before and after:

| | first run | after fixes |
|---|---|---|
| contribution claim | **not found** | found, and confirmed |
| blocking questions | 1 | **0** |
| serious questions | 3 | 2, both false positives (below) |
| fluff findings | 2 | **0** |
| trace passages | 5 | 4 |
| `edit` pass | never ran | **runs** |

### The `edit` pass finally ran, and both its proposals were rejected

Item 1 was worth fixing for this reason, and the first thing the pass produced
was two cuts that must not be made:

1. Delete "The latent load obeys a gradient relaxation with additive noise,"
   --- the sentence that introduces (1). That leaves a displayed equation
   dangling off a subsection heading. It is the math orphan-paragraph false
   positive the first run already warned about.
2. Delete the **entire Acknowledgment**, including the IEEE-mandated
   generative-AI disclosure. Part B6 explicitly says keep that disclosure.

Neither was applied. The pass is worth running and its output is worth reading,
but it cannot be applied unread.

### Fixed this round

- **Blocking question, "where is the contribution established?"** The claim
  sentence was abstract and shared no vocabulary with the body. It now names
  the three sections that establish its three clauses. The blocking question is
  gone.
- **A real citation defect.** `demetriou2018` was cited for "adult cohort
  studies couple sensory atypicality to executive difficulty with large effect
  sizes". The retrieved full text says the opposite of the last part --- "the
  generally smaller effect sizes on EF observed for the adult" --- and the
  meta-analysis is about executive function, not sensory--executive coupling.
  The sentence now credits `kiep2025` with the coupling and states the
  meta-analytic finding as smaller adult effect sizes. This is the one
  substantive error the tool caught in either run.
- **Empty forward reference.** "in what follows" now points at Sec. V.
- **Two unsupported superlatives**, both introduced by earlier fix passes
  ("the only component", "the only baselines"), rewritten without them. `fluff`
  is back to zero findings.

### Two serious questions remain, both false positives

- *"Outperforms what, exactly?"* now fires on the sentence written to answer
  it, because that sentence contains the word "outperformed". The matcher is
  lexical.
- *"What hyperparameters were used?"* still fires despite the `Settings`
  subsection. The matcher appears to look for machine-learning vocabulary
  (learning rate, batch size) that a Monte Carlo study does not use.

### Still failing, still refuted

`13 unverified citations` = the 12 year mismatches refuted under item 2, plus
`zeeman1976`, a 1976 *Scientific American* article with no DOI. It is one of
the four DOI-less entries `REFERENCE_CHECK.md` documents and confirms by hand.

One flag is left open rather than fixed: the opening sentence, cited to
`maclennan2022` for "it arrives suddenly, and it clears slowly", scores 0.188
coverage against the retrieved full text. The tool's own note says lexical
matching can miss a claim supported in different words and to check by hand
first. That check needs someone who can read the paper against the sentence, so
it is left for the author rather than guessed at.

## Summary

```
ingest       159 sentences, 2976 words, 16 citations used, 46 in bibliography
novelty      NO CONTRIBUTION CLAIM FOUND        <- blocks everything downstream
ground       34/46 resolved clean, 12 year mismatches, 0/16 full texts retrieved
originality  0 overlaps found (13 sources, 3 unretrievable)
fluff        0 findings
trace        3 flagged, 2 dismissed as false positives
ask          0 blocking, 3 serious, 2 minor
report       12 unverified citations (limit 0) -> CHECK FAILED
```

The `edit` pass **refused to run**. It will not propose cuts until the contribution
claim is confirmed, and no claim was found. Fixing item 1 unblocks it.

---

## 1. No contribution claim found (highest severity)

**Status:** DONE. The sentence below now sits immediately above the
contributions list in `main.tex`, with a third clause naming the ground-truth
test. Not yet re-run through the tool, so the `edit` pass is still unexecuted.

The contributions sit in `\noindent\textbf{Contributions.} (i) ... (iv) ...` at
`main.tex:118`. The parser does not recognise that as a claim, and there is no single
declarative "we present / we propose X" sentence anywhere in the abstract or the
introduction. The abstract opens with problem framing ("Overload is usually modelled
by...") and the closest thing to a claim is "We take a different route," which asserts
nothing checkable.

**Verified cause.** Tested on a copy: inserting one sentence before the contributions
list —

> We present a cusp-catastrophe formulation of overload together with an
> identifiability analysis that bounds what any such analysis can recover from
> wearable data.

— made the pass fire immediately.

**Fix.** Add one plain claim sentence before the contributions list. This matters
beyond the tool: a reviewer skimming the introduction currently hits four Roman
numerals with no one-line thesis above them.

**Caveat.** Once a claim exists, the pass reports 16 "orphan paragraphs," almost all of
them the equations in Sec. II–III. That is the tool's lexical matcher failing on math,
not a defect in the paper. Ignore those.

---

## 2. Twelve citation year mismatches

**Status:** WON'T FIX — refuted. `refs.bib` is unchanged and should stay
unchanged.

This is a known false positive, already investigated and recorded in
`REFERENCE_CHECK.md` (sections "Corrections made in this pass" and "Two
false-positive classes the checker used to produce"). research-better is
reading Crossref's `issued` field, which is the earliest registered date and
therefore the online-first year for any journal that posts ahead of print. The
bib entries carry the **print issue** volume, number and pages, and the year has
to match those: `kiep2025` cites *JADD* **55**(6), 2075--2084, which is a 2025
issue, not a 2023 one. Round 4 of the self-review flipped three of these the
wrong way and Round 5 reversed it for exactly this reason.

`thom1975` and `hutzenthaler2012` are already marked keep in the table below.

The consequence is that `12 unverified citations, limit 0` will keep failing on
every rerun until research-better prefers `published-print` over `issued`, the
way `code/experiments/check_citations.py` already does. That is a tool
configuration issue, not a manuscript defect.

Original table, retained for the record. Bib year -> record year:

| key | bib year | record year | DOI | action |
|---|---|---|---|---|
| `kiep2025` | 2025 | 2023 | 10.1007/s10803-023-06008-4 | fix |
| `maclennan2022` | 2022 | 2021 | 10.1007/s10803-021-05186-3 | fix |
| `demetriou2018` | 2018 | 2017 | 10.1038/mp.2017.75 | fix |
| `auge2025` | 2025 | 2024 | 10.1007/s10803-024-06385-4 | fix |
| `chrysaitis2023` | 2023 | 2022 | 10.1016/j.neubiorev.2022.105022 | fix |
| `leemput2014` | 2014 | 2013 | 10.1073/pnas.1312114110 | fix |
| `boucsein2012` | 2012 | 2011 | 10.1007/978-1-4614-1126-0 | fix |
| `greco2016cvxeda` | 2016 | 2015 | 10.1109/tbme.2015.2474131 | fix |
| `nahumshani2018` | 2018 | 2016 | 10.1007/s12160-016-9830-8 | fix |
| `chen2025ema` | 2025 | 2024 | 10.1177/13623613241305722 | fix |
| `thom1975` | 1975 | 2018 | 10.1201/9780429493027 | **keep 1975** — 2018 is the CRC reprint |
| `hutzenthaler2012` | 2012 | 2010 | 10.1214/11-aap803 | **keep 2012** — 2010 is the arXiv preprint |

### Low author-match scores (secondary)

**Status:** DONE. Eight entries carried `and others`; all eight now carry the
full author list as deposited with Crossref. `demetriou2018` is kept in
initials because that is what the publisher deposited — expanding it would have
been guesswork. The two remaining flagged keys were never truncated:
`chrysaitis2023` has both its authors and `grasman2009` all three; their low
scores come from the compound surname "Angeletos Chrysaitis" and from the Dutch
name particles. Nothing was masking a wrong entry.

Original note follows. Ten entries scored <= 0.667 on author matching but resolved by DOI, so this is
near-certainly truncated author lists in `refs.bib`. Worth a glance that no
`and others` is masking a wrong entry:

`demetriou2018`, `chrysaitis2023`, `grasman2009`, `scheffer2009`, `scheffer2012`,
`dakos2012`, `leemput2014`, `eisenberg2019`, `hosseini2022nurse`, `nahumshani2018`

---

## 3. Reviewer questions — serious

**Status:** DONE (3 of 3).

- **3a** — Sec. III-B now says the cardiac index is a reference channel used to
  justify a sensor assignment, not a competing method, and that no published
  system is claimed to be outperformed.
- **3b, 3c** — a new `\subsection{Settings}` closes Materials and Methods.
  Every number in it is read off the repository, not estimated: `mega_run.py`
  (master seed, `N_SURR=200`, the `REP_*` counts, `LENGTHS`, ten workers on six
  physical cores), `power_analysis.py` and `size_vs_persistence.py`
  (`N_SURR=100`), `ews.py` (IAAFT `n_iter=200`), `results/PROVENANCE.md` (grid
  coverage, 100/cell power, 40/point persistence) and `README.md` (~7 h on six
  cores). The repository records no CPU model, so the paper says "a six-core,
  twelve-thread CPU" and stops there.

### 3a. "Outperforms what, exactly?"

Triggered on the EDA-vs-cardiac comparison:

> At a \SI{30}{\second} window tonic electrodermal activity has lag-1 autocorrelation
> $0.98$, while a cardiac index from heart rate and RMSSD has $0.19$ [...]

No named point of comparison. A reviewer who cannot tell what was beaten assumes the
flattering comparison was chosen.

**Resolves it:** name the compared system and cite it, or state explicitly that the
cardiac index is a within-paper reference channel and not a competing method.

### 3b. Hyperparameters are never stated

The Monte Carlo study (1.2x10^4 simulated series), window widths, and surrogate
ensemble sizes are not given anywhere.

**Resolves it:** a settings paragraph in the method, or an appendix pointer.

### 3c. Hardware is never stated

**Resolves it:** one sentence in the method.

---

## 4. Reviewer questions — minor

**Status:** DONE (2 of 2).

- **4a** — stated plainly, as the second option in the finding. The results
  section now says the full-vs-nested-monostable comparison is the only
  component separation the data support, and gives the reason the others were
  not run: `alpha_A` and `epsilon` are unidentified at these lengths, so an
  ablation over them would attribute a change in fit to something the data
  cannot resolve. There is no component-wise ablation in `results/` to report
  — `e4_comparison_cfg*.csv` holds only whole-model comparisons — so inventing
  one was not an option.
- **4b** — new `\section*{Code and Data Availability}` before the
  acknowledgment, pointing at the MIT-licensed GitHub artefact from
  `CITATION.cff` and stating that the three corpora are third-party and not
  redistributed.

### 4a. Which component produces the gain?

No per-component evidence. Report the result with each component removed in turn, or
state plainly that the components were not separated and why.

### 4b. No code / data / environment availability statement

The paper says nothing about availability. Add a sentence saying where code and data
are, or why they cannot be released. Given the paper's posture of honesty about what
was not measured, the absence stands out.

---

## 5. Ungrounded assertions flagged by `trace`

**Status:** 5a and 5b DONE; 5c PARTIAL.

- **5a** — grounded rather than cut. The paragraph now derives the saturation
  from the paper's own `lambda_rel ∝ mu^{1/2}`, so the correlation time diverges
  as `mu^{-1/2}` while the window is fixed, and points at the window-30 and
  window-240 rows of Table II as the two ends of one bias.
- **5b** — the "never" is kept but pinned to the evidence: six lengths,
  1.2x10^4 series, `r` for `alpha_0` at 0.15 for n=200 and 0.10 for n=1000.
- **5c** — DONE, and largely refuted on measurement. Re-measured per section
  with a hedge-density script over `prose_stats.strip_latex`. Absolute values
  differ from the tool's (different hedge list), but the ranking reproduces:
  Introduction 1.51 per hundred words against a paper-wide 0.78, the highest of
  any section. Listing the actual hits explains it. Four of the seven are
  `rather than`, which is contrastive rather than epistemic; two more are
  substantive verbs (`could contradict`, `appears`). Exactly one was a true
  hedge and it was removed in the previous pass. What is real is the tic: four
  `rather than` constructions in one section. One is now `instead of`, another
  rewritten. No further action; the flag is a matcher artefact.

### 5a. Sec. "The early-warning estimator fails on ground truth", paragraph 2

> Critical slowing down means the relaxation time diverges at the fold, so a
> fixed-width window saturates exactly where the effect is **largest**.

Attach the measurement taken or the work that establishes it. If neither exists, cut.

### 5b. Discussion and Conclusion, paragraph 2

> Reporting a value needs a reparameterisation estimating $a$ and $b$ directly, since
> length alone **never** [...]

"Never" is a strong claim doing unsupported work. Point at the identifiability result
or soften it.

### 5c. Introduction — voice hedging (review, not a defect)

Hedging density 0.45 per hundred words in the Introduction against 0.07 paper-wide,
further from the paper mean than any other section. This is voice inconsistency, not an
error. Worth a read-through for tone.

**Dismissed as likely false positives** (no action needed): "What This Data Can
Identify" paragraphs 2 and 3, flagged only on sentence-length rhythm.

---

## Came back clean

- **`fluff`: zero findings.** No mechanical padding, no advisory cuts.
- **`originality`: zero overlaps** across 13 comparable sources.
- 34 of 46 bibliography entries resolved with title, author, and year all matching.

---

## What could NOT be checked — do not over-read the clean results

- **0 of 16 cited works had retrievable full text.** The originality pass compared
  against abstracts only, and all 16 cited claims came back `claim_uncheckable`. The
  zero-overlap result is close to uninformative and is **not** a plagiarism clearance.
- **Semantic Scholar was unreachable** during the run, so a missing record means less
  than usual.
- The `edit` pass has never executed (blocked by item 1).
- Rules `paragraph_shape_uniformity` and `sentence_length_variance` are switched off in
  the tool pending calibration.
- No verified venue profile, so questions used conservative defaults rather than
  IEEE-specific policy.

---

## Suggested order of work

Items 1, 3a--3c, 4a, 4b, 5a, 5b and B7 are done; item 2 is refuted. What is
left:

1. **Confirm the venue allows six pages.** This is the only open blocker. If
   it is a hard five, the fallback is to move the `Settings` numbers and the
   availability detail into `supplement/` behind one-line pointers and trim
   from there; that recovers roughly 1,400 of the 4,458 characters, and the
   rest would have to come out of substance.
2. Rerun the tool so the `edit` pass executes for the first time (item 1
   unblocks it). Expect item 2 to fail again — see the note there.
3. Decide B4: whether the autism framing drops to a motivation paragraph, or
   stays with an argued justification for the general-stress corpora. Author
   call, no mechanical answer.
4. Propagate the new title to `README.md` and any submission metadata.
   `main.tex` and `CITATION.cff` are already updated. Decide what to do with
   the stale `paper/paper_5page.pdf`, which is tracked in git and superseded by
   `paper_conference.pdf`.
5. Nothing else is outstanding from the tool run. Everything remaining is
   Part B repositioning the author has consciously declined: the cusp model
   still leads the title (B1) and the autism framing is kept with an argued
   justification rather than dropped (B4).

```bash
cd "C:\Users\Neil Thomas Mathew\Desktop\Neil\research\final\paper" && research-better run main.tex
```

---
---

# Part B — Substantive reviewer critique

Source: external critique supplied by the author, recorded verbatim in substance.
Overall rating given: **5.5 / 10**.

Headline judgement: *"a careful, self-critical negative methodological paper dressed in
the language of a positive modelling contribution."* The mathematics is standard and
correctly deployed; the simulation and surrogate work are competent; the honesty about
non-identifiability and failed predictions is a genuine virtue. But the empirical claim
about overload geometry is unsupported, the target clinical population is absent, and
the interesting positive statements (hysteresis scaling, EWS exponents, debt-driven
bistability) cannot be recovered at the data lengths available.

Suggested repositioning: this would be stronger as a short methods note titled something
like **"Identifiability limits of cusp models on wearable EDA"**, without the autism
framing and without the "ground-truth failure" headline. As currently positioned it
promises more generative insight into overload than it delivers.

## B1. Non-identifiability is not a side note — it IS the result

**Status:** PARTIAL. Reframed in the text, not in the title.

The abstract now says the identifiability bound "rather than the model, is the
paper's primary result", and the discussion opens with the B7 residue sentence
and calls the contribution negative and methodological. B3 has since narrowed
the early-warning clause of the title. What remains undone is the full
repositioning the critique suggests: the cusp model still leads the title and
the autism framing is intact (B4). Those are author decisions.

Only `lambda` (relaxation) and `sigma` are recovered in both rank and value at realistic
lengths (n ~ 200–1000 windows). The geometric parameters that actually define the cusp
(`a = theta_2/theta_1`, etc.) are ratios with an unbounded denominator. Rank correlation
for the splitting factor reaches ~0.88 at n=1000, but Pearson r stays near 0.10 because
estimates blow up when `lambda_hat` is small. Real-data fits have median
`lambda_hat ~ 0.0059`, producing absurd recovered `alpha_0_hat ~ 12` — attractors near
+/-2 on unit-variance data.

The paper's own conclusion ("length buys a defensible ranking... never a reportable
value") is honest and correct. But it means the central modelling claim is **untestable
in the data regime the paper studies**, and any subsequent cusp analysis of wearable
physiology inherits the same ratio pathology.

That is a useful negative methodological finding — not a positive model of overload. The
paper should be positioned as the former.

## B2. The one identifiable prediction fails on the data

**Status:** DONE.

The first discussion paragraph now states the two losses jointly and says they
differ in kind: the geometry is unrecoverable at these lengths, and the one
recoverable component is unsupported above a calibrated null and beaten by its
own removal on held-out density. It also says explicitly that bimodality plus a
likelihood-ratio excess without the cubic is structure of some other kind and is
not read as a fold, which is the "does not rescue the model" point.

- `theta_1 = lambda` (the cubic restoring term), the only trustworthy parameter, is
  significant in **2.7%** of 147 recordings against a calibrated 5% null — ~1.5% when
  person-weighted.
- The full model **loses to its nested monostable (no-cubic) special case** on held-out
  predictive density.
- Prospective onset prediction is **pure chance** (AUC 0.46–0.50).

Reported correctly as a bound excluding strong/moderate cusp dynamics. But combined with
B1, the paper demonstrates that the data contain neither a recoverable cusp geometry nor
evidence for the restoring cubic term that would produce one. "Structure without fold
structure" (bimodality and likelihood-ratio excess without the cubic) is interesting but
does not rescue the model.

## B3. The EWS failure is real but oversold in the title

**Status:** DONE, both in the text and in the title.

The results section now states the claim at its own size: fixed-width rolling
variance and lag-1 AC1 with and without Gaussian detrending; a failure of those
estimators rather than of early-warning theory, since the theoretical exponent
recovers on the same data; and a sharpening of the existing scepticism already
cited rather than a new discovery. The duplicate sentence in Limitations was
cut and now cross-references Sec. V.

Title changed on the author's decision to **"...a Ground-Truth Failure of
Rolling-Window Early-Warning Estimators in Wearable Physiology"**. The
`preferred-citation` title in `CITATION.cff` was updated to match. The README
and any submission metadata still carry the old string.

On genuine cusp simulations the theoretical curvature recovers ~+0.565 (close to +0.5).
Fixed-window variance and -log AC1 systematically invert sign at short windows and
collapse to zero at longer ones. Withdrawing the P2 test is the right call.

But this is a solid **local falsification of the specific estimators the author planned
to use**, not a devastating new discovery about the early-warning literature — and it
aligns with known critiques already cited (Ditlevsen & Johnsen, Boettiger & Hastings).
It is also partly expected once you remember that critical slowing produces a diverging
correlation time while the window stays fixed.

**Action:** "a Ground-Truth Failure of Early-Warning Indicators" in the title oversells
this. Narrow the claim to the estimators actually tested.

## B4. Motivation vs. data mismatch

**Status:** DONE, by the second of the two routes the finding offers.

The author's B3 decision was to narrow rather than reposition, so the autism
framing stays and the justification is now argued explicitly in the
Introduction: general stress corpora cannot settle whether autistic overload is
a cusp, but they carry the same sensor, sampling rate and recording lengths the
intended study would, so the identifiability bound and the estimator failure
transfer to it directly. The paragraph closes by saying no claim about the
population transfers and none is made.

If you would rather take the other route --- drop the framing and retitle ---
this paragraph is the thing to delete, and it is about 6 lines.

The introduction and abstract lean hard on autistic sensory/cognitive overload ("arrives
suddenly, and it clears slowly"). **No autistic participants are analysed.** The paper
states this explicitly and pre-registers a future EMA + continuous-wrist study, which is
better than the common practice of title-baiting a clinical population while analysing
convenience samples.

It nonetheless leaves the paper as a methodological exercise on general stress corpora
(WESAD, exam stress, nurse shifts) that happens to be motivated by autism. "The target
population is autistic adults" is aspirational, not empirical.

**Action:** either drop the autism framing to a motivation paragraph and retitle, or
justify why the general-stress corpora are informative about the target population.

## B5. Scope, length, and residual arbitrariness

**Status:** DONE, to the extent five pages allow.

Windowing and replication are stated (3b), the ablation question is answered
(4a), and Limitations now names the three knobs that were *not* swept --- the
softplus debt form, the driver set (S, T, U) and the choice to treat the Euler
map as the model rather than an approximation --- and says each could move the
fits. Sensor assignment already had its own justification in Sec. III-B.

The negative control firing more than the primary signal is already addressed
head-on, not in a footnote: Results §D reports the elevated A and C rates,
lists three explanations that were tested and failed, and concludes that the
parsimonious reading is artefact and that this is why the conclusion rests on
B. No change was needed there.

- **Sensor assignment.** Tonic EDA as the primary load coordinate (chosen on high lag-1
  AC) with the cardiac index as negative control is justified but still a choice.
- **Under-analysed knobs:** windowing; softplus debt accumulation; the precise driver set
  (S, T, U); and the decision to treat the Euler map as the exact model rather than an
  approximation. All matter, all receive limited sensitivity analysis.
- **Power** is high only for strong/moderate dynamics. Weak cusp dynamics remain
  compatible with the data.
- **Robustness is mixed:** the negative control fires more than the primary signal under
  some surrogates. This needs addressing head-on, not a footnote.
- The AI-assistance disclosure is welcome and appropriate — keep it.

Note this overlaps directly with tool item 3b (hyperparameters never stated) and item 4a
(no ablation). Fixing 3b/4a properly addresses part of B5.

## B6. What the critique says works — preserve these

- Geometric derivation of states and the 5x5 kernel from Kramers rates is **elegant**,
  and avoids the circularity of labelling experimental blocks then counting transitions.
- Surrogate calibration (random-walk + IAAFT) correctly diagnoses the nominal t-test's
  catastrophic size inflation (~42% rejection under the null) on near-unit-root tonic
  EDA.
- The paper does not hide its negative results or the identifiability bound. *"That is
  rarer than it should be."*
- Pre-registration language for the intended autistic validation study is concrete.
- The estimation approach (Euler discretisation -> linear-in-parameters drift -> profiled
  OLS over the slow rate epsilon) is exact under the model assumptions and avoids the
  usual numerical headaches of cusp fitting.
- The Monte Carlo identifiability study and the ground-truth EWS stress-test are the
  **strongest parts of the paper**.

## B7. The durable residue (what to build the paper around)

**Status:** DONE. This sentence, lightly rephrased, now opens the second
paragraph of Discussion and Conclusion.

The critique names the finding worth keeping:

> Cusp geometry on short wearable series is largely an artefact of ratios involving a
> poorly constrained relaxation rate, and naive rolling EWS indicators can invert even
> when a fold is present.

If the paper is rebuilt around that sentence rather than around the cusp model as a
positive contribution, B1–B4 largely dissolve.
