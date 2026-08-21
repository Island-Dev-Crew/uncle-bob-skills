#!/usr/bin/env python3
"""tornado-scan.py — files-touched-per-change trend alarm (change amplification).

Input: TSV rows, one row per change (commit, squashed PR, or story):

    change_id<TAB>files_touched

Row order must be declared: `--order oldest-first` (`git log --reverse`) or
`--order newest-first` (git's native order). There is no default — an
undeclared order exits 2, because a reversed climb reads as a fall and the
rows carry no signal that would let the scanner notice.

Comment rule (anchored, so no data row can vanish): a line is a comment only
when it contains NO TAB and its first non-space character is '#'. Any line
holding a TAB is data, so a PR-style id (`#1234<TAB>7`) is counted, never
dropped — a silently deleted row is a false green. Blank lines are skipped.
Every verdict prints `parsed N rows, skipped M`, so a loss can never be
invisible. Change ids must be unique under one documented key (NFC +
casefold); a log that lists a change twice is malformed, not averaged twice.

Verdict:
    recent = mean files_touched over the last --window changes
    base   = mean files_touched over the --baseline changes just before them
    ALARM when  recent / base > --climb    (the trend is climbing)
            or  recent        > --ceiling  (absolute backstop)
    Exactly-at passes, for both parameters.

Exit: 0 no alarm, 1 ALARM, 2 usage / IO / malformed or undecodable input /
insufficient history (fail closed — a trend that cannot be computed never
passes, and only 1 ever means tornado). Every error path exits 2, including
an unexpected exception, an out-of-range count, and a channel that cannot
carry the verdict: a closed stdin AND a closed stdout both exit 2, checked
before argparse so --help is covered too. Exit 1 is reserved for a verdict
this scanner actually computed and delivered from its first line onward.
A reader that hangs up mid-stream (`| head -1`) is the one delivery failure
that keeps the computed code: the verdict was already on the wire.
"""
import argparse
import math
import os
import re
import sys
import unicodedata

# Anchored: a change id is one token, never a whole line of prose. '#' is in
# the class because PR ids are conventionally written '#1234' — they are data.
ID_RE = re.compile(r"\A[A-Za-z0-9._@/:+#-]{1,64}\Z")
USAGE = 2
# A change touching more than a million files is a corrupted capture, not a
# repo. Bounded here so arithmetic downstream can never raise OverflowError
# and surface as exit 1 — the code reserved for a real tornado.
MAX_FILES = 10**6


def emit_err(msg: str) -> None:
    """Write one diagnostic to stderr, tolerating a closed or broken stderr.
    `print(file=None)` silently falls back to stdout, which would drop an
    error message onto the verdict channel; a raising stderr would escape a
    handler and leave the interpreter at exit 1, the code reserved for ALARM.
    Neither is allowed, so this never raises and never uses stdout."""
    try:
        if sys.stderr is not None:
            print(msg, file=sys.stderr)
            sys.stderr.flush()
    except BaseException:  # noqa: BLE001 — a diagnostic must not become the exit code
        pass


def die(msg: str) -> None:
    emit_err(f"error: {msg}")
    raise SystemExit(USAGE)


def clip(s: str, n: int = 48) -> str:
    """Quote a field for an error message, marking any truncation — a clipped
    400-digit count must not read as a short one."""
    return repr(s) if len(s) <= n else f"{s[:n]!r}...({len(s)} chars)"


def id_key(cid: str) -> str:
    """The single documented key function for change ids: NFC + casefold.
    Two spellings that normalize to one key are one change ('A1B2' is 'a1b2');
    counting it twice would dilute a window with history that happened once.
    NFC is applied for completeness only — ID_RE is ASCII-restricted, so a
    Unicode variant (NFD from macOS) is *refused* at exit 2 rather than
    normalized. Refuse or normalize, never silently reroute."""
    return unicodedata.normalize("NFC", cid).casefold()


