#!/usr/bin/env python3
"""cohesion-read.py - CCP change-spread and context-fit gate over a component map.

Input is one TSV artifact (stdin, or a single file argument). Lines are split on
'\\n' alone - never str.splitlines(), which also breaks on \\x0b, \\x0c, \\x85 and
U+2028, silently turning one physical row into two. A line is a comment only when
'#' is its FIRST character (column 0, anchored on purpose); a wholly empty line is
skipped; a whitespace-only line is a record shape with empty fields and is refused
rather than dropped, because a dropped row is a false green. Three record shapes:

    commits   <TAB> total <TAB> N                # the history's own commit count
    component <TAB> NAME  <TAB> SIZE_LINES       # the component map + its size
    commit    <TAB> REF   <TAB> comp_a,comp_b    # one commit, the components it touched

SIZE_LINES and N are whole numbers of at most twelve digits; a longer digit run is
refused as input rather than converted.

Every NAME and REF is compared, joined and deduplicated by one documented key
function - key() below - and by nothing else, so one entity cannot enter twice
under two spellings (API/Router.py vs api/router.py, ./billing vs billing//, NFD
vs NFC). Two spellings that share a key are refused as a collision, never merged
or silently rerouted; forms the key will not guess at (absolute names, '..'
segments, names that reduce to nothing) are refused outright.

One commit is one row. Two independent guards make that enforceable: a REF
repeated across rows is refused, and the declared commit count must equal the
number of commit rows read - so the one-row-per-path fold a naive
`git log --name-only` produces (which flattens every fan to 1 and inflates the
denominator, turning a 75% breach into 0.0%) is refused as input even when it
mints a distinct ref per path. The gate cannot audit the declaration against the
repo; deriving `N` honestly from `git rev-list --count` is the operator's job and
stays advisory.

Two verdicts, each with one declared budget:
  * context-fit - no component may exceed --context-lines (default 1500)
  * CCP spread  - at most --spread-max-pct of commits may touch more than
                  --fan components (defaults 25 and 2)

Both budgets breach on strictly-greater, so exactly-at-budget passes.

Exit codes are distinct by meaning, and no error path may wear a verdict's code:
  0  clean - both budgets respected
  1  breach - a real verdict against real input
  2  usage, IO, or malformed/empty input - the gate refuses to render a verdict

Nothing here returns any other code. argparse's own exits arrive as SystemExit
and are converted at the tail rather than re-raised (--help exits 0, a usage
error exits 2), so their buffered text cannot escape the seal. A stream this
process cannot write - a closed stdout, or a pipe whose reader has gone - is
sealed onto os.devnull before exit (_seal below) so the interpreter's own
shutdown flush cannot raise and replace the status with 120.
"""
import argparse
import os
import re
import sys
import unicodedata

ROW = re.compile(r"^(commits|commit|component)\t([^\t]+)\t([^\t]+)$")
NAME = re.compile(r"^[A-Za-z0-9._/-]+$")
# Bounded on purpose. An unbounded digit run matches "whole number" but blows
# up in int() past CPython's 4300-digit conversion limit - a ValueError raised
# outside InputError, escaping as a traceback under exit 1, the code reserved
# for a real verdict. Twelve digits is past any real line or commit count.
SIZE = re.compile(r"^[0-9]{1,12}$")


class InputError(Exception):
    """Malformed input - exit 2, never exit 1. Bad input is not a verdict."""


def key(raw):
    """The single documented key function: NFC-normalise, split on '/', drop
    empty and '.' segments (so './a', 'a//b', 'a/' and './/A//' all reduce),
    rejoin, casefold. Nothing in this file compares two names by any other
    rule."""
    segs = unicodedata.normalize("NFC", raw).split("/")
    return "/".join(s for s in segs if s not in ("", ".")).casefold()


def ident_key(kind, lineno, raw):
    if not NAME.match(unicodedata.normalize("NFC", raw)):
        raise InputError(f"line {lineno} bad {kind} name {raw!r}")
    if raw.startswith("/"):
        raise InputError(f"line {lineno} {kind} name {raw!r} is absolute - names are relative")
    k = key(raw)
    if not k or any(seg in (".", "..") for seg in k.split("/")):
        raise InputError(f"line {lineno} {kind} name {raw!r} has no usable key")
    return k


def _whole(lineno, what, field):
    if not SIZE.match(field):
        shown = field if len(field) <= 24 else field[:24] + "..."
        raise InputError(
            f"line {lineno} {what} must be a whole number of at most 12 digits, got {shown!r}"
        )
    return int(field)


