<!-- research-better 0.3.0 | source: main.tex | hash: 09a97776af96eaf6 | generated: 2026-08-12T01:19:12+00:00 -->

# Passages that may read as machine-written

Causes, not a score. Nothing here was checked against a detection service,
and every fix below is a change that improves the paper on its own terms.
If a change would only make the text look less machine-written, it is not
offered. See docs/INTEGRITY.md.

**Flagged:** 4. **Looked at and left alone:** 4.

## Flagged

### Introduction, paragraph 1

> Autistic adults report sensory reactivity differences across vision, sound and touch, and describe the difficulty of tolerating and controlling them \cite{macl…

*fix: unsupported claim + uniform rhythm*

- **unsupported claim.** cited to [demetriou2018], and the full text that was read does not carry it
  - Why this reads as generated: A sentence whose own cited source does not support it is the strongest content-level signal there is. Text that was generated attaches a citation because a citation belongs in that position, not because anybody read the source.
  - What to do: Read the quoted passage in grounding.json. Cite the work that establishes this, weaken the sentence to what the source actually says, or cut it.
- **uniform rhythm.** 5 sentences varying by 5.0 words, against 11.0 across this paper
  - Why this reads as generated: Even sentence length is a texture a reader notices without being able to name it. It is also what a genuinely formulaic passage looks like, so it is never a reason to change anything on its own.
  - What to do: Nothing on its own. If the causes above are fixed the rhythm changes with them. Do not lengthen a sentence to break a pattern.

Flagged on the content signals above. The texture, if any is listed, is recorded because it is there and is not a reason to change anything.

`par-6a91d46a54e0`

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

- **voice hedging.** 0.44 per hundred words here against 0.10 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-9fbf4a74b17d`

### Sensor assignment and a negative control (whole section)

> \subsection{Sensor assignment and a negative control}

*review: voice passive ratio*

- **voice passive ratio.** 0.33 of sentences here against 0.15 for the paper, which is further than any other section sits from it
  - Why this reads as generated: A section whose texture departs this far from the rest of the paper is what a reader notices as a change of voice. It is measured against this paper only, so it says nothing about how anybody else writes.
  - What to do: Read it beside a section you know you wrote. If it is yours, leave it. If it came from somewhere else, that is what to resolve, and no wording change resolves it.

A voice that departs from the rest of the paper is copied, drafted elsewhere, or written by a coauthor. Which one it is, is a question for you: the tool reports the inconsistency and does not guess.

`sec-819ac3e391e8`

## Looked at, left alone

These tripped a texture signal and nothing else. A detector might dislike
them. That is not a reason to change writing that is doing its job.

### What This Data Can Identify, paragraph 2

- 4 sentences varying by 5.3 words, against 11.0 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### What This Data Can Identify, paragraph 3

- 5 sentences varying by 3.3 words, against 11.0 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### The early-warning estimator fails on ground truth, paragraph 3

- 5 sentences varying by 5.4 words, against 11.0 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

### Structure without fold structure, paragraph 3

- 5 sentences varying by 3.6 words, against 11.0 across this paper

Likely a false positive, and worth leaving. Only texture fired here: rhythm and shape, which a careful writer can have naturally and which detectors get wrong most often on writers whose first language is not English. Nothing here is a reason to change a sentence.

## Not checked

- Nothing was skipped.
