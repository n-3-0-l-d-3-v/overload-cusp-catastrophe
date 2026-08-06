# Overload as a Cusp Catastrophe

Identifiability limits, and a ground-truth failure of early-warning indicators
in wearable physiology.

**Neil Thomas Mathew** — [ORCID 0009-0001-8802-7376](https://orcid.org/0009-0001-8802-7376)
Department of Computer Applications, CHRIST (Deemed to be University), Bengaluru

Complete research artefact: derivation, implementation, Monte Carlo validation,
figures, manuscript, and an unedited record of everything that broke along the
way.

---

## What this is

Sensory and executive overload is usually modelled by labelling states and
counting the transitions between them. Models built that way fit any data and
forbid nothing, so no observation can contradict them.

This work derives overload from the geometry of a **cusp catastrophe** instead.
A latent load coordinate relaxes in a quartic potential
`V(x; a, b) = ¼x⁴ − ½ax² − bx`, where the normal factor `b` follows momentary
demand and the splitting factor `a` follows accumulated recovery debt. The claim
that makes it science rather than metaphor: regulatory capacity does not *add*
to load, it changes the *shape of the landscape*. Below a critical `a` the load
tracks demand and returns. Above it a second attractor exists, and with it a
fold, a hysteresis loop, and critical slowing down.

Because the geometry is closed-form, it fixes numbers in advance:

| Prediction | Statement |
|---|---|
| P1 hysteresis width | `Δb = (4/3√3)·a^{3/2}` — the exponent is 3/2, not merely positive |
| P2 early-warning exponents | `Var ∝ μ^{−1/2}`, `−log AC1 ∝ μ^{+1/2}` in distance `μ` to the fold |
| P3–P5 | dwell-time over-dispersion, re-entry hazard, recovery scaling with debt gain |

Functional states stop being labels and become regions of the `(a, b)` plane;
the 5×5 transition kernel follows from Kramers escape rates, so nine
interpretable parameters replace twenty counted frequencies.

## What we found

Three results. Two are about method, and those are the durable ones.

**1. The geometry is not identifiable at wearable series lengths.** Simulating
from the model with known parameters and refitting, the relaxation rate and the
diffusion coefficient come back cleanly (r = 0.91, 0.95 at n = 200). The
parameters carrying the actual geometry do not: the splitting factor sits at
r = 0.06, the debt gain at −0.07. The mechanism is arithmetic, not statistical —
recovered geometry is the ratio `a = θ₂/θ₁`, so it inflates without bound as
`θ₁ → 0`. In the real corpora the median `λ̂` is 0.0059. **Any** cusp analysis of
wearable data inherits this, which is why the result bounds other people's work
and not only ours.

**2. The standard early-warning estimator returns the wrong sign on ground
truth.** On data simulated from a model that provably contains a fold, the
closed-form theory recovers +0.565 against a predicted +0.5. The rolling-window
autocorrelation and variance indicators the literature runs on return negative
slopes where +0.5 is predicted and positive where −0.5 is. Every window length,
every detrending choice, series up to n = 20,000. The relaxation time diverges
at the fold, so a fixed-width window saturates exactly where the signal lives.
We withdrew our own P2 test rather than report it.

**3. The one identifiable prediction is not supported.** Across 147 recordings
from 40 people, the restoring cubic term is significant in 2.7% of units against
a nominal 5%; 1.5% weighting one vote per person. The full model loses to its
own monostable special case on held-out prediction (win rate 33.8%,
p = 8 × 10⁻⁵). Onset prediction is at chance. Measured power bounds this to
excluding strong and moderate dynamics — **not** a faint fold.

> The target population is autistic adults. **No autistic participants are
> analysed here**, because no public wearable corpus of that group exists at the
> temporal density this model needs. The paper says so in the abstract and does
> not name a population it did not measure. A pre-registered validation is
> specified.

---

## Layout

```
.
├── paper/
│   ├── main.tex                 IEEE two-column conference manuscript
│   ├── main_full_journal.tex    long-form draft for the journal version
│   ├── refs.bib                 46 entries, all DOIs verified
│   ├── REFERENCE_CHECK.md       what was wrong and how it was found
│   ├── paper_5page.pdf          compiled output
│   └── tables/                  auto-generated LaTeX tables
├── code/
│   ├── chm/
│   │   ├── potential.py         closed-form cusp geometry
│   │   ├── model.py             parameters, driver links, simulator
│   │   ├── states.py            five derived states, Kramers kernel
│   │   ├── estimate.py          profiled-LS estimator, nulls, inference
│   │   ├── ews.py               early-warning indicators, scaling-law fits
│   │   ├── baselines.py         five competing models
│   │   ├── signals.py           physiological feature extraction
│   │   └── datasets.py          loaders for the three corpora
│   ├── tests/                   32 tests: analytic claims + recovery
│   └── experiments/
│       ├── reproduce.py         run everything, report what passed
│       ├── mega_run.py          the Monte Carlo suite (chunked, resumable)
│       ├── run_all.py           corpus analyses E1–E10
│       ├── fetch_data.py        download from primary repositories
│       ├── compile_paper.py     compile + assert layout and bibliography
│       ├── check_citations.py   verify every DOI against Crossref/DataCite
│       └── make_figures_v2.py   figures, with width assertions
├── data/DATASETS.md             provenance, licences, the Kaggle question
├── results/                     every CSV the paper cites
├── figures/                     600 dpi PDF + PNG
├── supplement/SUPPLEMENT.md     long-form material for the journal version
├── review/                      four rounds of adversarial self-review
└── progress/PROGRESS_LOG.md     what was done, what broke, what changed
```

## Reproducing

```bash
pip install -r requirements.txt
```

Everything that needs no data and no network — tests, citation consistency, and
a manuscript compile that asserts 5 pages, zero overfull boxes and no empty
bibliography entries:

```bash
python code/experiments/reproduce.py --stage check
```

Add the Monte Carlo suite at 2% replication (minutes, verifies the pipeline but
the numbers are not publishable):

```bash
python code/experiments/reproduce.py --stage fast
```

Full replication — roughly seven hours on six cores, and these are the numbers
in the paper:

```bash
python code/experiments/reproduce.py --stage all
```

The suite is chunked and checkpointed. If it is interrupted, rerun with
`--resume` and it continues from the last completed chunk:

```bash
python code/experiments/mega_run.py --block all --resume
```

### The corpus analyses

These need the three datasets on disk. They total about 20 GB and are not
redistributed here.

```bash
python code/experiments/fetch_data.py
python code/experiments/run_all.py --config B
```

Configuration B (tonic EDA) is primary, C (skin temperature) is a robustness
check, and **A (a cardiac index) is a negative control** — a coordinate
independently shown to be noise-dominated, where a working pipeline should find
nothing. It does find something, which is the negative control doing its job and
the reason the conclusion rests on B alone.

## Data

Three open corpora, each downloaded from its **primary repository**, never a
mirror. Exact URLs, download dates and byte counts are in
[`data/DATASETS.md`](data/DATASETS.md).

| Corpus | Sessions | People | Setting |
|---|---|---|---|
| WESAD ([UCI 465](https://archive.ics.uci.edu/dataset/465)) | 15 | 15 | controlled laboratory |
| Wearable Exam Stress ([PhysioNet](https://doi.org/10.13026/kvkb-aj90)) | 30 | 10 | naturalistic cognitive load |
| Nurse Stress ([Sci. Data](https://doi.org/10.1038/s41597-022-01361-y)) | 102 | 15 | hospital shifts, ~1250 h |
| **Total after screening** | **147** | **40** | median 194 windows each |

An earlier draft sourced WESAD from a Kaggle mirror. That was fixed: a mirror
carries no version, licence or checksum guarantee, and citing one tells a
reviewer you did not go to the source. Nothing here uses a Kaggle re-upload.

## The working record

[`review/`](review/) holds four rounds of adversarial self-review, kept
unedited, including the rounds that found real damage: a baseline silently
returning nothing behind a bare `except: pass`, a survivorship bias in the model
comparison, a sampling bug drawing 112 "nurse sessions" from 5 nurses, and six
of nine spot-checked references wrong. Round 3 published a hypothesis for the
configuration-C non-replication; Round 4 refuted it with three experiments. That
is in the record too.

[`progress/PROGRESS_LOG.md`](progress/PROGRESS_LOG.md) tracks what changed and
why, including three claims that survived one round of checking and failed the
next.

## Status

Submitted work in progress. The conference manuscript is complete; the journal
version awaits wearable data from the population the model is about.

## Licence

MIT for the code, manuscript and figures — see [LICENSE](LICENSE). The corpora
are **not** covered and carry their own terms; obtain each from its primary
repository.

## Citing

See [CITATION.cff](CITATION.cff).
