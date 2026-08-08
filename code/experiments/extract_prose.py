"""
extract_prose.py
================
Pull the readable prose out of the manuscript, so that anything you run over it
-- a readability check, a style pass, a similarity or AI check -- is reading
what a human reads rather than LaTeX markup.

    python code/experiments/extract_prose.py            # -> paper/prose.txt
    python code/experiments/extract_prose.py --stdout

Why this matters. A .tex file is roughly a third notation by character count:
control sequences, math, table cells, bibliography keys, float bodies. Tools
that expect natural language have no idea what to do with `\\cite{kiep2025}` or
`$V(x;a,b)=\\tfrac14 x^4-\\tfrac12 a x^2-bx$`, and whatever score they return
for a file full of that is not a measurement of the writing.

What is kept: the abstract and the body paragraphs. Citations and
cross-references are removed, and inline maths is rendered to readable text
rather than deleted, so sentences stay grammatical and keep their values.

What is dropped: preamble, figure and table environments, captions, the
bibliography, and section headings. Captions and headings are labels, not
prose, and their clipped register skews any per-sentence statistic.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"

DROP_ENVS = ("figure", "figure*", "table", "table*", "tabular",
             "equation", "equation*", "align", "align*", "eqnarray",
             "IEEEkeywords", "thebibliography", "proposition")


GREEK = {
    "alpha": "\u03b1", "beta": "\u03b2", "gamma": "\u03b3", "delta": "\u03b4",
    "epsilon": "\u03b5", "varepsilon": "\u03b5", "theta": "\u03b8",
    "lambda": "\u03bb", "mu": "\u03bc", "sigma": "\u03c3", "phi": "\u03c6",
    "rho": "\u03c1", "tau": "\u03c4", "Delta": "\u0394", "Var": "Var",
}
SYMBOL = {
    r"\times": "\u00d7", r"\pm": "\u00b1", r"\mp": "\u2213",
    r"\le": "\u2264", r"\leq": "\u2264", r"\ge": "\u2265", r"\geq": "\u2265",
    r"\gtrsim": "\u2273", r"\lesssim": "\u2272", r"\approx": "\u2248",
    r"\to": "\u2192", r"\propto": "\u221d", r"\cdot": "\u00b7",
    r"\ll": "\u226a", r"\gg": "\u226b", r"\neq": "\u2260", r"\infty": "\u221e",
    r"\log": "log", r"\exp": "exp", r"\sqrt": "sqrt",
}


def math_to_text(m: str) -> str:
    """Render inline maths as something a reader can say out loud."""
    m = re.sub(r"\\tfrac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", m)
    m = re.sub(r"\\d?frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", m)
    m = re.sub(r"\\hat\{?\\?([a-zA-Z]+)\}?", r"\1-hat", m)
    m = re.sub(r"\\(math|text|mathrm|mathbf|operatorname)\{([^{}]*)\}", r"\2", m)
    m = re.sub(r"10\^\{?(-?\d+)\}?", r"10^\1", m)
    for k, v in SYMBOL.items():
        m = m.replace(k, v)
    for k, v in GREEK.items():
        m = re.sub(r"\\" + k + r"\b", v, m)
    m = re.sub(r"_\{?([A-Za-z0-9]+)\}?", r"\1", m)      # subscripts inline
    m = re.sub(r"\^\{?([A-Za-z0-9/+-]+)\}?", r"^\1", m)
    m = re.sub(r"\\[a-zA-Z]+", "", m)                    # leftovers
    m = m.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", m).strip()


def extract(tex: str) -> str:
    # Body only: from the abstract to the acknowledgment.
    start = tex.find(r"\begin{abstract}")
    end = tex.find(r"\section*{Acknowledgment}")
    if end == -1:
        end = tex.find(r"\bibliographystyle")
    body = tex[start if start != -1 else 0: end if end != -1 else len(tex)]

    # Comments first, so commented-out text never reaches the output.
    body = re.sub(r"(?<!\\)%.*", "", body)

    # Whole environments that are not prose.
    for env in DROP_ENVS:
        body = re.sub(re.escape(r"\begin{" + env + "}") + r".*?"
                      + re.escape(r"\end{" + env + "}"), " ", body, flags=re.S)

    # Citations and cross-references become nothing; the sentence around them
    # is what we want to read.
    body = re.sub(r"~?\\cite[tp]?\*?(\[[^\]]*\])*\{[^}]*\}", "", body)
    body = re.sub(r"~?\\(ref|eqref|autoref|Cref|cref)\{[^}]*\}", "", body)
    body = re.sub(r"\\label\{[^}]*\}", "", body)

    # Inline maths is rendered to readable text rather than deleted. Deleting
    # it leaves holes -- "grows as the power of the splitting factor" with the
    # 3/2 missing -- and ungrammatical sentences skew anything read off the
    # result. Keeping the value preserves the sentence a reader actually sees.
    body = re.sub(r"\\SIrange\{([^}]*)\}\{([^}]*)\}\{[^}]*\}", r"\1 to \2", body)
    body = re.sub(r"\\SI\{([^}]*)\}\{[^}]*\}", r"\1", body)
    body = re.sub(r"\\num\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\$\$(.*?)\$\$", lambda m: " " + math_to_text(m.group(1)) + " ",
                  body, flags=re.S)
    body = re.sub(r"\$([^$]*)\$", lambda m: math_to_text(m.group(1)), body)

    # Text-level commands: keep the argument, drop the command.
    for cmd in ("emph", "textbf", "textit", "texttt", "mbox", "text"):
        for _ in range(3):
            body = re.sub(r"\\" + cmd + r"\{([^{}]*)\}", r"\1", body)

    # Section headings are labels, not prose.
    body = re.sub(r"\\(section|subsection|subsubsection|paragraph)\*?\{[^}]*\}",
                  "\n\n", body)

    # Anything left that is still a control sequence.
    body = re.sub(r"\\[a-zA-Z@]+\*?", " ", body)
    body = re.sub(r"\\[^a-zA-Z]", " ", body)
    body = body.replace("---", "\u2014").replace("--", "\u2013")
    body = re.sub(r"``|''", '"', body)
    body = re.sub(r"[{}]", " ", body)

    # The VALUE placeholders have done their job; drop them and tidy.
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" ([,.;:%)])", r"\1", body)
    body = re.sub(r"\( ", "(", body)
    body = re.sub(r"\n{3,}", "\n\n", body)

    paras = [re.sub(r"\s+", " ", p).strip() for p in body.split("\n\n")]
    paras = [p for p in paras if len(p.split()) >= 12]
    out = "\n\n".join(paras)
    # The abstract environment leaves its own name at the very front.
    return re.sub(r"^abstract\s+", "", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="main.tex")
    ap.add_argument("--out", default="prose.txt")
    ap.add_argument("--stdout", action="store_true")
    a = ap.parse_args()

    prose = extract((PAPER / a.tex).read_text(encoding="utf-8"))
    if a.stdout:
        print(prose)
        return

    out = PAPER / a.out
    out.write_text(prose, encoding="utf-8")
    words = len(prose.split())
    paras = prose.count("\n\n") + 1
    src = len((PAPER / a.tex).read_text(encoding="utf-8").split())
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  {paras} paragraphs, {words} words")
    print(f"  source was {src} whitespace-tokens; "
          f"{100 * (1 - words / src):.0f}% of it was markup, not prose")


if __name__ == "__main__":
    main()
