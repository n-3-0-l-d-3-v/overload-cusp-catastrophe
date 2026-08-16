# Research progress brief

**Neil Thomas Mathew** — Department of Computer Applications, CHRIST (Deemed to be University)
Paper: *When Cusp Geometry Is an Artefact: Non-Identifiability and Sign-Inverting
Early-Warning Estimators in Wearable Physiology*
Repository: https://github.com/n-3-0-l-d-3-v/overload-cusp-catastrophe

---

## 1. Where this started, and what was wrong with it

The project began from an earlier draft of mine that an evaluation scored
**18/50**. Two of its objections were correct and I acted on both:

1. The paper was titled "…in Autistic Adults" and contained **zero autistic
   participants**. The data were healthy adults in a laboratory protocol.
2. Early-warning-signal theory requires a system fluctuating freely near a
   self-organised tipping point. In WESAD an experimenter switches the stress
   condition on at a scheduled time, so testing critical slowing down there is
   a methodological mismatch rather than a minor limitation.

While fixing those I found a third problem the critique had missed, and it was
the worst of the three: **the state assignment was circular.** The pipeline
mapped experimental condition labels directly onto model states and then
estimated a transition matrix between them. Such a matrix can only re-describe
the block design of the protocol. Nothing was being discovered.

Fixing that circularity is what forced the rebuild, and it is why the model
now derives states as geometric regions of a fitted potential rather than
assigning them from labels.

## 2. The finding that changed the paper's identity

Before testing the model on real recordings I ran it on **simulated data with
known ground truth** — a system built to contain a cusp, where the correct
answer is known by construction. The early-warning estimator returned an
exponent of the wrong sign.

That is not a negative result about physiology. It is a broken instrument, and
it would have invalidated the headline test I had planned. Investigated
properly across a 90-configuration grid at 500 replicates each:

| estimator | window | predicted | median | sign |
|---|---|---|---|---|
| theory, from true curvature | — | +0.50 | **+0.565** | correct |
| rolling $-\log$AC1 | 30 | +0.50 | −0.216 | wrong, 95% of replicates |
| rolling variance | 30 | −0.50 | +0.307 | wrong, 99% of replicates |
| rolling variance | 240 | −0.50 | −0.014 | collapses to zero |

The theory recovers; the estimators the applied literature runs do not. I
withdrew my own planned test rather than report it, and the mechanism is now
identified in the paper: the correlation time diverges at the fold while the
window stays fixed.

## 3. The second result, which became the paper's primary claim

A Monte Carlo identifiability study over **1.2 × 10⁴ simulated series** at six
lengths showed that the parameters carrying the cusp geometry are ratios,
`a = θ₂/θ₁`, whose denominator is not bounded away from zero. Series length
recovers their **ordering** but never their **value**: rank correlation for the
splitting factor reaches 0.88 at n = 1000 while linear correlation stays at
0.10.

This binds any study of this kind, not only mine. It is now the paper's stated
primary contribution, and the title names it.

## 4. What was measured

| Component | Scale |
|---|---|
| Corpora | 147 recordings, 40 people, 3 open datasets, all from primary repositories |
| Identifiability study | 2000 replicates per cell, 6 lengths, 12,000 series |
| Test size | 30,000 nominal + 7,500 calibrated replicates |
| Power | 2000 per cell across 4 regimes |
| Early-warning validation | 90 configurations, 500 each, 15,000 series |
| AR(1) persistence | 1000 replicates at each of 9 values of φ |

Every number in the paper has a replication count and a source file recorded in
`results/PROVENANCE.md`. That file exists because an earlier version of this
project cited two summary files that turned out to hold three-replicate smoke
output left behind by a crashed run. Nothing in the toolchain caught it, so I
built the audit.

## 5. Verification

- **Five adversarial review rounds**, written up and scored in `review/`.
- **A claim-level citation audit.** Every cited claim was checked against its
  source, not merely against its DOI. **Four sentences were citing claims their
  sources do not make**, including one where the meta-analysis I cited reports
  the *opposite* of what I had written. All four are corrected and the audit is
  recorded in `paper/REFERENCE_CHECK.md`.
- **A reproducibility check** (`code/experiments/reproduce.py`) that runs the
  unit tests, the citation consistency check and the manuscript compile in one
  command. All three stages pass.
- 28 unit tests checking each analytic claim against independent numerical
  computation.

## 6. What the paper does not claim

The target population is autistic adults and **none are analysed**. No public
wearable dataset of that group exists at the temporal density the model needs.
The paper says so in the abstract, the scope paragraph and the limitations, and
the title no longer names a population it does not measure. The identifiability
and estimator results are properties of the method, so they transfer to that
study when the data exist; no claim about the population transfers, and none is
made. A pre-registered validation protocol is specified.

I would rather submit a bounded result than an overstated one.

## 7. Current state

- Conference manuscript: 6 pages, IEEE format, 0 overfull boxes, 16 references.
- Long-form journal draft: 14 pages, compiles clean.
- Full artefact under MIT licence with provenance table and reproduction script.
- 39 commits with the reasoning recorded in each.

## 8. Disclosure

In accordance with IEEE policy on generative AI, the acknowledgment section of
the paper discloses that an AI assistant was used for code implementation,
literature organisation and manuscript drafting. I verified all analyses,
results and claims and I am solely responsible for the content. I am flagging
this here rather than leaving you to find it in the paper.

## 9. What I am asking for

1. Whether the repositioning in §3 is the right call, or whether you would
   frame the contribution differently.
2. Whether the scope handling in §6 is sufficient for submission, or whether
   the absent target population should be handled another way.
3. A venue decision. The paper is built for a six-page IEEE conference slot.
