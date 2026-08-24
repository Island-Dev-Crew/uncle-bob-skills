#!/usr/bin/env python3
"""strategic-share.py — deterministic accounting for the tactical/strategic split (C25).

Reads TSV rows (stdin, or one file path argument):

    item <TAB> tag <TAB> minutes [<TAB> evidence]

  tag       'tactical' or 'strategic' (case-insensitive); anything else is malformed
  minutes   positive finite number — effort booked to that item
  evidence  required on strategic rows, form: metric=before->after (e.g. crap_max=14->5)
            before must differ from after; a no-delta pair is not evidence of a
            structural change, so the row is discounted as UNEVIDENCED

Every non-blank line is a data row EXCEPT a narrow comment: a raw '#' in column 1
with NO tab anywhere on the line. So '#482-checkout-flow<TAB>tactical<TAB>540' is an
issue-numbered work item, not a comment, and an indented '# note' is a malformed row
(exit 2) rather than a silent drop — shrinking the denominator must never be cheaper
than re-tagging. Lines skipped as comments are counted in the report.

Prints one line per row, then the EVIDENCED strategic share of total effort against
the target band. Unevidenced strategic minutes stay in the denominator and leave the
numerator: an unbacked strategic claim lowers the share instead of flattering it.

Exit codes (distinct meanings, never shared):
  0  every strategic row evidenced AND share at or above the floor
  1  verdict breach — an unevidenced strategic row, or share below the floor
  2  fail-closed on ledger CONTENT — empty ledger, or a malformed/undecidable row
  3  IO or usage error — unreadable path, bad flag, --help (never a verdict)

OVER the ceiling prints OVER and exits 0: over-investment is a judgment call this
script does not own. The floor is enforced; the ceiling is a reading.
"""
import math
import re
import os
import sys
from pathlib import Path

EXIT_OK, EXIT_BREACH, EXIT_MALFORMED, EXIT_IO = 0, 1, 2, 3

# Both patterns are literal and fully anchored via fullmatch(); no ledger field is
# ever interpolated into a pattern, so no input can widen what these accept.
TAG_RE = re.compile(r"(tactical|strategic)")
EVIDENCE_RE = re.compile(
    r"\s*(?P<metric>[A-Za-z][A-Za-z0-9_.]*)\s*=\s*"
    r"(?P<before>-?\d+(?:\.\d+)?)\s*->\s*(?P<after>-?\d+(?:\.\d+)?)\s*"
)


def die(msg: str, code: int) -> None:
    print(f"strategic-share: {msg}", file=sys.stderr)
    sys.exit(code)


def usage(msg: str) -> None:
    die(f"{msg}\n{__doc__}", EXIT_IO)


def parse_args(argv):
    path, floor, ceiling = None, 10.0, 20.0
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--floor", "--ceiling"):
            if i + 1 >= len(argv):
                usage(f"{arg} needs a percent value")
            try:
                value = float(argv[i + 1])
            except ValueError:
                usage(f"{arg} must be numeric, got {argv[i + 1]!r}")
            if not math.isfinite(value) or not 0.0 <= value <= 100.0:
                usage(f"{arg} must be a percent in 0..100, got {argv[i + 1]!r}")
            floor, ceiling = (value, ceiling) if arg == "--floor" else (floor, value)
            i += 2
        elif arg in ("-h", "--help"):
            usage("manual follows (printing the manual is never a verdict)")
        elif arg.startswith("-"):
            usage(f"unknown flag {arg!r}")
        elif path is None:
            path, i = arg, i + 1
        else:
            usage("at most one ledger path")
    if floor > ceiling:
        usage(f"floor {floor} exceeds ceiling {ceiling}")
    return path, floor, ceiling


def read_lines(path):
    if path is None:
        return sys.stdin.read().splitlines()
    try:
        return Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as err:
        usage(f"cannot read ledger {path!r}: {err}")


