#!/usr/bin/env python3
"""crap-score.py — per-function CRAP scorer and threshold gate.

CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)   (Savoia & Evans, 2007)

Input:  TSV rows on stdin or from a file: function<TAB>complexity<TAB>coverage_pct
Output: one scored row per function, breaches marked, then a summary line.
Exit:   0 when every function scores <= threshold, 1 on any breach,
        2 on every non-verdict, and those three are the whole set. Exit 2 covers
        malformed or empty input, a non-finite or overflowing complexity, coverage,
        threshold or score, an input this tool cannot read or decode, an output
        stream it cannot write, and any unexpected internal fault — a closed stdin,
        an interrupt, a function name a stream's encoding cannot carry. In particular
        no failure leaves wearing exit 1, CPython's default for an escaping exception
        and this tool's BREACH, and a dead output pipe exits 2 rather than leaking
        CPython's shutdown code 120, because a report nobody received is not a
        verdict about the code.

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
        if not line:
            continue
        # Narrow, on purpose, and the same rule the pack's other TSV gates already use:
        # a comment is a raw `#` in column 1 AND no tab anywhere on the line. Treating
        # every `#` line as a comment swallowed `#validate<TAB>9<TAB>40` — an ES2022
        # private method, which is how JavaScript spells one and how istanbul reports it
        # — so its 26.50 breach vanished and the gate exited 0. What decides it is the
        # line's shape, never the name's: any tab-bearing line is a row, so no row can
        # leave the numerator and denominator unnoticed, and an indented `# note` falls
        # through to the field count below and dies there. The price is the standard
        # `#function<TAB>complexity<TAB>coverage_pct` header spelling, which now reaches
        # the errors below and exits 2 instead of being skipped — loud and fail-closed,
        # never a false green. Spell such a header's separators as text, the way the
        # fixtures beside this script do, and it stays a comment.
        if line.startswith("#") and "\t" not in line:
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


if __name__ == "__main__":
    # THE SEAL. Two ways out of this script were open, and each handed a caller a code
    # the table above does not mean. CPython exits 1 on an escaping exception, and 1 is
    # this gate's BREACH: a closed stdin (AttributeError at sys.stdin.buffer) and an
    # ASCII-only stdout meeting a non-ASCII function name (UnicodeEncodeError) both left
    # that way, reaching the fix-until-green loop looking like a real breach, and the
    # agent would start rewriting code the gate never scored. CPython also flushes both
    # streams AGAIN at interpreter shutdown, after this module is done; when that flush
    # raises — `--help` into a dead pipe, a hung-up stderr — it REPLACES the status with
    # 120. So every exception is caught here except argparse's own SystemExit, and both
    # streams are flushed while a status can still be chosen, each failing fd pointed at
    # the null device so the shutdown flush cannot fail a second time.
    try:
        code = main()
    except SystemExit as exc:  # argparse's --help and usage errors pick their own status
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BrokenPipeError:  # the ordinary `| head` idiom: IO, never a verdict
        code = NON_VERDICT
    except BaseException as exc:  # no unexpected fault may wear a verdict's code
        try:
            print(f"crap-score: no verdict computed — {type(exc).__name__}: {exc}",
                  file=sys.stderr)
        except BaseException:  # a stream too broken to carry the reason still gets the code
            pass
        code = NON_VERDICT
    for stream, fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if stream is not None:
                stream.flush()
        except BaseException:  # closed, detached, or hung up
            if code in (0, 1):  # a report nobody received is not a verdict
                code = NON_VERDICT
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), fd)
            except BaseException:
                pass
    sys.exit(code)
