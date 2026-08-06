"""
cluster_analysis.py
===================
E14: does the headline result survive the fact that recordings are nested
within people?

112 of the 157 units are nurse *sessions*, and those sessions come from only 15
nurses. Treating each session as independent gives that corpus most of the
weight in any pooled proportion and understates the standard error, because
sessions from one person share whatever that person's physiology does.

The pooled figure is therefore not by itself adequate. This script recomputes
the headline rejection rate three ways:

    unit level     every recording counts once (what the paper reports)
    subject level  each person contributes the mean of their own sessions,
                   then people are averaged -- one vote per person
    any-session    fraction of people with at least one significant session,
                   which is the most generous possible reading

If the conclusion is a null, the subject-level figure is the one that could
overturn it: a null driven by many uninformative sessions from a few people
would look different once people are weighted equally.

    python experiments/cluster_analysis.py --config B
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RESULTS = Path(__file__).resolve().parents[2] / "results"


def person_id(dataset, unit):
    """
    Recover the individual behind a recording.

    WESAD  'S2'                -> S2          (subject == recording)
    EXAM   'S1' + session      -> S1          (3 exams per student)
    NURSE  '15_1594140175'     -> 15          (nurse id, then a shift timestamp)
    """
    u = str(unit)
    if dataset == "NURSE":
        m = re.match(r"([A-Za-z0-9]+?)_\d{6,}", u)
        return f"NURSE:{m.group(1) if m else u}"
    return f"{dataset}:{u}"


def summarise(df, pcol, label):
    df = df.dropna(subset=[pcol]).copy()
    if not len(df):
        print(f"  {label}: no data")
        return None
    df["sig"] = (df[pcol] < 0.05).astype(float)
    df["person"] = [person_id(d, u) for d, u in zip(df["dataset"], df["unit"])]

    unit_rate = df["sig"].mean()
    per_person = df.groupby("person")["sig"].mean()
    subj_rate = per_person.mean()
    any_rate = (df.groupby("person")["sig"].max() > 0).mean()

    # cluster-robust SE for the subject-level mean
    se = per_person.std(ddof=1) / np.sqrt(len(per_person)) if len(per_person) > 1 else np.nan

    print(f"  {label}")
    print(f"     units                : {len(df)}")
    print(f"     people               : {len(per_person)}")
    print(f"     unit-level rate      : {unit_rate:.3f}")
    print(f"     subject-level rate   : {subj_rate:.3f}"
          + (f"  (95% CI [{subj_rate-1.96*se:.3f}, {subj_rate+1.96*se:.3f}])"
             if np.isfinite(se) else ""))
    print(f"     >=1 sig. session     : {any_rate:.3f} of people")
    return {"stat": label, "n_units": len(df), "n_people": len(per_person),
            "unit_rate": unit_rate, "subject_rate": subj_rate,
            "subject_se": se, "any_session_rate": any_rate}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="B")
    args = ap.parse_args()

    rows = []

    f3 = RESULTS / f"e3_lrt_cfg{args.config}.csv"
    if f3.exists():
        d = pd.read_csv(f3).rename(columns={"subject": "unit"})
        print(f"\nE3, config {args.config} — calibrated tests, "
              f"clustered by person")
        print("=" * 66)
        for col, lab in (("p_rw_lam_t", "cubic term (decisive)"),
                         ("p_rw_lr", "likelihood ratio"),
                         ("p_rw_bimodality", "marginal bimodality")):
            if col in d.columns:
                r = summarise(d, col, lab)
                if r:
                    r["source"] = "E3"
                    rows.append(r)

    f13 = RESULTS / "e13_surrogate_comparison.csv"
    if f13.exists():
        d13 = pd.read_csv(f13)
        print(f"\nE13 — cubic term by surrogate ensemble, clustered by person")
        print("=" * 66)
        for cfg, g in d13.groupby("config"):
            for col, lab in (("p_rw", f"config {cfg}: random-walk null"),
                             ("p_iaaft", f"config {cfg}: IAAFT null")):
                if col in g.columns:
                    r = summarise(g, col, lab)
                    if r:
                        r["source"] = f"E13-{cfg}"
                        rows.append(r)

    if rows:
        out = pd.DataFrame(rows)
        out.to_csv(RESULTS / f"e14_clustered_cfg{args.config}.csv", index=False)
        print(f"\nwrote {RESULTS / f'e14_clustered_cfg{args.config}.csv'}")
        print("\nRead: if the subject-level rate tracks the unit-level rate,")
        print("the pooled figure is not an artefact of session counts.")


if __name__ == "__main__":
    main()
