"""
fetch_data.py
=============
Download the three corpora from their PRIMARY repositories and extract only the
files the pipeline needs.  No Kaggle mirrors: see data/DATASETS.md for why the
distinction matters.

    python code/experiments/fetch_data.py            # download + extract
    python code/experiments/fetch_data.py --verify   # check what is present

Sizes are checked against the values recorded at first download; a mismatch
stops the run rather than silently analysing a truncated file.
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
RAW = DATA / "raw"

SOURCES = {
    "WESAD": {
        "url": "https://uni-siegen.sciebo.de/s/HGdUkoNlW1Ub0Gx/download",
        "file": "WESAD.zip",
        "bytes": 2249444501,
        "cite": "Schmidt et al., ICMI 2018; UCI ML Repository ID 465",
    },
    "EXAM": {
        "url": "https://physionet.org/content/wearable-exam-stress/get-zip/1.0.0/",
        "file": "exam_stress.zip",
        "bytes": 85968624,
        "cite": "Amin et al., PhysioNet, doi:10.13026/kvkb-aj90",
    },
    "NURSE": {
        "url": "https://zenodo.org/api/records/5514277/files/Stress_dataset.zip/content",
        "file": "Stress_dataset.zip",
        "bytes": 1156939542,
        "cite": "Hosseini et al., Sci. Data 2022; doi:10.5061/dryad.5hqbzkh6f",
    },
    "NURSE_SURVEY": {
        "url": "https://zenodo.org/api/records/5514277/files/SurveyResults.xlsx/content",
        "file": "SurveyResults.xlsx",
        "bytes": 49048,
        "cite": "Hosseini et al., Sci. Data 2022",
    },
}


def download(name, spec):
    dest = DATA / spec["file"]
    if dest.exists() and dest.stat().st_size == spec["bytes"]:
        print(f"  {name}: already present ({dest.stat().st_size} bytes)")
        return dest
    print(f"  {name}: downloading from {spec['url']}")
    DATA.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(spec["url"], headers={"User-Agent": "chm/1.0"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    got = dest.stat().st_size
    if got != spec["bytes"]:
        raise RuntimeError(
            f"{name}: expected {spec['bytes']} bytes, got {got}. "
            "Refusing to continue with a possibly truncated file."
        )
    print(f"  {name}: ok ({got} bytes)")
    return dest


def extract_wesad(zip_path):
    out = RAW / "WESAD"
    if list(out.glob("S*/S*.pkl")):
        print("  WESAD: already extracted")
        return
    print("  WESAD: extracting .pkl and _quest.csv")
    with zipfile.ZipFile(zip_path) as z:
        want = [n for n in z.namelist()
                if n.endswith(".pkl") or n.endswith("_quest.csv")]
        for n in want:
            z.extract(n, RAW)


def extract_exam(zip_path):
    out = RAW / "exam_stress"
    if list(out.rglob("EDA.csv")):
        print("  EXAM: already extracted")
        return
    print("  EXAM: extracting nested Data.zip")
    out.mkdir(parents=True, exist_ok=True)
    root = ("a-wearable-exam-stress-dataset-for-predicting-cognitive-"
            "performance-in-real-world-settings-1.0.0/")
    with zipfile.ZipFile(zip_path) as z:
        for extra in ("readme.md", "StudentGrades.txt", "LICENSE.txt"):
            try:
                (out / extra).write_bytes(z.read(root + extra))
            except KeyError:
                pass
        zipfile.ZipFile(io.BytesIO(z.read(root + "Data.zip"))).extractall(out)


def extract_nurse(zip_path):
    out = RAW / "nurse"
    if len(list(out.rglob("EDA.csv"))) > 500:
        print("  NURSE: already extracted")
        return
    print("  NURSE: extracting per-session archives")
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        inner = [n for n in z.namelist() if n.endswith(".zip")]
        for n in inner:
            sub = n.split("/")[0]
            d = out / sub / Path(n).stem
            if (d / "EDA.csv").exists():
                continue
            try:
                zi = zipfile.ZipFile(io.BytesIO(z.read(n)))
            except Exception as e:
                print(f"    skip {n}: {e}")
                continue
            d.mkdir(parents=True, exist_ok=True)
            for f in ("ACC.csv", "BVP.csv", "EDA.csv", "HR.csv",
                      "TEMP.csv", "tags.csv"):
                if f in zi.namelist():
                    (d / f).write_bytes(zi.read(f))


def verify():
    print("Present:")
    print(f"  WESAD subjects : {len(list((RAW/'WESAD').glob('S*/S*.pkl')))}")
    print(f"  EXAM sessions  : {len(list((RAW/'exam_stress').rglob('EDA.csv')))}")
    print(f"  NURSE sessions : {len(list((RAW/'nurse').rglob('EDA.csv')))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        verify()
        return

    RAW.mkdir(parents=True, exist_ok=True)
    print("Fetching from primary repositories (no Kaggle mirrors):")
    for name, spec in SOURCES.items():
        print(f"\n{name}  [{spec['cite']}]")
        p = download(name, spec)
        if name == "WESAD":
            extract_wesad(p)
        elif name == "EXAM":
            extract_exam(p)
        elif name == "NURSE":
            extract_nurse(p)
    print()
    verify()


if __name__ == "__main__":
    sys.exit(main())