def check_evidence(text):
    if not text or text == "-":
        return False, "no before/after evidence recorded"
    match = EVIDENCE_RE.fullmatch(text)
    if not match:
        return False, f"evidence not in metric=before->after form: {text!r}"
    before, after = float(match["before"]), float(match["after"])
    if not (math.isfinite(before) and math.isfinite(after)):
        return False, f"non-finite metric values: {text!r}"
    if before == after:
        return False, f"no delta ({match['metric']} {before:g} -> {after:g})"
    return True, f"{match['metric']} {before:g} -> {after:g}"


def parse_rows(lines):
    rows, comments = [], 0
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        # Narrow, on purpose: a comment is a RAW '#' in column 1 AND no tab on the
        # line. A '#'-leading line carrying tab fields is a data row (issue-numbered
        # item), so it cannot vanish from numerator and denominator unnoticed; an
        # indented '# note' falls through to the field count and dies EXIT_MALFORMED.
        if line.startswith("#") and "\t" not in line:
            comments += 1
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            parts.append("")
        if len(parts) != 4:
            die(f"line {n}: expected 3 or 4 tab-separated fields, got {len(parts)}", EXIT_MALFORMED)
        item, tag, minutes_s, evidence = (p.strip() for p in parts)
        if not item:
            die(f"line {n}: empty item name", EXIT_MALFORMED)
        if not TAG_RE.fullmatch(tag.lower()):
            die(f"line {n}: tag must be tactical or strategic, got {tag!r}", EXIT_MALFORMED)
        try:
            minutes = float(minutes_s)
        except ValueError:
            die(f"line {n}: minutes must be numeric, got {minutes_s!r}", EXIT_MALFORMED)
        if not math.isfinite(minutes) or minutes <= 0:
            die(f"line {n}: minutes must be positive and finite, got {minutes_s!r}", EXIT_MALFORMED)
        rows.append((item, tag.lower(), minutes, evidence))
    if not rows:
        die("no data rows — an empty ledger cannot pass", EXIT_MALFORMED)
    return rows, comments


def main(argv) -> int:
    path, floor, ceiling = parse_args(argv)
    rows, comments = parse_rows(read_lines(path))
    total = evidenced = discounted = 0.0
    unevidenced = 0
    for item, tag, minutes, evidence in rows:
        total += minutes
        if tag == "tactical":
            print(f"tactical    {minutes:>6.0f}m  {'':<34}  {item}")
            continue
        ok, detail = check_evidence(evidence)
        if ok:
            evidenced += minutes
            print(f"STRATEGIC   {minutes:>6.0f}m  {detail:<34}  {item}")
        else:
            discounted += minutes
            unevidenced += 1
            print(f"UNEVIDENCED {minutes:>6.0f}m  {detail:<34}  {item}")
    # Cross-multiplied comparison: no division, so the floor is exact at the boundary.
    if evidenced * 100.0 < floor * total:
        verdict = "UNDER"
    elif evidenced * 100.0 > ceiling * total:
        verdict = "OVER"
    else:
        verdict = "IN-BAND"
    share = evidenced / total * 100.0
    tail = f", {discounted:.0f}m unevidenced discounted" if discounted else ""
    print(
        f"strategic share {share:.2f}% {verdict} (band {floor:g}-{ceiling:g}%); "
        f"{evidenced:.0f}m evidenced of {total:.0f}m{tail}"
    )
    if comments:
        print(f"{comments} line(s) skipped as comments (raw '#' in column 1, no tab)")
    if unevidenced:
        print(f"{unevidenced} strategic row(s) claimed without before/after evidence")
    return EXIT_BREACH if (unevidenced or verdict == "UNDER") else EXIT_OK


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython flushes
    # the std streams after main() returns, and if that flush raises — a pipe whose reader
    # has already gone, which is the ordinary `gate.py … | head` idiom — it REPLACES the
    # status this script chose with 120, a code no table here names. An unhandled exception
    # is the other leak, and the worse one: it exits 1, and 1 is a VERDICT here, so a crash
    # would be read as a real finding about the code under test.
    try:
        _code = main(sys.argv[1:])
    except SystemExit as _exc:                 # argparse raises this from inside
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:
        _code = 3
    except BaseException as _exc:              # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
        _code = 3
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 3
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
