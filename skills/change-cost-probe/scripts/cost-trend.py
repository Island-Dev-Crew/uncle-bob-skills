#!/usr/bin/env python3
"""cost-trend.py - is a change getting more expensive in THIS repo? (C21, C2)

Reads TSV rows (a file argument or stdin): story <TAB> cost
`cost` is what ONE story cost to push through your pipeline end to end, in the
unit named by --unit (minutes or tokens). One row per story, in the order
declared by --order.

The scanner compares the mean of the last --window stories against the
--baseline stories immediately before them. A climb past --climb is the alarm:
the price of change is rising, which is what accumulating mess looks like from
outside the code (C2). A flat or falling curve is the $1-house premise holding
in your repo rather than being asserted at you (C21).

Exit codes - the only code this scanner CHOOSES that means rising cost is 1:
  0  STEADY  - recent mean is at or below --climb x the baseline mean
  1  RISING  - the climb rule breached
  2  everything else, fail closed: usage errors, an unreadable or undecodable
     input, a leading byte-order mark, a malformed row, a '#word' story id
     (a '#'-leading id must be '#' followed by digits, so an annotation carrying
     a TAB can never be counted as a story), a '#'-digit line with a second
     token but no TAB (a story row whose TAB became spaces, which must not be
     eaten by the comment rule), a duplicate story, a
     non-positive / non-finite / out-of-range cost, insufficient history, a
     non-finite threshold, a closed stdin, a closed or dead output channel, and
     any otherwise-unhandled exception (KeyboardInterrupt included).
A signal that kills the interpreter outright (SIGTERM, SIGKILL) never runs this
code at all; the shell reports those as 143 and 137 and they are not verdicts.

--cheap is an ADVISORY label: it classifies the recent mean for planning depth
and is not part of the verdict - no value of it turns STEADY into RISING or back.
A non-finite or non-positive --cheap is refused as a usage error, like any other.
"""
import argparse
import math
import os
import re
import sys
import unicodedata

# A story id is one ASCII token, ticket-key shaped. Anchored end to end, and
# deliberately ASCII-only: a non-ASCII id is REFUSED rather than normalized, so
# NFC vs NFD (routine on macOS) can never reach the duplicate join and quietly
# split one story into two rows.
ID_RE = re.compile(r"\A[A-Za-z0-9._@/:+#-]{1,64}\Z")
# A '#'-leading id is the ticket-number idiom and nothing else: '#312' is a story,
# '#note1' is not. Without this, '#note1<TAB>20' reads as an annotation to a human
# and as a data row to the scanner, and five such lines can push a real climb out
# of the window. Used again in the comment branch for the mirror case: '#301  60'
# reads as an annotation to this scanner and as a data row to a human, and five
# such lines can drop a real climb out of the file. Disjoint by shape both ways.
HASH_ID_RE = re.compile(r"\A#[0-9]{1,63}\Z")
MAX_COST = 1e9


