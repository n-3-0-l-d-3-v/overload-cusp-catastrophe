"""
chm.datasets
============
Loaders for the three corpora, each obtained from its PRIMARY peer-reviewed
repository rather than from a re-upload.  Provenance matters for review: a
Kaggle mirror of WESAD is the same bytes, but it is not a citable source and it
carries no licence guarantee.  See data/DATASETS.md.

D1  WESAD           15 subjects, controlled laboratory protocol
                    Schmidt et al., ICMI 2018; UCI ML Repository ID 465
D2  Exam stress     10 students x 3 exams, naturalistic cognitive load
                    Amin et al., PhysioNet, doi:10.13026/kvkb-aj90
D3  Nurse stress    15 nurses, ~1250 h of naturalistic occupational monitoring
                    Hosseini et al., Sci. Data 2022; Dryad doi:10.5061/dryad.5hqbzkh6f

The three form a deliberate gradient: fully controlled -> partly structured ->
fully in the wild.  That gradient is the point.  Early-warning theory applies
to systems fluctuating freely near a self-organised tipping point, NOT to a
system whose "transition" is an experimenter flipping a condition on.  D1 is
therefore included as a benchmark and as a negative control for the
early-warning analysis; D2 and D3 are where the theory is actually tested.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from . import signals as sg

__all__ = ["DATA_ROOT", "WINDOW_S", "load_wesad_subject", "wesad_subjects",
           "load_e4_dir", "load_exam_session", "exam_sessions",
           "load_nurse_subject", "nurse_subjects", "prepare"]

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
# Analysis window.  Chosen so the load coordinate is slow enough to carry
# recoverable drift but not so slow that a session yields too few samples:
# on WESAD, tonic EDA has lag-1 autocorrelation 0.998 at 10 s, 0.985 at 30 s and
# 0.958 at 60 s, while the number of windows per subject falls 607 -> 202 -> 101.
WINDOW_S = 30.0

# WESAD wrist sampling rates (Empatica E4)
FS_ACC, FS_BVP, FS_EDA, FS_TEMP, FS_LABEL = 32, 64, 4, 4, 700

# WESAD protocol labels
WESAD_LABELS = {1: "baseline", 2: "stress", 3: "amusement", 4: "meditation"}


# --------------------------------------------------------------------------- #
# D1 WESAD
# --------------------------------------------------------------------------- #
def wesad_subjects(root=None):
    root = Path(root or DATA_ROOT / "raw" / "WESAD")
    if not root.exists():
        return []
    return sorted(
        (p.name for p in root.iterdir() if p.is_dir() and (p / f"{p.name}.pkl").exists()),
        key=lambda s: int(s[1:]),
    )


def load_wesad_subject(sid, root=None, window_s=WINDOW_S, config="B"):
    """Return (frame, protocol_label_per_window) for one WESAD subject."""
    root = Path(root or DATA_ROOT / "raw" / "WESAD")
    with open(root / sid / f"{sid}.pkl", "rb") as f:
        d = pickle.load(f, encoding="latin1")

    w = d["signal"]["wrist"]
    acc = np.asarray(w["ACC"], float)
    bvp = np.asarray(w["BVP"], float).ravel()
    eda = np.asarray(w["EDA"], float).ravel()
    tmp = np.asarray(w["TEMP"], float).ravel()

    hr, rr = sg.hr_from_bvp(bvp, FS_BVP, window_s)
    tonic, phasic = sg.tonic_phasic(eda, FS_EDA)
    scr = sg.scr_rate(phasic, FS_EDA, window_s)
    we = max(int(window_s * FS_EDA), 1)
    ton_w = np.array([np.mean(tonic[i * we : (i + 1) * we])
                      for i in range(len(tonic) // we)])
    wt = max(int(window_s * FS_TEMP), 1)
    tmp_w = np.array([np.mean(tmp[i * wt : (i + 1) * wt])
                      for i in range(len(tmp) // wt)])
    _, switch = sg.activity_index(acc, FS_ACC, window_s)

    n = min(len(hr), len(scr), len(ton_w), len(switch), len(tmp_w))
    frame = sg.build_frame(hr[:n], rr[:n], scr[:n], ton_w[:n], switch[:n],
                           window_s, config=config, temp_win=tmp_w[:n])
    lab = sg.windowise(d["label"], FS_LABEL, window_s, n)
    frame["protocol"] = [WESAD_LABELS.get(int(v), "transition") for v in lab]
    frame["subject"] = sid
    frame["dataset"] = "WESAD"
    return frame


# --------------------------------------------------------------------------- #
# Empatica E4 CSV format (used by D2 and D3)
# --------------------------------------------------------------------------- #
def _read_e4_csv(path):
    """
    E4 CSV: row 0 = UNIX start time, row 1 = sampling rate, rest = samples.
    ACC has three columns; the header rows repeat per axis.
    """
    raw = pd.read_csv(path, header=None)
    if raw.shape[0] < 3:
        return None, None, None
    t0 = float(raw.iloc[0, 0])
    fs = float(raw.iloc[1, 0])
    vals = raw.iloc[2:].to_numpy(float)
    return (vals if vals.shape[1] > 1 else vals.ravel()), fs, t0


def load_e4_dir(d, window_s=WINDOW_S, config="B"):
    """Build a modelling frame from one directory of Empatica E4 CSV exports."""
    d = Path(d)
    need = {n: d / f"{n}.csv" for n in ("ACC", "BVP", "EDA")}
    if not all(p.exists() for p in need.values()):
        return None

    acc, fs_acc, t0 = _read_e4_csv(need["ACC"])
    bvp, fs_bvp, _ = _read_e4_csv(need["BVP"])
    eda, fs_eda, _ = _read_e4_csv(need["EDA"])
    tmp_p = d / "TEMP.csv"
    tmp, fs_tmp, _ = _read_e4_csv(tmp_p) if tmp_p.exists() else (None, None, None)
    if acc is None or bvp is None or eda is None:
        return None
    if min(len(bvp), len(eda)) < 100:
        return None

    hr, rr = sg.hr_from_bvp(np.asarray(bvp).ravel(), fs_bvp, window_s)
    tonic, phasic = sg.tonic_phasic(np.asarray(eda).ravel(), fs_eda)
    scr = sg.scr_rate(phasic, fs_eda, window_s)
    we = max(int(window_s * fs_eda), 1)
    ton_w = np.array([np.mean(tonic[i * we : (i + 1) * we])
                      for i in range(len(tonic) // we)])
    _, switch = sg.activity_index(np.atleast_2d(acc), fs_acc, window_s)

    if tmp is not None:
        wt = max(int(window_s * fs_tmp), 1)
        t_arr = np.asarray(tmp).ravel()
        tmp_w = np.array([np.mean(t_arr[i * wt : (i + 1) * wt])
                          for i in range(len(t_arr) // wt)])
    else:
        tmp_w = None

    n = min(len(hr), len(scr), len(ton_w), len(switch))
    if tmp_w is not None:
        n = min(n, len(tmp_w))
    if n < 60:
        return None
    frame = sg.build_frame(hr[:n], rr[:n], scr[:n], ton_w[:n], switch[:n],
                           window_s, config=config,
                           temp_win=None if tmp_w is None else tmp_w[:n])
    frame["t"] = t0 + np.arange(n) * window_s
    return frame


# --------------------------------------------------------------------------- #
# D2 exam stress
# --------------------------------------------------------------------------- #
def exam_sessions(root=None):
    root = Path(root or DATA_ROOT / "raw" / "exam_stress")
    if not root.exists():
        return []
    out = []
    for p in sorted(root.rglob("EDA.csv")):
        out.append(p.parent)
    return out


def load_exam_session(d, window_s=WINDOW_S, config="B"):
    d = Path(d)
    frame = load_e4_dir(d, window_s, config)
    if frame is None:
        return None
    frame["subject"] = d.parent.name
    frame["session"] = d.name
    frame["protocol"] = "exam"
    frame["dataset"] = "EXAM"
    return frame


# --------------------------------------------------------------------------- #
# D3 nurse stress
# --------------------------------------------------------------------------- #
def nurse_subjects(root=None, stratify=True):
    """
    Session directories for the nurse corpus, ordered ROUND-ROBIN BY NURSE.

    The corpus holds 609 sessions from 15 nurses, very unevenly distributed.
    Sorting by path and taking the first N -- the obvious thing, and what an
    earlier version did -- returns every session of nurse "15", then every
    session of "5C", and so on: a limit of 150 yielded 112 sessions from just
    5 of the 15 nurses, while the paper described the corpus as 15 nurses.

    Interleaving by nurse means any prefix of the list is spread across as many
    people as possible, so `limit` trades sessions for breadth instead of
    silently restricting the analysis to whoever sorts first.
    """
    root = Path(root or DATA_ROOT / "raw" / "nurse")
    if not root.exists():
        return []
    dirs = sorted({p.parent for p in root.rglob("EDA.csv")}, key=str)
    if not stratify:
        return dirs

    by_person: dict[str, list] = {}
    for d in dirs:
        pid = d.name.split("_")[0] if "_" in d.name else d.parent.name
        by_person.setdefault(pid, []).append(d)

    out, i = [], 0
    while len(out) < len(dirs):
        added = False
        for pid in sorted(by_person):
            if i < len(by_person[pid]):
                out.append(by_person[pid][i])
                added = True
        if not added:
            break
        i += 1
    return out


def load_nurse_subject(d, window_s=WINDOW_S, config="B"):
    d = Path(d)
    frame = load_e4_dir(d, window_s, config)
    if frame is None:
        return None
    frame["subject"] = d.parent.name if d.name.isdigit() else d.name
    frame["protocol"] = "shift"
    frame["dataset"] = "NURSE"
    return frame


# --------------------------------------------------------------------------- #
# convenience
# --------------------------------------------------------------------------- #
def prepare(dataset, config="B", window_s=WINDOW_S, limit=None, verbose=True):
    """Load every unit of one dataset; returns a list of frames."""
    frames = []
    if dataset == "WESAD":
        units = wesad_subjects()
        loader = lambda u: load_wesad_subject(u, window_s=window_s, config=config)
    elif dataset == "EXAM":
        units = exam_sessions()
        loader = lambda u: load_exam_session(u, window_s, config)
    elif dataset == "NURSE":
        units = nurse_subjects()
        loader = lambda u: load_nurse_subject(u, window_s, config)
    else:
        raise ValueError(dataset)

    if limit:
        units = units[:limit]
    for u in units:
        try:
            fr = loader(u)
            if fr is not None and len(fr) >= 60:
                frames.append(fr)
                if verbose:
                    print(f"  {dataset} {getattr(u,'name',u)}: {len(fr)} windows")
        except Exception as e:            # a corrupt export must not kill the run
            if verbose:
                print(f"  {dataset} {getattr(u,'name',u)}: FAILED ({e})")
    return frames