def parse_rows(src, where: str):
    """Parse every row or die. A malformed row is never silently dropped —
    skipping it would let a corrupted log walk the gate green. Returns
    (rows, skipped) so the caller can print what was left out."""
    if src is None:
        die(f"{where} is closed — no input channel to read")
    rows, skipped, seen = [], 0, {}
    for n, raw in enumerate(src, 1):
        line = raw.rstrip("\r\n")
        if n == 1 and line.startswith("\ufeff"):
            # A Windows editor writes a BOM without being asked. U+FEFF is not
            # whitespace to str.lstrip and not in ID_RE, so it already fails
            # closed — but as "expected 2 fields, got 1", which invites the
            # user to delete a real row. Name the mark instead. The scanner
            # does not strip it: silently editing the capture it is auditing
            # is the same move as silently dropping a row.
            die(f"{where} line 1: file begins with a UTF-8 byte-order mark; "
                f"re-save the capture without the BOM")
        if "\t" not in line:
            # Anchored comment detection: only a line that cannot be a data
            # row may be dropped, and the drop is counted and reported.
            if not line.strip() or line.lstrip().startswith("#"):
                skipped += 1
                continue
            die(f"{where} line {n}: expected 2 tab-separated fields, got 1")
        parts = line.split("\t")
        if len(parts) != 2:
            die(f"{where} line {n}: expected 2 tab-separated fields, got {len(parts)}")
        cid, files_s = parts[0].strip(), parts[1].strip()
        if not ID_RE.fullmatch(cid):
            die(f"{where} line {n}: change id {cid!r} is not a single id token")
        try:
            files = int(files_s)
        except ValueError:
            # Also the landing spot for a digit string past the interpreter's
            # int-conversion limit (~4300 digits) — a ValueError either way,
            # and either way exit 2 rather than an unhandled crash at exit 1.
            die(f"{where} line {n}: files_touched {clip(files_s)} is not an "
                f"integer within the interpreter's digit limit")
        if files < 1:
            die(f"{where} line {n}: files_touched must be >= 1, got {files}")
        if files > MAX_FILES:
            die(f"{where} line {n}: files_touched {clip(files_s)} exceeds {MAX_FILES}")
        key = id_key(cid)
        if key in seen:
            die(f"{where} line {n}: change id {cid!r} repeats line {seen[key]} "
                f"under key {key!r}; ids must be unique")
        seen[key] = n
        rows.append((cid, files))
    return rows, skipped


def mean(rows) -> float:
    return sum(f for _, f in rows) / len(rows)


def cmp_fmt(a: float, b: float):
    """Render a comparison pair so a strict inequality never prints as
    equality. Two decimals is the readable default; widen only when rounding
    would make the message contradict the comparison the verdict used
    (`recent 9.00 > 9.00` is a self-refuting ALARM line)."""
    for prec in (2, 4, 6, 9, 12):
        sa, sb = f"{a:.{prec}f}", f"{b:.{prec}f}"
        if a == b or sa != sb:
            return sa, sb, prec
    return repr(a), repr(b), 12


def positive_finite(x: float) -> bool:
    # isfinite first: NaN loses every comparison, so a bare `x <= 0` guard
    # lets NaN through and NaN then defeats both rules — the gate silently
    # off while still printing a verdict. inf disables them the same way.
    return math.isfinite(x) and x > 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="files-touched-per-change trend alarm")
    p.add_argument("path", nargs="?", help="TSV file; omit to read stdin")
    p.add_argument("--window", type=int, default=5, help="recent changes (default 5)")
    p.add_argument("--baseline", type=int, default=10, help="prior changes (default 10)")
    p.add_argument("--climb", type=float, default=1.5, help="tolerated recent/base ratio (default 1.5)")
    p.add_argument("--ceiling", type=float, default=8.0, help="tolerated recent mean (default 8.0)")
    # No default: git's native order is newest-first, so a defaulted flag would
    # read a genuine climb as a fall and exit 0. Undeclared order is a usage
    # error (argparse exits 2), never a quiet verdict.
    p.add_argument("--order", choices=("oldest-first", "newest-first"), required=True,
                   help="row order of the input; required, no default")
    return p


def main(argv=None) -> int:
    # A verdict nobody can read is not a verdict. With fd 1 closed at exec
    # (`>&-`, a daemonized runner, os.close(1) before exec) CPython sets
    # sys.stdout to None: print() becomes a silent no-op and every later
    # flush raises AttributeError, which used to escape the top-level guard
    # and leave the interpreter at exit 1 — a false tornado on a green repo.
    # Checked before argparse so --help is covered by the same rule.
    if sys.stdout is None:
        die("stdout is closed — no channel to deliver the verdict")
    # argparse exits 2 on bad flags, which is this tool's usage code already.
    args = build_parser().parse_args(argv)
    if args.window < 1 or args.baseline < 1:
        die("--window and --baseline must be >= 1")
    if not positive_finite(args.climb) or not positive_finite(args.ceiling):
        die("--climb and --ceiling must be finite and > 0 (nan/inf rejected)")

    if args.path:
        try:
            # surrogateescape, not strict: undecodable bytes must reach the
            # anchored ID_RE and die at exit 2 like every other malformed row.
            # A UnicodeDecodeError would escape the OSError guard and exit 1 —
            # indistinguishable from an ALARM.
            with open(args.path, encoding="utf-8", errors="surrogateescape") as fh:
                rows, skipped = parse_rows(fh, args.path)
        except OSError as e:
            die(f"cannot read {args.path}: {e}")
    else:
        # The same handler, forced onto stdin. Left alone, sys.stdin inherits
        # the interpreter default — surrogateescape only under PEP 540 UTF-8
        # mode, but *strict* under a normal locale such as LANG=en_US.UTF-8 —
        # so identical bytes exited 2 by file and 1 by pipe. Reconfigure makes
        # the channel irrelevant to the verdict. A closed stdin (0<&-) leaves
        # sys.stdin None; parse_rows dies at 2 rather than raising.
        try:
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(errors="surrogateescape")
            rows, skipped = parse_rows(sys.stdin, "stdin")
        except OSError as e:
            die(f"cannot read stdin: {e}")

    if args.order == "newest-first":
        rows.reverse()

    need = args.window + args.baseline
    if len(rows) < need:
        die(f"insufficient history: {len(rows)} changes, need {need} "
            f"(--window {args.window} + --baseline {args.baseline})")

    recent_rows = rows[-args.window:]
    base_rows = rows[-need:-args.window]
    recent, base = mean(recent_rows), mean(base_rows)
    ratio = recent / base  # base >= 1.0: every parsed row touches >= 1 file

    print(f"parsed {len(rows)} rows, skipped {skipped} blank/comment line(s)")
    print(f"baseline {len(base_rows):>3} changes  mean {base:.2f} files/change")
    print(f"recent   {len(recent_rows):>3} changes  mean {recent:.2f} files/change")
    for cid, files in recent_rows:
        print(f"  {cid}  {files} files")

    reasons = []
    if ratio > args.climb:
        sr, sl, p = cmp_fmt(ratio, args.climb)
        reasons.append(f"trend climbing — {recent:.{p}f} / {base:.{p}f} = {sr}x > {sl}x")
    if recent > args.ceiling:
        sr, sl, _ = cmp_fmt(recent, args.ceiling)
        reasons.append(f"absolute ceiling — recent {sr} > {sl} files/change")

    if reasons:
        for r in reasons:
            print(f"ALARM  {r}")
        print(f"tornado signature over {len(rows)} changes ({skipped} line(s) skipped), "
              f"{len(reasons)} rule(s) breached")
        return 1
    print(f"ok  no tornado signature over {len(rows)} changes ({skipped} line(s) skipped) "
          f"— {ratio:.2f}x climb, recent {recent:.2f} files/change")
    return 0


