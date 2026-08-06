"""
check_citations.py
==================
Two jobs, both of which have caught real defects in this project.

1. Consistency. Every key cited in the manuscript must exist in refs.bib, and
   every entry in refs.bib should be cited by something. An uncited entry is
   usually a leftover from an earlier draft; a cited-but-missing key compiles
   to a bare [?] that is easy to miss in a long PDF.

2. Correctness. Round 4 of the self-review checked nine entries against
   publisher metadata and found six wrong, including one DOI that resolved to
   an entirely different paper. That is not a rate at which the remaining
   entries can be assumed clean, so this script re-checks every entry that
   carries a DOI against the Crossref REST API and reports disagreements in
   first author, year, title and container.

   Crossref is the authority here rather than a search engine: it serves the
   metadata the publisher itself deposited.

Usage
-----
    python code/experiments/check_citations.py              # consistency only
    python code/experiments/check_citations.py --crossref   # + network check

The network check is deliberately opt-in so the consistency pass stays usable
offline and in CI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / "paper" / "main.tex"
BIB = ROOT / "paper" / "refs.bib"

CITE_RE = re.compile(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]*)\}")
ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)

# Crossref asks for a contact address in the User-Agent so they can reach you
# if a script misbehaves. ORCID serves the same purpose without publishing an
# inbox in the repository.
UA = ("chm-citation-check/1.0 "
      "(https://orcid.org/0009-0001-8802-7376)")


def cited_keys(text):
    keys = set()
    for m in CITE_RE.finditer(text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.add(k)
    return keys


def bib_entries(text):
    """Return {key: {field: value}} for every entry in the file."""
    out = {}
    for m in ENTRY_RE.finditer(text):
        key = m.group(2)
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start:i - 1]
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*[{\"](.+?)[}\"]\s*,?\s*(?=\w+\s*=|$)",
                              body, re.DOTALL):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        out[key] = fields
    return out


def norm(s):
    s = re.sub(r"[{}\\]", "", (s or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]


def datacite(doi):
    """
    Datasets are usually registered with DataCite rather than Crossref, so a
    Crossref 404 on a PhysioNet or Zenodo DOI means "wrong registry", not
    "wrong DOI". Normalised into the subset of Crossref's shape we use.
    """
    url = "https://api.datacite.org/dois/" + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        a = json.load(r)["data"]["attributes"]
    authors = []
    for c in a.get("creators", []):
        name = c.get("name", "")
        authors.append({"family": c.get("familyName")
                        or (name.split(",")[0].strip() if "," in name else name),
                        "given": c.get("givenName", "")})
    return {
        "title": [t.get("title", "") for t in a.get("titles", [])],
        "author": authors,
        "container-title": [a.get("publisher", "")],
        "issued": {"date-parts": [[a.get("publicationYear")]]},
    }


def pub_year(m):
    """
    The year a reader will find on the article.

    Crossref's `issued` is the earliest registered date, which for a journal
    that posts online-first is the preprint year, not the year of the issue the
    volume and page numbers refer to. Citing the print year alongside a volume
    and issue is correct, so `published-print` wins where it exists. Ignoring
    this produced four spurious "wrong year" reports on entries that were fine.
    """
    for field in ("published-print", "issued"):
        parts = ((m.get(field) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            return str(parts[0])
    return ""


def check_against_crossref(key, f):
    """Return a list of human-readable disagreements for one entry."""
    doi = f.get("doi", "").strip()
    if not doi:
        return ["no DOI in entry; not machine-checkable"]
    try:
        m = crossref(doi)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return [f"Crossref lookup failed (HTTP {e.code})"]
        try:
            m = datacite(doi)
        except Exception:
            return ["DOI resolves at neither Crossref nor DataCite -- "
                    "the DOI itself is probably wrong"]
    except Exception as e:
        return [f"lookup failed: {type(e).__name__}"]

    bad = []

    got_title = norm(" ".join(m.get("title") or []))
    want_title = norm(f.get("title"))
    if want_title and got_title:
        wt, gt = set(want_title.split()), set(got_title.split())
        if wt and len(wt & gt) / len(wt) < 0.6:
            bad.append(f"title: bib has {f.get('title')!r}, "
                       f"Crossref has {' '.join(m.get('title') or [])!r}")

    authors = m.get("author") or []
    if authors:
        got_first = norm(authors[0].get("family", ""))
        want_auth = norm(f.get("author"))
        if got_first and want_auth and got_first not in want_auth:
            names = ", ".join(
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in authors[:4])
            bad.append(f"author: bib has {f.get('author')!r}, "
                       f"Crossref first author is "
                       f"{authors[0].get('family')!r} ({names}...)")

    got_year = pub_year(m)
    want_year = re.sub(r"\D", "", f.get("year", ""))
    if got_year and want_year and got_year != want_year:
        bad.append(f"year: bib has {want_year}, Crossref has {got_year}")

    got_ct = norm(" ".join(m.get("container-title") or []))
    want_ct = norm(f.get("journal") or f.get("booktitle") or "")
    if got_ct and want_ct:
        wc, gc = set(want_ct.split()), set(got_ct.split())
        if wc and len(wc & gc) / len(wc) < 0.4:
            bad.append(f"venue: bib has "
                       f"{f.get('journal') or f.get('booktitle')!r}, "
                       f"Crossref has {' '.join(m.get('container-title') or [])!r}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crossref", action="store_true",
                    help="verify every DOI-bearing entry against Crossref")
    ap.add_argument("--only-cited", action="store_true",
                    help="restrict the Crossref pass to entries the paper cites")
    args = ap.parse_args()

    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    cited = cited_keys(tex)
    entries = bib_entries(bib)

    print(f"cited keys      : {len(cited)}")
    print(f"bib entries     : {len(entries)}")

    missing = sorted(cited - set(entries))
    uncited = sorted(set(entries) - cited)
    print(f"\ncited but absent from refs.bib ({len(missing)}):")
    for k in missing:
        print(f"   MISSING  {k}")
    print(f"\nin refs.bib but never cited ({len(uncited)}):")
    for k in uncited:
        print(f"   unused   {k}")

    rc = 1 if missing else 0

    if args.crossref:
        keys = sorted(cited & set(entries)) if args.only_cited else sorted(entries)
        print(f"\nCrossref verification of {len(keys)} entries")
        print("-" * 70)
        clean = nodoi = flagged = 0
        for k in keys:
            problems = check_against_crossref(k, entries[k])
            if not problems:
                clean += 1
                continue
            if len(problems) == 1 and problems[0].startswith("no DOI"):
                nodoi += 1
                print(f"\n  {k}\n     - {problems[0]}")
                continue
            flagged += 1
            rc = 1
            print(f"\n  {k}")
            for p in problems:
                print(f"     ! {p}")
            time.sleep(0.2)          # be polite to the API
        print("\n" + "-" * 70)
        print(f"verified clean {clean} | no DOI {nodoi} | disagreements {flagged}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
