<!-- research-better 0.3.0 | source: main.tex | hash: 88df1cc0588acbd0 | generated: 2026-08-12T10:33:21+00:00 -->

# Passages that may read as machine-written

Causes, not a score. Nothing here was checked against a detection service,
and every fix below is a change that improves the paper on its own terms.
If a change would only make the text look less machine-written, it is not
offered. See docs/INTEGRITY.md.

**Flagged:** 4. **Looked at and left alone:** 3.

## Flagged

### Introduction, paragraph 1

> Catastrophe models are an attractive way to formalise overload. A latent load coordinate relaxing in a quartic potential turns functional states into metastabl…

*fix: unsupported claim + unsupported claim*

- **unsupported claim.** cited to [maclennan2022], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.
- **unsupported claim.** cited to [demetriou2018], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.

Flagged on the content signals above. The texture, if any is listed, is recorded because it is there and is not a reason to change anything.

`par-c609d5ecb7f4`

### Corpora, paragraph 1

> Three open corpora, taken from their primary repositories rather than mirrors, span a gradient of experimental control: WESAD, a laboratory stress and affect p…

*fix: unsupported claim*

- **unsupported claim.** cited to [hosseini2022nurse], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.

Flagged on the content signals above. The texture, if any is listed, is recorded because it is there and is not a reason to change anything.

`par-270c7c876f61`

### Introduction (whole section)

> \section{Introduction}

*review: voice hedging*

- **voice hedging.** 0.44 per hundred words here against 0.07 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-9fbf4a74b17d`

### Sensor assignment and a negative control (whole section)

> \subsection{Sensor assignment and a negative control}

*review: voice passive ratio*

- **voice passive ratio.** 0.33 of sentences here against 0.14 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-819ac3e391e8`

## Looked at, left alone

These tripped a texture signal and nothing else. A detector might dislike
them. That is not a reason to change writing that is doing its job.

### What This Data Can Identify, paragraph 2

- 4 sentences varying by 5.3 words, against 11.6 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### What This Data Can Identify, paragraph 3

- 5 sentences varying by 3.3 words, against 11.6 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### The early-warning estimator fails on ground truth, paragraph 3

- 5 sentences varying by 5.4 words, against 11.6 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

## Not checked

- Nothing was skipped.
