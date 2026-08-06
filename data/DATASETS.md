# Datasets: provenance, credibility and licensing

This file exists because the honest answer to "is the data credible?" is more
specific than yes or no, and a reviewer will ask.

---

## The Kaggle question, answered directly

The earlier draft of this work sourced WESAD from Kaggle. **The concern about
Kaggle is half right, and it is worth being precise about which half.**

*Not a problem:* WESAD itself. It is a peer-reviewed dataset published at ACM
ICMI 2018, deposited in the UCI Machine Learning Repository (ID 465), and used
in hundreds of downstream papers. It is one of the most standard benchmarks in
wearable affect computing. Nothing about the data is questionable.

*A real problem:* citing a Kaggle re-upload as the source. A Kaggle mirror is
an uncontrolled copy — no version guarantee, no licence guarantee, no checksum,
and it can be edited or deleted by its uploader at any time. A methods section
that says "downloaded from Kaggle" tells a reviewer the authors did not go to
the primary source, which invites doubt about everything else in the pipeline.

*What was done here:* every corpus below was downloaded from its primary
repository, programmatically, with the exact URL recorded. No Kaggle mirrors
are used anywhere in this project.

The second, and much more serious, criticism of the earlier draft was not about
Kaggle at all: it was that a paper claiming to model **autistic adults**
contained **zero autistic participants**. That is addressed in the paper's
framing rather than by swapping datasets — see "The autism question" below.

---

## D1 — WESAD (Wearable Stress and Affect Detection)

| | |
|---|---|
| Primary citation | P. Schmidt, A. Reiss, R. Duerichen, C. Marberger, K. Van Laerhoven, "Introducing WESAD, a multimodal dataset for wearable stress and affect detection," *Proc. 20th ACM Int. Conf. Multimodal Interaction (ICMI)*, 2018, pp. 400–408. doi:10.1145/3242969.3242985 |
| Repository | UCI Machine Learning Repository, ID 465 |
| Source used | `https://uni-siegen.sciebo.de/s/HGdUkoNlW1Ub0Gx/download` (the authors' own institutional mirror, linked from the UCI record) |
| Downloaded | 2026-07-22, 2 249 444 501 bytes, HTTP 200 |
| Participants | 15 (S2–S11, S13–S17; S1 and S12 excluded by the dataset authors) |
| Signals used | Wrist Empatica E4: EDA 4 Hz, BVP 64 Hz, TEMP 4 Hz, ACC 32 Hz |
| Protocol labels | 1 baseline, 2 stress (TSST), 3 amusement, 4 meditation, at 700 Hz |
| Windows/subject | ≈ 200 at the 30 s analysis window |
| Role | Controlled benchmark, and a **negative control for the early-warning analysis** |

**Why it is a negative control for early warnings, not a test of them.**
Critical-slowing-down theory describes a system fluctuating freely near a
tipping point it approaches on its own. In WESAD the "transition" is an
experimenter starting the Trier Social Stress Test at a scheduled time. The
system does not drift towards its own threshold; it is pushed across one. This
is a genuine methodological mismatch, and it was the sharpest criticism of the
earlier draft. Rather than ignore it, we use WESAD for what it is good for
(benchmarking, state validation against known conditions) and test the
early-warning predictions on D2 and D3.

---

## D2 — Wearable Exam Stress

| | |
|---|---|
| Primary citation | M. R. Amin, D. Wickramasuriya, R. T. Faghih, "A wearable exam stress dataset for predicting cognitive performance in real-world settings" (v1.0.0), *PhysioNet*, 2022. doi:10.13026/kvkb-aj90 |
| Repository | PhysioNet |
| Source used | `https://physionet.org/content/wearable-exam-stress/get-zip/1.0.0/` |
| Downloaded | 2026-07-22, 85 968 624 bytes, HTTP 200 |
| Participants | 10 students × 3 exams (2 midterms, 1 final) = 30 sessions |
| Signals used | Empatica E4: EDA, BVP, TEMP, ACC |
| Licence | Open Data Commons Attribution License v1.0 |
| Role | Naturalistic cognitive load, freely fluctuating |

Exams are self-paced: load rises and falls under the participant's own
regulation, which is the condition early-warning theory actually assumes.

---

## D3 — Nurse Stress in a Hospital

| | |
|---|---|
| Primary citation | S. Hosseini *et al.*, "A multimodal sensor dataset for continuous stress detection of nurses in a hospital," *Scientific Data*, vol. 9, art. 255, 2022. doi:10.1038/s41597-022-01361-y |
| Repository | Dryad, doi:10.5061/dryad.5hqbzkh6f (Zenodo mirror 5514277, deposited by the same authors) |
| Source used | `https://zenodo.org/api/records/5514277/files/Stress_dataset.zip/content` |
| Downloaded | 2026-07-22, 1 156 939 542 bytes, HTTP 200 |
| Participants | 15 nurses, ~1250 h across 609 recording sessions, during COVID-19 |
| Signals used | Empatica E4: EDA, BVP, TEMP, ACC |
| Labels | `SurveyResults.xlsx`, self-reported stress with timestamps |
| Role | Fully naturalistic occupational monitoring — the primary test bed |

**Note on the Dryad API.** `datadryad.org` returns HTTP 401 for the documented
`/api/v2/.../download` endpoint without a bearer token, and 403 to scripted
clients on the file-stream endpoint. The Zenodo deposit is the same files by
the same authors and is scriptable, so it was used instead. Both DOIs are cited.

---

## Why three corpora, and why in this order

They form a deliberate gradient in how much the environment is controlled:

| | control | who moves the load | early-warning theory applies? |
|---|---|---|---|
| D1 WESAD | full lab | experimenter | **no** — used as negative control |
| D2 Exam | structured, real | participant + task | partly |
| D3 Nurse | none | participant + world | **yes** |

A model of self-organised tipping should look *better* as you move down that
table. If it does not, the mechanism is not what we claim it is. Reporting all
three lets that comparison be made rather than asserted.

---

## The autism question

The target population of the underlying research programme is autistic adults.
None of these three corpora contains autistic participants, and **no claim is
made in the paper that they do.** The paper's empirical claims are about
sensory–autonomic load dynamics in the populations actually measured; autism
appears as the motivating application and in a preregistered protocol for
subsequent validation.

This is a deliberate downgrade from the earlier draft's framing, which titled
the work "…in Autistic Adults" while analysing 15 healthy adults doing a public
speaking task. That version would have been rejected on the first page.

Autistic-adult datasets that were checked and their status:

| Candidate | Status |
|---|---|
| Scheeren *et al.* 2025 EMA (87 autistic adults, 28 days) — osf.io/98jup | OSF entry holds **preregistration materials**, not raw data. Requires author contact. Not available today. |
| openESM database (Kirtley *et al.* 2025) | Index of open ESM datasets; no autism-specific dense physiological series found. |
| QU autism wearable (IEEE DataPort 10.21227/5b7r-8j60) | Autistic **children**, not adults; population mismatch. |
| ABIDE | Neuroimaging, not dense functional time series. |

Systematic reviews confirm there is currently **no public wearable
physiological dataset of autistic adults** with the density this model needs.
That absence is itself a finding worth stating in the paper, and it is what the
preregistered protocol is for.

---

## Reproducing the downloads

```bash
python code/experiments/fetch_data.py
```

Verifies sizes and SHA-256 where the repository publishes them, and refuses to
proceed on a mismatch.
