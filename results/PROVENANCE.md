# Which file backs which claim, and at what replication

This file exists because a previous version of this project cited
`m3_power_summary.csv` and `m5_ews_summary.csv` in the supplement when both held
two- and three-replicate smoke output left behind by a crashed run. Nothing in
the toolchain caught it. The fix is to state replication next to every number
and keep this table current.

Regenerate the audit with:

```bash
python -c "
import pandas as pd, glob, os
for f in sorted(glob.glob('results/*summary*.csv')+glob.glob('results/e0*.csv')):
    d=pd.read_csv(f); c=[x for x in d.columns if 'n_rep' in x or x=='count']
    print(os.path.basename(f), len(d), min(int(d[x].min()) for x in c) if c else '-')
"
```

---

## Monte Carlo suite

Run 2026-08-07 with `mega_run.py --block all --resume`. **Stopped by hand part
way through**, so the blocks below differ in how much of their grid completed.
Everything is checkpointed in `results/_checkpoints/`; `--resume` continues.

| File | Backs | Replicates | Grid coverage |
|---|---|---|---|
| `m1_recovery_summary.csv` | Table I, Fig. 2a, Sec. IV | **2000/cell**, 12,000 series | complete |
| `m2_size_summary.csv` | Results §A, Fig. 3a | **5000/cell**, 30,000 nominal + 7,500 calibrated | complete |
| `m5_ews_summary.csv` | Table II, Results §B | **500/cell**, 15,000 series | complete, 90 configurations |
| `m6_noise_summary.csv` | supplementary robustness | **1000/cell** | **10 of 15 cells.** Run stopped before the high-$\sigma$ end. The `complete` column marks which cells are full; no cell is partial |
| `m3_power_summary.csv` | Results §A, Fig. 3b | **100/cell** | rebuilt from `e0_power_size.csv`; the power block never ran. `source` column records this |
| — persistence | Results §D | see `e15` below | block never ran |

`m1_recovery_summary.csv` reports **both** Spearman and Pearson. They answer
different questions and the gap between them is a result in its own right; see
Sec. IV. It also carries `p99_abs_est` and `max_abs_est`, which are what make
the gap legible.

## Earlier runs still in use

These predate the Monte Carlo suite and remain the source for claims the suite
did not reach. Replication is lower and the paper says so where it matters.

| File | Backs | Replicates | Note |
|---|---|---|---|
| `e0_power_size.csv` | power at $n=200$: 1.00 / 0.76 / 0.24 | 100/cell | valid, just less precise than the rest |
| `e15_size_vs_persistence.csv` | AR(1) persistence robustness, Fig. 12 | 40/point | thin. At 40 replicates this cannot detect an inflation below about 0.15, and the paper now states that |
| `e12_ews_validation.csv` | — | 24/cell | **superseded** by `m5` at 500/cell. Retained for the record; nothing cites it |
| `e2`–`e9`, `e11`, `e13`, `e14` | corpus analyses, Results §C–D | 147 units, 40 people | real data, not simulation |

## Corpus results

`SUMMARY_cfgB.txt` is the primary configuration. `cfgA` is the **negative
control** (a cardiac index shown to be noise-dominated) and `cfgC` a robustness
check; both are elevated and the paper explains why that is the control working
rather than a finding.

## Rule

If a number appears in the paper, its file appears above with its replication.
A file whose replication is not stated here should be assumed unverified.
