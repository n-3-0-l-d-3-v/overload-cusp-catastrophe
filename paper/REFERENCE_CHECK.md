# Reference verification

Every entry in `refs.bib` that carries a DOI has been checked against the
metadata the publisher deposited, not against a search engine. Crossref is the
authority for articles and conference papers; DataCite for datasets, which are
registered there instead and return a Crossref 404 that means nothing.

Reproduce with:

```bash
python code/experiments/check_citations.py --crossref
```

**Status as of 2026-08-07:** 46 entries — 42 verified clean, 4 without a DOI,
0 disagreements.

---

## Why this file exists

Round 4 of the self-review spot-checked nine entries and found six wrong. One
DOI resolved to an entirely different paper. At that base rate the remaining
entries could not be assumed clean, so the check was automated and run over all
46. It found two further defects that four rounds of human reading had missed.

Citation errors are not cosmetic. A wrong DOI in a submitted manuscript is the
kind of thing that gets a paper desk-rejected, and if it survives review it
becomes a correction notice.

---

## Corrections made in this pass (2026-08-07)

### `wichers2021` → `helmich2021` — wrong first author, wrong pages

Two independent errors in one entry.

| Field | Was | Should be |
|---|---|---|
| First author | Wichers, Marieke | **Helmich, Marieke A.** (Wichers is fourth) |
| Pages | 105–110 | **51–58** |

Same class of defect as the six found in Round 4: an author-year key that looks
plausible, attached to metadata nobody re-read. Key renamed to match the actual
first author so the error cannot silently return.

### Three entries dated to online-first rather than the issue cited

`kiep2023` → **`kiep2025`**, `auge2024` → **`auge2025`**,
`chen2024ema` → **`chen2025ema`**.

Each carried the volume, issue and page numbers of the print issue while giving
the year the article first appeared online. That is internally inconsistent: a
reader following *J. Autism Dev. Disord.* **55**(6), 2075–2084 arrives at a 2025
issue, not a 2023 one.

| Key | Online-first | Print issue | Year now cited |
|---|---|---|---|
| `kiep2025` | 2023-05-12 | 55(6), Jun 2025 | 2025 |
| `auge2025` | 2024-05-18 | 55(8), Aug 2025 | 2025 |
| `chen2025ema` | 2024-12-18 | 29(6), Jun 2025 | 2025 |

Round 4 moved these the wrong way, changing correct 2025 dates to the
online-first years while keeping the print volume and pages. This pass reverses
that and records why, so a future round does not flip them a third time.
`chen2025ema` was also missing its issue number.

---

## Two false-positive classes the checker used to produce

Both were bugs in the checking script, not in the bibliography. Recording them
because a checker that cries wolf gets ignored, which is worse than no checker.

**Online-first dates.** Crossref's `issued` field is the earliest registered
date, which for any journal that posts ahead of print is not the year of the
issue being cited. The script now prefers `published-print` and falls back to
`issued`. This removed four spurious reports (`demetriou2018`, `leemput2014`,
`maclennan2022`, `nahumshani2018`), all of which were correct as written.

**Dataset DOIs.** PhysioNet registers with DataCite, so `amin2022exam`
(10.13026/kvkb-aj90) returned a Crossref 404 that read as "the DOI is wrong".
It is not; the record is correct in every field. The script now falls back to
the DataCite API before reporting a DOI as bad.

---

## Entries without a DOI

Four, all pre-dating routine DOI assignment. Each was confirmed against the
publisher's own catalogue record by hand; none is machine-checkable and none
should be flagged in future runs.

| Key | Work |
|---|---|
| `thom1975` | Thom, *Structural Stability and Morphogenesis*, W. A. Benjamin, 1975 |
| `zeeman1976` | Zeeman, "Catastrophe theory", *Sci. Am.* 234(4), 65–83, 1976 |
| `gilmore1981` | Gilmore, *Catastrophe Theory for Scientists and Engineers*, Wiley, 1981 |
| `gardiner2009` | Gardiner, *Stochastic Methods*, 4th ed., Springer, 2009 |

---

## Consistency

`check_citations.py` also confirms that every key cited in `main.tex` exists in
`refs.bib`, and reports entries that are never cited.

- Cited keys in the conference paper: **16**. All resolve. No `[?]` markers.
- Uncited entries: **30**. These belong to `main_full_journal.tex`, the
  long-form draft kept for the journal version. They are retained deliberately;
  a single shared bibliography is easier to keep correct than two.

---

## Claim-level audit, 2026-08-12

The checks above verify that each entry *resolves* — right title, authors, year,
DOI. That is a different question from whether the sentence citing it says what
the source says. Every cited claim in `main.tex` was checked against its source
on 2026-08-12, prompted by `research-better`'s `trace` pass flagging three of
them. **Four sentences were citing claims their sources do not make.** All four
are fixed; the corrections are in the git history.

| Key | What the sentence claimed | What the source says | Outcome |
|---|---|---|---|
| `maclennan2022` | "functional breakdown under combined sensory and cognitive demand ... arrives suddenly, clears slowly" | A thematic study of sensory *reactivity* differences across modalities. Neither the combined sensory–cognitive claim nor the temporal shape appears | Rewritten. The temporal shape is now stated as the premise the paper formalises, not as an inherited finding |
| `demetriou2018` | adult cohort studies couple sensory atypicality to executive difficulty "with large effect sizes" | A meta-analysis of executive function, not of sensory–executive coupling, reporting *smaller* effect sizes in adults | Rewritten. `kiep2025` now carries the coupling; `demetriou2018` carries the meta-analytic finding, stated correctly |
| `hosseini2022nurse` | "15 nurses across roughly 1250 h of hospital shifts" | Describes the dataset and setting; states neither figure. Both come from our own audit of the released files (`data/DATASETS.md`) | Rewritten. Counts now attributed to our screening |
| `cano2024`, `chen2025ema` | "no public wearable dataset of that group exists at the temporal density the model needs" | Reviews of wearable design and of EMA feasibility in autism. Both survey what has been collected; neither asserts the absence | Rewritten. The survey is attributed to them, the absence to us |
| `ditlevsen2010`, `boettiger2012` | early-warning indicators arise "spuriously on almost any autocorrelated series" | Ditlevsen: the shifts were noise-induced rather than bifurcations, with limited predictability. Boettiger: quantifies a reliability/sensitivity trade-off, notes error rates are hardly ever characterised | Rewritten to say those two things |

Verified as accurate, no change needed:

- `chrysaitis2023` — "empirical support a ten-year review found mixed and
  methodologically inconsistent". The abstract says results are "highly mixed"
  and reports "low statistical power and often inconsistent approaches".
  Confirmed against PubMed and the Edinburgh Research Explorer record; Crossref
  deposits no abstract for this entry, which is why the automated pass could
  not check it.
- `adamou2026` — "avowedly theoretical, collecting no data". The abstract
  describes developing interpretable mathematical models grounded in
  neuropsychological theory, with no data collection.
- `scheffer2009`, `dakos2012` — cited as the source of the rolling-window
  indicators. These are the canonical methods papers for exactly that.
- `kramers1940`, `schreiber1996`, `schmidt2018wesad`, `amin2022exam`,
  `kiep2025` — cited for a formula, a method, and dataset identities
  respectively; each matches its source.

**Status: all 18 cited claims in `main.tex` verified against source.**
