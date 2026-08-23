#!/usr/bin/env python3
"""fleet-cost.py - price the coordination surface of an agent fleet.

Usage: python3 fleet-cost.py PLAN-FILE
       python3 fleet-cost.py --help      (-h is accepted as the same flag)

Reads a four-line fleet plan and answers exactly one question: does the LAST
agent in the proposed fleet still reduce elapsed time, or does it only add
communication paths? Brooks's law, computed.

Model (exact rational arithmetic, no floating point in any verdict):

    elapsed(n) = S * ((1 - p) + p / n)  +  h * n * (n - 1) / 2

    S = serial_minutes    the work if one agent did all of it
    p = partitionable     the share of it that splits with no shared context
    h = handoff_minutes   reconciliation cost per communication path
    n = fleet             number of agents

The first term is the partition term - partitionable work divides by n, work
needing shared context does not. The second term is the pair count of a set of
n, which is the coordination surface. elapsed() is convex in n (the partition
term falls at a decreasing rate, the pair term rises at an increasing rate), so
the first n whose successor costs more is the global optimum.

PLAN FILE FORMAT (strict; every deviation is exit 2, nothing is dropped):
  A regular file of at most 64 KiB. UTF-8, with or without a BOM.
  Lines are separated by LF, CRLF or CR - and by nothing else. U+2028, U+2029,
  U+0085, form feed, vertical tab and the file/group/record separators are NOT
  line boundaries here, which is why a '#' line cannot smuggle a key past this
  parser: whatever follows one of those characters stays on the comment line.
  Blank lines, and lines whose first character after leading spaces and tabs is
  '#', are ignored whole - a comment line is never split or parsed.
  Every other line is exactly two tokens separated by spaces and/or tabs,
  `key value`. Any other whitespace character stays inside its token, so it is
  refused as an unknown key or a malformed value rather than acting as a break.
  All four keys are required, each exactly once. No other key is accepted.
    serial_minutes   decimal, greater than 0
    partitionable    decimal, 0 to 1 inclusive
    handoff_minutes  decimal, 0 or more
    fleet            whole number, 1 to 4096 inclusive
  A value token is at most 32 characters and matches [0-9]+(.[0-9]+)? end to
  end - which is why 'nan', 'inf', '1e9', '-1', '1_0' and '3/7' are refused
  rather than parsed.

EXIT CODES (the complete set this script can return):
  0  the proposed fleet still pays - the last agent reduces elapsed time.
     Also returned by --help (or -h) on a working stdout.
  1  Brooks - the last agent does not reduce elapsed time (a tie counts as
     not paying; the agent bought nothing and added a path).
  2  anything that is not a verdict - usage error, a path that is not a
     regular file (directory, FIFO, /dev/zero and other character devices),
     a plan over 64 KiB, unreadable file, decode error, malformed line,
     unknown key, duplicate key, missing key, out-of-range value, dead output
     stream, internal failure.

Every input reaches one of those three codes: the path is stat'd and refused
unless it is a regular file, and the read is capped, so there is no input class
that runs forever instead of returning a code.
"""
import os
import re
import stat
import sys
from fractions import Fraction

USAGE = "usage: python3 fleet-cost.py PLAN-FILE"

KEYS = ("serial_minutes", "partitionable", "handoff_minutes", "fleet")
VALUE_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?")
MAX_TOKEN = 32
MAX_FLEET = 4096
MAX_BYTES = 64 * 1024

# Line boundaries, enumerated. str.splitlines() would additionally break on
# \x0b \x0c \x1c \x1d \x1e \x85 U+2028 U+2029, so a '#' comment carrying any
# of those would have its tail parsed as live configuration - a false green.
LINE_RE = re.compile(r"\r\n|\r|\n")
# Token separators, enumerated. str.split() would additionally break on every
# Unicode space, so NBSP and friends would silently act as a separator.
FIELD_RE = re.compile(r"[ \t]+")


def fmt(fr):
    """Round an exact Fraction to 2 decimals using integer arithmetic only.

    No float() anywhere: a float conversion could overflow on a large input and
    would put a rounded value where an exact one belongs. Verdicts never read
    this string - it is display only, and the caller prints the exact ratio
    whenever rounding would hide a non-zero difference.
    """
    scaled = fr * 100
    q, r = divmod(scaled.numerator, scaled.denominator)  # floor; 0 <= r < denom
    if 2 * r >= scaled.denominator:
        q += 1
    sign = "-" if q < 0 else ""
    q = abs(q)
    return f"{sign}{q // 100}.{q % 100:02d}"