def channels_ok() -> bool:
    """True only when a verdict can actually be delivered.

    With fd 1 or 2 closed at exec, CPython sets the stream to None: print() goes
    quiet and the final flush raises. Checked BEFORE argparse so --help and a
    usage error are covered by the same rule instead of falling through to the
    interpreter's default exit code.
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            return False
        try:
            stream.fileno()
        except BaseException:
            return False
    return True


def die(msg: str, code: int = 2) -> None:
    """Every refusal exits 2. Non-raising by construction (except SystemExit)."""
    try:
        print(f"cost-trend: {msg}", file=sys.stderr)
    except BaseException:
        pass
    sys.exit(code)


def fmt_pair(a: float, b: float):
    """Format two numbers so the printed comparison cannot contradict the verdict.

    Two-decimal rounding turns 1.5000001 > 1.5 into the line '1.50x > 1.50x',
    which reads as a gate contradicting itself. Widen precision until the two
    strings differ; equal values are formatted plainly because there is nothing
    to contradict.
    """
    if a == b:
        return f"{a:.2f}", f"{b:.2f}"
    for p in range(2, 18):
        sa, sb = f"{a:.{p}f}", f"{b:.{p}f}"
        if sa != sb:
            return sa, sb
    return repr(a), repr(b)


def read_input(path):
    """Return the input as text, decoded strictly as UTF-8 by this script.

    Bytes are read and decoded here rather than through a text-mode handle so
    the caller's locale cannot change a verdict.
    """
    if path:
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            die(f"cannot read {path!r}: {exc}")
    else:
        stdin = sys.stdin
        buf = getattr(stdin, "buffer", None) if stdin is not None else None
        if buf is None:
            die("stdin is closed or has no byte channel - nothing to probe")
        try:
            data = buf.read()
        except OSError as exc:
            die(f"cannot read stdin: {exc}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        die(f"input is not valid UTF-8: {exc}")


def parse_rows(text: str):
    """Parse TSV rows. No line carrying data is dropped: every line is a row, a
    comment, a blank, or a refusal, and rows/comments/blanks are all counted so a
    line-count reconcile against the capture can actually be completed."""
    if text.startswith("\ufeff"):
        die("input begins with a UTF-8 byte-order mark (U+FEFF) - remove the mark, not the line")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # A trailing newline is a terminator, not a line: drop the empty tail element
    # so rows + comments + blanks equals the capture's own line count exactly and
    # the reconcile at the end of the island can be done by counting.
    if lines and lines[-1] == "":
        lines.pop()
    rows = []
    skipped = 0
    blank = 0
    seen = {}
    for n, line in enumerate(lines, 1):
        if not line.strip():
            blank += 1
            continue
        # Anchored comment rule: a comment holds NO TAB and starts with '#'.
        # A story id may legitimately be '#1234', and such a row is counted.
        if "\t" not in line and line.lstrip().startswith("#"):
            # Symmetric with the TAB direction below. '#301    60' is a data row
            # whose TAB became spaces - editor expandtab, a hand-typed row, a
            # terminal copy-paste, a markdown round-trip - and skipping it as a
            # comment drops a story silently while the printed line count still
            # reconciles. Refuse instead: a dropped row is a false green.
            head = line.split(None, 1)
            if len(head) == 2 and HASH_ID_RE.match(head[0]):
                die(f"line {n}: {head[0]!r} is a ticket-number story id but this line "
                    f"carries no TAB - a data row whose TAB became spaces would be read "
                    f"as a comment here; restore the TAB, or renumber the annotation")
            skipped += 1
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            die(f"line {n}: expected 2 tab-separated fields (story, cost), got {len(parts)}")
        story, cost_s = parts[0].strip(), parts[1].strip()
        if not ID_RE.match(story):
            die(f"line {n}: story id {story!r} is not one ASCII token [A-Za-z0-9._@/:+#-] of 1..64 chars")
        if story.startswith("#") and not HASH_ID_RE.match(story):
            die(f"line {n}: a '#'-leading story id must be '#' followed by 1..63 digits "
                f"(the ticket-number idiom), got {story!r} - a '#word' row reads as an "
                f"annotation to a human and as a story to this scanner")
        try:
            cost = float(cost_s)
        except ValueError:
            die(f"line {n}: cost must be numeric, got {cost_s!r}")
        if not math.isfinite(cost):
            die(f"line {n}: cost must be finite, got {cost_s!r}")
        if not 0 < cost <= MAX_COST:
            die(f"line {n}: cost must be in (0, {MAX_COST:.0f}], got {cost!r}")
        key = unicodedata.normalize("NFC", story).casefold()
        if key in seen:
            die(f"line {n}: story {story!r} already listed on line {seen[key]} - one row per story")
        seen[key] = n
        rows.append((story, cost))
    if not rows:
        die("no data rows - an empty probe cannot pass")
    return rows, skipped, blank


def positive_finite(value: float, flag: str) -> float:
    """Reject nan and inf explicitly: `nan <= 0` is False, so a bare guard lets a
    non-finite threshold through and then every comparison against it is False -
    a silently disabled rule wearing a green verdict."""
    if not math.isfinite(value) or value <= 0:
        die(f"{flag} must be a positive finite number, got {value!r}", code=2)
    return value


def main() -> int:
    if not channels_ok():
        return 2
    ap = argparse.ArgumentParser(
        prog="cost-trend.py",
        description="Trend the measured cost of change per story (C21, C2).",
    )
    ap.add_argument("ledger", nargs="?", help="TSV file (default: stdin)")
    ap.add_argument("--order", choices=("oldest-first", "newest-first"), required=True,
                    help="row order of the capture; there is no default, because a "
                         "reversed climb reads as a fall")
    ap.add_argument("--unit", choices=("minutes", "tokens"), required=True,
                    help="unit of the cost column; labels the verdict, does not validate it")
    ap.add_argument("--window", type=int, default=5, help="recent stories to average (default 5)")
    ap.add_argument("--baseline", type=int, default=10,
                    help="stories immediately before the window (default 10)")
    ap.add_argument("--climb", type=float, default=1.5,
                    help="recent/baseline ratio above which cost is RISING (default 1.5)")
    ap.add_argument("--cheap", type=float, default=None,
                    help="ADVISORY planning-depth label: recent mean at or below this is CHEAP. "
                         "Not part of the verdict; a non-finite value is refused.")
    args = ap.parse_args()

    if args.window < 1:
        die(f"--window must be at least 1, got {args.window}")
    if args.baseline < 1:
        die(f"--baseline must be at least 1, got {args.baseline}")
    climb = positive_finite(args.climb, "--climb")
    cheap = None if args.cheap is None else positive_finite(args.cheap, "--cheap")

    rows, skipped, blank = parse_rows(read_input(args.ledger))
    if args.order == "newest-first":
        rows.reverse()

    need = args.window + args.baseline
    if len(rows) < need:
        die(f"insufficient history: {len(rows)} stories, need window+baseline = {need}")

    recent = [c for _, c in rows[-args.window:]]
    base = [c for _, c in rows[-need:-args.window]]
    r_mean = sum(recent) / len(recent)
    b_mean = sum(base) / len(base)
    ratio = r_mean / b_mean
    rising = ratio > climb

    r_s, c_s = fmt_pair(ratio, climb)
    verdict = "RISING" if rising else "STEADY"
    op = ">" if rising else "<="
    print(f"{verdict}  unit={args.unit}  baseline({args.baseline})={b_mean:.2f}  "
          f"recent({args.window})={r_mean:.2f}  climb {r_s}x {op} {c_s}x")
    print(f"parsed {len(rows)} rows, skipped {skipped} comment lines, {blank} blank")
    if cheap is None:
        print("planning-depth: undeclared (--cheap not given)")
    else:
        m_s, k_s = fmt_pair(r_mean, cheap)
        label = "CHEAP (fiddle beats plan)" if r_mean <= cheap else "PRICEY (that is data about the codebase)"
        print(f"planning-depth: {label} - recent mean {m_s} {args.unit} "
              f"vs --cheap {k_s} [advisory, not part of the verdict]")
    return 1 if rising else 0


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
