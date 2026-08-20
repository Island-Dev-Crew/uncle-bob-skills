#!/usr/bin/env python3
"""crap-score.py — per-function CRAP scorer and threshold gate.

CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)   (Savoia & Evans, 2007)

Input:  TSV rows on stdin or from a file: function<TAB>complexity<TAB>coverage_pct
Output: one scored row per function, breaches marked, then a summary line.
Exit:   0 when every function scores <= threshold, 1 on any breach,
        2 on malformed or empty input (fail closed — an empty gate cannot pass).

Usage:
  crap-score.py [--threshold N] [file.tsv]
  printf 'foo\\t5\\t80\\n' | crap-score.py --threshold 6
"""
import argparse
import sys


def crap(comp: float, cov: float) -> float:
    return comp ** 2 * (1 - cov / 100) ** 3 + comp


def parse_rows(src):
    rows, errors = [], []
    for n, line in enumerate(src, 1):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            errors.append(f"line {n}: expected 3 tab-separated fields, got {len(parts)}")
            continue
        fn, comp_s, cov_s = parts
        try:
            comp, cov = float(comp_s), float(cov_s)
        except ValueError:
            errors.append(f"line {n}: complexity/coverage not numeric")
            continue
        if comp < 1 or not 0 <= cov <= 100:
            errors.append(f"line {n}: complexity must be >=1 and coverage in 0..100")
            continue
        rows.append((fn, comp, cov, crap(comp, cov)))
    return rows, errors


def main() -> int:
    p = argparse.ArgumentParser(description="Per-function CRAP scorer and threshold gate.")
    p.add_argument("--threshold", type=float, default=6.0,
                   help="breach when score > threshold (default 6, the agent regime)")
    p.add_argument("tsv", nargs="?",
                   help="TSV file (default stdin): function<TAB>complexity<TAB>coverage_pct")
    args = p.parse_args()

    src = open(args.tsv, encoding="utf-8") if args.tsv else sys.stdin
    with src:
        rows, errors = parse_rows(src)

    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 2
    if not rows:
        print("ERROR no rows scored — an empty gate cannot pass", file=sys.stderr)
        return 2

    breaches = 0
    for fn, comp, cov, score in rows:
        over = score > args.threshold
        breaches += over
        print(f"{'BREACH' if over else 'ok    '} {score:8.2f}  comp={comp:g} cov={cov:g}%  {fn}")
    print(f"{len(rows)} functions, {breaches} over threshold {args.threshold:g}")
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
