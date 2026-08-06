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
