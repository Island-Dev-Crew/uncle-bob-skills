#!/usr/bin/env python3
"""crap-score.py — per-function CRAP scorer and threshold gate.

CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)   (Savoia & Evans, 2007)

Input:  TSV rows on stdin or from a file: function<TAB>complexity<TAB>coverage_pct
Output: one scored row per function, breaches marked, then a summary line.
Exit:   0 when every function scores <= threshold, 1 on any breach,
        2 on every non-verdict, and those three are the whole set. Exit 2 covers
        malformed or empty input, a non-finite or overflowing complexity, coverage,
        threshold or score, an input this tool cannot read or decode, and an output
        stream it cannot write. In particular a dead output pipe exits 2 rather than
        leaking CPython's shutdown code 120, because a report nobody received is not
        a verdict about the code.

Usage:
  crap-score.py [--threshold N] [file.tsv]
  printf 'foo\\t5\\t80\\n' | crap-score.py --threshold 6
"""
import argparse
import io
import math
import os
import sys

NON_VERDICT = 2  # every path where the gate did not actually score the input


def crap(comp: float, cov: float) -> float:
    """Score one function. Raises OverflowError on finite input too large to square."""
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
        # nan and inf parse as floats and then defeat every comparison below: `nan < 1`
        # is False, so a nan complexity used to reach the gate and score nan, and
        # `nan > threshold` is False, so the row printed ok and the gate exited green.
        if not (math.isfinite(comp) and math.isfinite(cov)):
            errors.append(f"line {n}: complexity/coverage must be finite, got "
                          f"{comp_s!r}/{cov_s!r}")
            continue
        if comp < 1 or not 0 <= cov <= 100:
            errors.append(f"line {n}: complexity must be >=1 and coverage in 0..100")
            continue
        try:
            score = crap(comp, cov)
        except OverflowError:
            errors.append(f"line {n}: score overflows the float range at complexity {comp:g}")
            continue
        if not math.isfinite(score):
            errors.append(f"line {n}: score is not finite")
            continue
        rows.append((fn, comp, cov, score))
    return rows, errors


def report(rows, threshold):
    breaches = 0
    for fn, comp, cov, score in rows:
        over = score > threshold
        breaches += over
        print(f"{'BREACH' if over else 'ok    '} {score:8.2f}  comp={comp:g} cov={cov:g}%  {fn}")
    print(f"{len(rows)} functions, {breaches} over threshold {threshold:g}")
    return 1 if breaches else 0


def main() -> int:
    p = argparse.ArgumentParser(description="Per-function CRAP scorer and threshold gate.")
    p.add_argument("--threshold", type=float, default=6.0,
                   help="breach when score > threshold (default 6, the agent regime)")
    p.add_argument("tsv", nargs="?",
                   help="TSV file (default stdin): function<TAB>complexity<TAB>coverage_pct")
    args = p.parse_args()

    # A gate whose report goes nowhere has not reported. CPython hands us sys.stdout is
    # None when fd 1 was closed before exec, and print() then discards every row in
    # silence — a green that nobody could have read.
    if sys.stdout is None:
        print("crap-score: stdout is closed — no verdict was reported", file=sys.stderr)
        return NON_VERDICT
    # An out-of-range threshold is the same class of fault as a bad row: `x > nan` and
    # `x > inf` are False for every finite score, so the gate would pass everything.
    if not math.isfinite(args.threshold):
        print(f"crap-score: --threshold must be finite, got {args.threshold}", file=sys.stderr)
        return NON_VERDICT

    try:
        # stdin is re-wrapped rather than used as-is. CPython picks its error handler
        # from the locale, and on a UTF-8 locale that is `surrogateescape`: bytes this
        # tool cannot decode become surrogates, flow through the parser, and get SCORED —
        # a BREACH verdict printed over input that was never valid. The file path already
        # decoded strictly, so the same bytes produced a verdict from stdin and a refusal
        # from a file. Deciding this here makes the two agree on every machine.
        src = (open(args.tsv, encoding="utf-8") if args.tsv
               else io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="strict"))
    except OSError as exc:
        # An unreadable input is not a CRAP breach. Borrowing exit 1 here handed a
        # fix-until-green agent a dirty verdict over a file that was never scored, and
        # it would start splitting functions to satisfy a gate that never ran.
        print(f"crap-score: {exc}", file=sys.stderr)
        return NON_VERDICT
    try:
        with src:
            rows, errors = parse_rows(src)
    except UnicodeDecodeError as exc:
        # Same reasoning as an unreadable file: bytes we cannot decode were never scored.
        print(f"crap-score: {args.tsv or '<stdin>'}: not valid UTF-8 ({exc})", file=sys.stderr)
        return NON_VERDICT

    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return NON_VERDICT
    if not rows:
        print("ERROR no rows scored — an empty gate cannot pass", file=sys.stderr)
        return NON_VERDICT

    return report(rows, args.threshold)


def quiet_stdio() -> None:
    """Point the standard streams at the null device.

    Without this, the interpreter's own shutdown flush hits the dead pipe after main()
    has returned and CPython replaces our exit status with 120 — a code this tool does
    not document and a caller cannot read.
    """
    try:
        null = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            os.dup2(null, stream.fileno())
        except (OSError, ValueError, AttributeError):
            continue


if __name__ == "__main__":
    try:
        code = main()
        if sys.stdout is not None:
            sys.stdout.flush()
    except BrokenPipeError:
        quiet_stdio()
        code = NON_VERDICT
    except OSError as exc:
        quiet_stdio()
        print(f"crap-score: output failed: {exc}", file=sys.stderr)
        code = NON_VERDICT
    sys.exit(code)
