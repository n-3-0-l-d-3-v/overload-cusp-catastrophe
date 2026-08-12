<!-- research-better 0.3.0 | source: main.tex | hash: 6bb4c482d26838d1 | generated: 2026-08-10T23:54:08+00:00 -->

# Passages that may read as machine-written

Causes, not a score. Nothing here was checked against a detection service,
and every fix below is a change that improves the paper on its own terms.
If a change would only make the text look less machine-written, it is not
offered. See docs/INTEGRITY.md.

**Flagged:** 4. **Looked at and left alone:** 3.

## Flagged

### Introduction, paragraph 1

> Autistic adults describe functional breakdown under combined sensory and cognitive demand in consistent terms: it arrives suddenly, and it clears slowly \cite{…

*fix: unsupported claim + unsupported claim*

- **unsupported claim.** cited to [maclennan2022], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.
- **unsupported claim.** cited to [demetriou2018], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.

Flagged on the content signals above. The texture, if any is listed, is recorded because it is there and is not a reason to change anything.

`par-045ea8bbc127`

### Corpora, paragraph 1

> Three open corpora, each from its primary repository rather than a mirror, span a gradient of experimental control: WESAD, 15 subjects in a laboratory protocol…

*fix: unsupported claim*

- **unsupported claim.** cited to [hosseini2022nurse], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.

Flagged on the content signals above. The texture, if any is listed, is recorded because it is there and is not a reason to change anything.

`par-bdac38a22a03`

### Introduction (whole section)

> \section{Introduction}

*review: voice hedging*

- **voice hedging.** 0.53 per hundred words here against 0.10 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-9fbf4a74b17d`

### Sensor assignment and a negative control (whole section)

> \subsection{Sensor assignment and a negative control}

*review: voice passive ratio*

- **voice passive ratio.** 0.38 of sentences here against 0.18 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-819ac3e391e8`

## Looked at, left alone

These tripped a texture signal and nothing else. A detector might dislike
them. That is not a reason to change writing that is doing its job.

### What This Data Can Identify, paragraph 2

- 4 sentences varying by 5.3 words, against 11.4 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### What This Data Can Identify, paragraph 3

- 5 sentences varying by 3.3 words, against 11.4 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### The early-warning estimator fails on ground truth, paragraph 3

- 5 sentences varying by 5.2 words, against 11.4 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

## Not checked

- Nothing was skipped.