def mute_stdout() -> None:
    """Redirect stdout to /dev/null so interpreter shutdown cannot fail while
    flushing a broken pipe — that failure exits 120, a code outside this
    tool's documented set (0/1/2). Cleanup must never raise: if this function
    became the exception it would replace the verdict with the interpreter's
    own exit 1, the code reserved for ALARM. When sys.stdout is None there is
    nothing to flush at shutdown and fd 1 is not ours to reassign, so the
    only correct cleanup is none."""
    try:
        if sys.stdout is None:
            return
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    except BaseException:  # noqa: BLE001 — a cleanup step must not become the exit code
        pass


def flush_stdout() -> bool:
    """Deliver the verdict; return False if it could not be delivered. Never
    raises — a raise here lands inside an exception handler and escapes it,
    which is exactly how a cleanup step once became the exit code. The caller
    fails closed at 2 on False: an undelivered verdict is not a verdict."""
    try:
        if sys.stdout is None:
            return False
        sys.stdout.flush()
        return True
    except BaseException:  # noqa: BLE001 — a broken pipe must not become 120 or 1
        mute_stdout()
        return False


def seal_stderr() -> None:
    """Flush stderr and, on failure, point fd 2 at /dev/null.

    The mirror of `mute_stdout`, and the hole it closes is one the stdout side
    already covered: `except SystemExit: ... raise` re-raises with stderr still
    live, so a usage message written into a pipe whose reader has gone raises at
    interpreter shutdown and CPython replaces the status with 120 — a code this
    tool's documented set (0/1/2) does not contain. Never raises: a cleanup step
    that throws inside a handler becomes the exit code, the exact failure the
    handlers above were built to prevent."""
    try:
        if sys.stderr is None:
            return
        sys.stderr.flush()
    except BaseException:  # noqa: BLE001 — cleanup must not become the exit code
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
        except BaseException:  # noqa: BLE001
            pass


if __name__ == "__main__":
    # Last line of defence for the exit-code contract: any unexpected
    # exception (OverflowError, MemoryError, BrokenPipeError, KeyboardInterrupt)
    # would otherwise leave the interpreter at exit 1 — the code reserved for
    # ALARM — and a CI consumer would record a tornado the scanner never
    # computed. SystemExit passes through: it carries a real verdict, and its
    # stdout is flushed here so a delivery failure becomes 2, not 120. Every
    # statement inside these handlers is itself non-raising (emit_err,
    # flush_stdout, mute_stdout), because the round-2 hole was the cleanup
    # step raising and taking the guard down with it.
    try:
        _code = main()
    except SystemExit:
        # die() and argparse both arrive here. Deliver first: if the channel
        # cannot carry it, the run fails closed at 2 whatever code it was
        # about to raise (a `--help` nobody can read is not a help screen).
        # Seal stderr before re-raising: argparse writes its usage there, and
        # this branch leaves by `raise`, so an unsealed broken stderr raises at
        # shutdown and becomes 120 instead of the code chosen here.
        if not flush_stdout():
            seal_stderr()
            sys.exit(USAGE)
        seal_stderr()
        raise
    except BaseException as exc:  # noqa: BLE001 — deliberate, see above
        emit_err(f"error: unexpected failure: {type(exc).__name__}: {exc}")
        mute_stdout()
        seal_stderr()
        sys.exit(USAGE)
    if not flush_stdout():
        emit_err("error: stdout could not be flushed — verdict undelivered")
        seal_stderr()
        sys.exit(USAGE)
    seal_stderr()
    sys.exit(_code)