def _claim(lineno, kind, store, k, raw):
    """Refuse a second declaration of one key, naming the collision explicitly."""
    prior = store.get(k)
    if prior is None:
        return
    if prior == raw:
        raise InputError(f"line {lineno} {kind} {raw!r} declared twice")
    raise InputError(
        f"line {lineno} {kind} {raw!r} collides with {prior!r} under the documented key {k!r}"
    )


def parse(text):
    sizes, shown, commits, refs, member_raw = {}, {}, [], {}, {}
    declared_total = None
    for lineno, raw in enumerate(text.split("\n"), 1):
        line = raw[:-1] if raw.endswith("\r") else raw
        if line == "" or line.startswith("#"):
            continue
        if not line.strip():
            raise InputError(f"line {lineno} is whitespace only - a dropped row is a false green")
        m = ROW.match(line)
        if not m:
            raise InputError(f"line {lineno} is not 'commits|component|commit<TAB>NAME<TAB>FIELD'")
        kind, ident, field = m.group(1), m.group(2).strip(), m.group(3).strip()
        if kind == "commits":
            if key(ident) != "total":
                raise InputError(f"line {lineno} commits row must read 'commits<TAB>total<TAB>N'")
            if declared_total is not None:
                raise InputError(f"line {lineno} commit count declared twice")
            declared_total = _whole(lineno, "commit count", field)
        elif kind == "component":
            k = ident_key("component", lineno, ident)
            size = _whole(lineno, "size", field)
            _claim(lineno, "component", shown, k, ident)
            sizes[k], shown[k] = size, ident
        else:
            members = [p.strip() for p in field.split(",")]
            if not members or any(not p for p in members):
                raise InputError(f"line {lineno} commit {ident!r} has an empty component entry")
            mkeys = set()
            for p in members:
                mk = ident_key("component", lineno, p)
                member_raw.setdefault(mk, p)
                mkeys.add(mk)
            rk = ident_key("commit ref", lineno, ident)
            _claim(lineno, "commit", refs, rk, ident)
            refs[rk] = ident
            commits.append((ident, sorted(mkeys)))
    if not sizes:
        raise InputError("no component rows - an empty map cannot pass")
    if not commits:
        raise InputError("no commit rows - an unmeasured history cannot pass")
    if declared_total is None:
        raise InputError("no 'commits<TAB>total<TAB>N' row - the commit count must be declared")
    if declared_total != len(commits):
        raise InputError(
            f"declared {declared_total} commits but read {len(commits)} commit rows - one commit "
            "is one row; a per-path fold mints one row per path and destroys the fan"
        )
    for ref, mkeys in commits:
        for k in mkeys:
            if k not in sizes:
                raise InputError(f"commit {ref!r} touches undeclared component {member_raw[k]!r}")
    return sizes, shown, commits


def report(sizes, shown, commits, context_lines, fan, spread_max_pct):
    oversize = []
    for k in sorted(sizes):
        size = sizes[k]
        over = size > context_lines
        print(f"{'OVER' if over else 'ok  '}  {size:>6} lines  {shown[k]}")
        if over:
            oversize.append(shown[k])
    spread = [ref for ref, members in commits if len(members) > fan]
    total = len(commits)
    pct = (100 * len(spread)) / total
    print(f"context-fit  {len(oversize)}/{len(sizes)} components over {context_lines} lines")
    print(f"CCP spread   {len(spread)}/{total} commits touch more than {fan} components ({pct:.1f}%)")
    for ref in spread[:10]:
        print(f"  spread commit {ref}")
    # Integer comparison - no float rounding decides a verdict, and the breach
    # line prints the integer basis alongside the rounded percent so a printed
    # "25.0%" can never look like it agrees with a budget it exceeded.
    spread_breach = 100 * len(spread) > spread_max_pct * total
    if oversize:
        print(f"BREACH context-fit - over {context_lines} lines - {', '.join(oversize)}")
    if spread_breach:
        print(
            f"BREACH CCP spread - {len(spread)}/{total} commits ({pct:.1f}%) "
            f"over budget {spread_max_pct}%"
        )
    return bool(oversize) or spread_breach