def parse(path):
    """Return (values dict, error string). Exactly one of the two is falsy."""
    try:
        st = os.stat(path)
    except OSError as exc:
        return None, f"cannot read plan '{path}': {exc}"
    if not stat.S_ISREG(st.st_mode):
        # A directory, FIFO, socket or character device is not a plan. /dev/zero
        # would otherwise be read until memory ran out, which is a hung CI job
        # rather than a refusal - and a hang is not one of the three exit codes.
        return None, f"plan '{path}' is not a regular file"
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError as exc:
        return None, f"cannot read plan '{path}': {exc}"
    if len(raw) > MAX_BYTES:
        return None, f"plan '{path}' exceeds {MAX_BYTES} bytes"
    try:
        text = raw.decode("utf-8-sig")  # tolerates a UTF-8 BOM, refuses UTF-16
    except UnicodeDecodeError as exc:
        return None, f"plan '{path}' is not UTF-8: {exc}"

    seen = {}
    for lineno, line in enumerate(LINE_RE.split(text), 1):  # LF, CRLF and CR only
        stripped = line.strip(" \t")
        if not stripped:
            continue
        if stripped.startswith("#"):
            # Full-line comments only, and the whole line really is the comment:
            # LINE_RE breaks on LF/CRLF/CR alone, so no exotic separator can end
            # this comment early and hand the remainder to the parser. No
            # trailing-comment stripping either: every legal value is numeric,
            # so '#' can never open one, and a '#' anywhere else stays part of a
            # token and is refused below.
            continue
        parts = FIELD_RE.split(stripped)
        if len(parts) != 2:
            return None, f"line {lineno}: expected 'key value', got {len(parts)} token(s)"
        key, tok = parts
        if key not in KEYS:
            return None, f"line {lineno}: unknown key '{key}' (accepted: {', '.join(KEYS)})"
        if key in seen:
            return None, f"line {lineno}: duplicate key '{key}'"
        if len(tok) > MAX_TOKEN:
            return None, f"line {lineno}: value for '{key}' exceeds {MAX_TOKEN} characters"
        if not VALUE_RE.fullmatch(tok):
            return None, (f"line {lineno}: value '{tok}' for '{key}' is not a plain "
                          "non-negative decimal")
        if key == "fleet":
            if "." in tok:
                return None, f"line {lineno}: fleet must be a whole number, got '{tok}'"
            n = int(tok)
            if not 1 <= n <= MAX_FLEET:
                return None, f"line {lineno}: fleet must be 1..{MAX_FLEET}, got {n}"
            seen[key] = n
            continue
        val = Fraction(tok)
        if key == "serial_minutes" and val <= 0:
            return None, f"line {lineno}: serial_minutes must be greater than 0"
        if key == "partitionable" and not 0 <= val <= 1:
            return None, f"line {lineno}: partitionable must be 0..1, got {tok}"
        seen[key] = val

    missing = [k for k in KEYS if k not in seen]
    if missing:
        return None, f"plan '{path}' is missing required key(s): {', '.join(missing)}"
    return seen, ""


def elapsed(plan, n):
    """Exact elapsed minutes for a fleet of n. n is a positive int."""
    S = plan["serial_minutes"]
    p = plan["partitionable"]
    h = plan["handoff_minutes"]
    return S * ((1 - p) + p / n) + h * (n * (n - 1)) / 2


def crossover(plan):
    """Smallest n whose successor costs at least as much, or None within cap.

    elapsed() is convex in n, so the first non-improving step is the global
    optimum; the walk never needs to look past it.
    """
    prev = elapsed(plan, 1)
    for n in range(1, MAX_FLEET):
        nxt = elapsed(plan, n + 1)
        if nxt >= prev:
            return n
        prev = nxt
    return None


def main():
    # A dead output stream is not a verdict. When fd 1 or fd 2 is already closed
    # at process start CPython sets the stream to None and print() becomes a
    # documented silent no-op - nothing raises, so without this guard a verdict
    # would be "reported" into an empty log and a CI capture would read exit 0
    # against zero bytes. Placed before --help so the help path is covered too.
    if sys.stdout is None or sys.stderr is None:
        return 2
    argv = sys.argv[1:]
    if len(argv) == 1 and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if len(argv) != 1 or argv[0].startswith("-"):
        print(USAGE, file=sys.stderr)
        print("error: expected exactly one plan file", file=sys.stderr)
        return 2

    plan, err = parse(argv[0])
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    n = plan["fleet"]
    paths = n * (n - 1) // 2
    here = elapsed(plan, n)
    print(f"plan       serial={fmt(plan['serial_minutes'])}m "
          f"partitionable={fmt(plan['partitionable'])} "
          f"handoff={fmt(plan['handoff_minutes'])}m/path fleet={n}")
    print(f"paths      {paths} communication path(s) at fleet {n}  [n(n-1)/2]")

    opt = crossover(plan)
    if opt:
        print(f"crossover  fleet {opt} is the last size that still pays")
    else:
        print(f"crossover  none within {MAX_FLEET} - the pair term has not caught the "
              "partition gain yet")

    if n == 1:
        print(f"PAYS       fleet 1 has no coordination surface  elapsed={fmt(here)}m")
        return 0

    before = elapsed(plan, n - 1)
    delta = here - before
    shown = fmt(delta)
    # A rounded message must never be the only basis on offer: when rounding
    # hides a non-zero difference, print the exact ratio the verdict used.
    exact = "" if delta == 0 or shown.lstrip("-") != "0.00" else \
        f"  [exact delta {delta.numerator}/{delta.denominator}]"
    print(f"elapsed    fleet {n - 1}: {fmt(before)}m -> fleet {n}: {fmt(here)}m  "
          f"(delta {'+' if delta > 0 else ''}{shown}m){exact}")

    if delta >= 0:
        print(f"BROOKS     fleet {n} does not pay - agent {n} adds surface, "
              f"not progress{exact}")
        return 1
    print(f"PAYS       fleet {n} pays - agent {n} saves {fmt(-delta)}m{exact}")
    return 0


if __name__ == "__main__":
    try:
        _code = main()
    except SystemExit as _exc:          # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except BaseException as _exc:       # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
