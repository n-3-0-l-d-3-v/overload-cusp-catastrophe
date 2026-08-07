# Pitch and briefing notes

For talking to evaluators, faculty and reviewers. Not part of the manuscript.

---

## The one-paragraph version

People describe overload — sensory, cognitive, the kind autistic adults report
under combined demand — the same way every time: it hits suddenly, and it clears
slowly. Existing models label those states and count how often people move
between them, which can never be wrong because it only re-describes the
experiment. I took a different route: I modelled overload as a ball rolling in a
landscape of valleys, where being run-down does not push the ball but *carves a
second valley* it can fall into and get stuck in. That shape is a known object in
mathematics, so it predicts exact numbers rather than vague directions — and
numbers can be refuted. Testing it on 147 real wearable recordings from 40 people
gave three results, and the two that matter are about method. First, the
parameters carrying the model's entire scientific content cannot be measured from
recordings this short, for an arithmetic reason that applies to *everyone* doing
this, not just me. Second, the early-warning toolkit the whole field relies on
returns answers of the **wrong sign** on data I built to contain a real tipping
point — so I withdrew my own test rather than publish it. The physiological claim
came back null, and I report it as a null with the power to say what that
excludes.

---

## Thirty-second version, if someone stops you in a corridor

> Everyone modelling overload as a tipping point is using measurement tools that
> return the wrong sign on data that provably contains a tipping point. I showed
> that on ground truth and explained the mechanism. And the cusp parameters people
> report from wearable data are ratios with a near-zero denominator — a "splitting
> factor of 12" from a short recording is arithmetic, not physiology. I give the
> length threshold that fixes it and a pre-registered study that would test the
> real question.

Lead with this. Do **not** lead with "I fitted a model and found nothing."
Same paper, completely different reception.

---

## What was actually done

| | |
|---|---|
| **Theory** | Overload derived from cusp-catastrophe geometry. Five functional states become regions of a plane rather than assigned labels. The 5×5 transition kernel follows from Kramers escape rates: nine interpretable parameters replacing twenty counted frequencies. |
| **Predictions fixed in advance** | Hysteresis width ∝ a^{3/2}. Near the fold, variance and log-autocorrelation scale as ∓1/2. Point hypotheses, not directions. |
| **Estimator** | Exact. Conditional on the slow variable the drift is linear, so fitting is profiled least squares over one scalar — no bounds, no starting values, no local optima. |
| **Data** | 147 recordings, 40 people, 3 open corpora, each pulled from its **primary repository** with URL, date and byte count recorded. Lab (WESAD), naturalistic (30 exam sessions), in-the-wild (~1250 h of nursing shifts). |
| **Simulation** | **67,000** primary simulated series across the completed Monte Carlo blocks — 12,000 for identifiability, 30,000 for test size, 15,000 for the early-warning validation, 10,000 for noise robustness. A further 3.5 million surrogate series were generated inside the calibrated tests. |
| **Verification** | 32 unit tests. 46 references checked against Crossref/DataCite — 42 clean, 0 disagreements. Five rounds of adversarial self-review, kept unedited including the rounds that found real damage. |
| **Reproducibility** | One command runs tests, citation checks and a layout-asserting compile. Public repo, MIT licensed, CI on every push. |

## The three results

1. **Identifiability.** At the recording lengths wearable corpora actually
   supply, only the relaxation rate and the noise level are recoverable. The
   parameters carrying the geometry are ratios with an unbounded denominator, so
   **length buys their ordering but never their value** — rank correlation for the
   splitting factor climbs to 0.88 at n=1000 while its linear correlation sits at
   0.10. This bounds every cusp study of such data, mine included.

2. **The early-warning estimator fails on ground truth.** On data simulated to
   contain a genuine fold, closed-form theory recovers +0.565 against a predicted
   +0.5. The rolling-window indicators the literature runs on invert the sign at
   short windows — 99% of replicates wrong in the worst case — and collapse to
   zero at long ones. Nowhere on a 90-configuration grid does an estimate come
   near the predicted magnitude. I withdrew my own test on the strength of this.

3. **The one testable prediction is not supported.** Significant in 2.7% of 147
   units against a nominal 5%; 1.5% weighting one vote per person. The full model
   loses to its own simpler special case on held-out prediction. Onset prediction
   is at chance. Measured power says this excludes strong and moderate dynamics —
   **not** a faint effect.

---

## Questions you will get, and what to say

**"Isn't this just a negative result?"**
> The physiology is a null. The two method results are positive, and they
> constrain other people's work, not only mine. Negative-methods findings like
> the identifiability bound get cited by everyone who tries the same thing next.

**"Why should I believe overload is a cusp if you found nothing?"**
> I'm not asking you to. I'm showing that one of five predictions was testable
> with this data, that it failed at the power I had, and that the other four
> aren't testable at these recording lengths. Weak dynamics remain open — my
> power for those is 0.24. It's a bound, not a refutation.

**"You have no autistic participants."**
> Correct, and the paper says so in the abstract, in the scope paragraph, in the
> limitations, and by not naming a population in the title. No public wearable
> corpus of autistic adults exists at the temporal density this model needs. The
> pre-registered validation study is specified in full.

**"The dataset is just WESAD from Kaggle."**
> No. Three corpora, not one, and every download came from the primary
> repository — WESAD from the authors' Siegen mirror linked off the UCI record,
> not a Kaggle re-upload. `data/DATASETS.md` records exact URLs, dates and byte
> counts. An earlier draft did use a Kaggle mirror; that was fixed and documented.

**"Did you use AI?"**
> Yes, and it's disclosed in the Acknowledgment per IEEE policy: AI assistance
> for code implementation, literature organisation and manuscript drafting. I
> verified every analysis, result and claim, and I'm responsible for the content.
> The git history shows the work commit by commit, and `review/` records five
> rounds where I found and fixed my own errors — including four claims that
> survived one round of checking and failed the next.

**"How do I know the numbers are right?"**
> Clone the repo and run `python code/experiments/reproduce.py --stage check`.
> It runs the tests, the citation consistency pass, and a compile that asserts
> page count, zero overfull boxes and no empty bibliography entries. No data or
> network required. `results/PROVENANCE.md` maps every number in the paper to the
> file it came from and its replication count.

---

## The honest weaknesses — say these before someone else does

Volunteering your own limitations is the single strongest credibility move
available to you. It is also the thing that separates this project from a
student report.

- No autistic participants. The motivating claim is untested, not refuted.
- Tonic EDA is a peripheral, artefact-prone proxy for a latent construct.
- Power for weak dynamics is 0.24 — a faint fold is not excluded.
- Two supporting numbers are thin: power at 100 replicates per cell, the AR(1)
  persistence check at 40 per point. Both are stated as such in the paper.
- The debt-accumulation parameters can't be recovered from passive data at *any*
  length tested, so the most clinically interesting part of the mechanism is
  currently unmeasurable. That is now written into the pre-registration.

## Where this is honestly positioned

Conference: strong, on the strength of the two method contributions.
Q1 journal: not yet. A null on a proxy signal in the wrong population will not
clear a Q1 rigour bar. The autistic-adult EMA data is the whole ballgame, and
chasing it is the highest-value thing left.