def _err(msg):
    """Diagnostics go to stderr and nowhere else.

    builtins.print treats file=None as "write to sys.stdout", and CPython sets
    sys.stderr to None when fd 2 is closed (`2>&-`) - so a plain
    print(..., file=sys.stderr) redirects the diagnostic into stdout, the
    captured evidence stream, where an io-error line reads as gate output.
    Refuse the fallback: with no stderr the message is dropped and only the
    exit code carries the refusal. A stderr that exists but cannot be written
    (broken pipe) is dropped the same way; the code still says 2.
    """
    try:
        if sys.stderr is not None:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
    except (OSError, ValueError):
        pass
    return 2


def _seal(stream, fallback_fd):
    """Flush a stream we own, and on failure point its fd at os.devnull.

    Returns True if everything this process wrote actually landed. A pipe whose
    reader has gone - the ordinary `| head -1` CI idiom - fails at flush; if the
    failure is left to interpreter shutdown, CPython prints "Exception ignored
    while flushing sys.stdout" and overrides the exit status with 120, a fourth
    code outside this gate's law that would swallow a real verdict. Sealing the
    fd onto devnull lets the shutdown flush succeed, so the status the gate
    chose is the status the caller sees.
    """
    if stream is None:
        return True
    try:
        stream.flush()
        return True
    except (OSError, ValueError):
        pass
    try:
        fd = stream.fileno()
    except (OSError, ValueError, AttributeError):
        fd = fallback_fd
    try:
        null = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(null, fd)
        finally:
            os.close(null)
    except (OSError, ValueError):
        pass
    try:
        stream.flush()
    except (OSError, ValueError):
        pass
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="CCP spread and context-fit gate")
    ap.add_argument("path", nargs="?", help="TSV map file (default stdin)")
    ap.add_argument("--context-lines", type=int, default=1500)
    ap.add_argument("--fan", type=int, default=2)
    ap.add_argument("--spread-max-pct", type=int, default=25)
    args = ap.parse_args(argv)
    if args.context_lines < 1 or args.fan < 1 or not 0 <= args.spread_max_pct <= 100:
        return _err("usage error - budgets must be positive and spread-max-pct in 0..100")
    # A verdict nobody can read is not a verdict: refuse before computing one.
    if sys.stdout is None:
        return _err("io error - stdout is closed, no verdict can be rendered")
    try:
        if args.path:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
        else:
            # CPython sets sys.stdin to None when fd 0 is closed (`0<&-`); the
            # AttributeError that follows used to escape as exit 1.
            if sys.stdin is None:
                return _err("io error - stdin is closed")
            text = sys.stdin.read()
    except (OSError, UnicodeDecodeError, ValueError) as e:
        # UnicodeDecodeError subclasses ValueError, not OSError: without it an
        # undecodable map escapes as a traceback and exits 1, the code reserved
        # for a real verdict against real input.
        return _err(f"io error - {e}")
    # One leading U+FEFF is an encoding artifact, not content: every Windows
    # editor writes it and it is never part of a field. Strip exactly one, at
    # position 0 only - a U+FEFF anywhere else stays in the line and is refused
    # by NAME/ROW like any other control character.
    if text.startswith("\ufeff"):
        text = text[1:]
    try:
        sizes, shown, commits = parse(text)
    except InputError as e:
        return _err(f"input error - {e}")
    try:
        breach = report(sizes, shown, commits, args.context_lines, args.fan, args.spread_max_pct)
    except OSError as e:
        # A pipe whose reader has gone mid-report. Partial output is not a
        # verdict, so this is an io error, not the breach we were computing.
        return _err(f"io error - the verdict could not be written to stdout - {e}")
    return 1 if breach else 0


if __name__ == "__main__":
    try:
        code = main()
    except SystemExit as exc:
        # argparse's usage error and --help leave through here. Re-raising them
        # skips the seal below, and their buffered text then fails at
        # interpreter shutdown on a broken stdout/stderr pipe, which replaces
        # the status with 120. Convert instead, and clamp anything outside the
        # three documented codes so the exit-code law keeps partitioning.
        raw = exc.code
        code = 0 if raw is None else (raw if isinstance(raw, int) else 1)
        if code not in (0, 1, 2):
            code = 2
    except BaseException as exc:  # no unexpected error may wear a verdict's code
        code = _err(f"internal error - {type(exc).__name__}: {exc}")
    # Own the flush. Buffered output that never lands is not a rendered verdict,
    # so a stdout failure downgrades any 0 or 1 to 2 - and sealing both streams
    # keeps the interpreter's shutdown flush from raising and exiting 120.
    if not _seal(sys.stdout, 1) and code != 2:
        code = _err("io error - stdout write failed, no verdict was rendered")
    _seal(sys.stderr, 2)
    sys.exit(code)
