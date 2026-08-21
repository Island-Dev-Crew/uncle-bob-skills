#!/usr/bin/env python3
"""load-ledger.py — gate a per-task context-load ledger against the interface budget.

Usage:
  python3 load-ledger.py [--impl-share-max FLOAT] LEDGER.tsv [LEDGER.tsv ...]
  python3 load-ledger.py [--impl-share-max FLOAT] -          (read stdin)

Row format — five TAB-separated fields, one row per file loaded into context.
The ledger must be UTF-8 (a leading byte-order mark is accepted and dropped,
because that is what Windows editors write); anything else is unreadable, not a
verdict (exit 2).
Paths must be repo-relative: a path that is absolute, drive-qualified, home-
anchored, or that escapes the repo root with a leading '..' cannot be compared
against the relative spelling of the same body, so it is refused (exit 2)
rather than allowed to key apart from it. A path carrying an invisible control
or format character (U+FEFF, U+200B, U+0001...) is refused for the same reason:
it renders identically to the same body typed without it, so it would key apart
while looking the same on the page.
  task_id <TAB> path <TAB> kind <TAB> tokens <TAB> reason
    kind   : interface | test | impl        (case-insensitive)
    tokens : non-negative integer, at most 9 digits
    reason : required for kind=impl, from the closed vocabulary below; '-' otherwise
  Blank lines are ignored. A comment is a line whose FIRST column is '#':
  the marker is anchored at column 0 so no indented row can vanish unannounced
  (an indented '#' is malformed, and says so, instead of being dropped).

Rules (a violation is a verdict, exit 1):
  IMPL-FIRST   an impl row appears before this task's first interface/test row
  UNJUSTIFIED  an impl row's reason is not in the closed vocabulary
  RE-READ      one file bought twice at the same tier or below, inside one task.
               Paths are keyed by norm_key() below, so every repo-relative
               spelling that names one body collapses to one key; task ids are
               keyed casefolded for the same reason, so 'T-43' and 't-43' are
               one task and cannot split one over-read into two green ones. A strictly
               upward tier move on one path (interface -> impl for a single-file
               module with no stub) is a subset then the whole, not the same fact
               twice, and is legal; a repeat at the same tier, or a move back
               down, is a violation.
  OVER-BUDGET  impl tokens exceed the declared share of the task's loaded tokens
               (breach is strictly greater than the ceiling; exactly-at passes)

Exit codes — distinct meanings, never shared:
  0  every task passed every rule (also argparse's own --help, which gates
     nothing — unless the help text itself cannot be written, which is the same
     input failure as a lost report and exits 2)
  1  verdict: at least one rule violation
  2  usage / unreadable, closed, or non-UTF-8 input / malformed or empty ledger
     / a report that cannot be written (stdout closed at start, closed by the
     reader mid-report, or otherwise unwritable)
     (fail-closed: an empty gate cannot pass, and an unreadable one is not a
     verdict. No error path this script raises may borrow exit 1, which is
     reserved for a verdict the gate actually computed — an unhandled crash is
     caught and re-coded to 2 rather than left to CPython's exit 1. Nor may one
     borrow CPython's 120: every exit this script or argparse raises is caught
     at __main__, both streams are flushed while the code is still ours to set,
     and a stream that fails to flush is pointed at /dev/null — so the flush
     CPython runs at interpreter shutdown cannot fail and replace the status
     with 120. A signal is outside that promise: SIGINT is never handled here —
     the one clause naming it re-raises it untouched — so the process dies by
     signal 2, which POSIX shells report as 130.)
"""
import argparse
import os
import posixpath
import re
import sys
import traceback
import unicodedata
from pathlib import Path

TIERS = {"interface": 1, "test": 2, "impl": 3}
KINDS = tuple(TIERS)
REASONS = (
    "interface-silent",   # interface + its comment did not answer the question
    "comment-missing",    # the interface carries no comment to read
    "tests-absent",       # no test demonstrates the behaviour in question
    "editing",            # the task is to change this implementation
    "defect-suspected",   # the defect is believed to live inside this implementation
    "contract-doubt",     # observed behaviour contradicts the interface comment
)
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$")
INT_RE = re.compile(r"^[0-9]{1,9}$")
# Not-repo-relative, in one place: leading '/', a drive letter with or without a
# separator ('C:/a.py' and the drive-relative 'C:a.py' both name a body outside
# this repo's key space), or a '~' home anchor.
NONREL_RE = re.compile(r"^(?:/|[A-Za-z]:|~)")
SCALE = 10000  # integer basis points; no float comparison decides a verdict


def complain(msg):
    """Put a diagnostic on stderr and NEVER on stdout. print(file=sys.stderr)
    is not enough: when fd 2 is closed at startup CPython sets sys.stderr to
    None, and print() treats a None file as 'use sys.stdout' — which would drop
    an error message into the middle of the report stream. Fall back to a raw
    write on fd 2, and if that fd is gone too, stay silent rather than pollute
    the report. Encoding errors are escaped, never raised."""
    line = f"load-ledger: {msg}\n"
    if sys.stderr is not None:
        try:
            sys.stderr.write(line)
            sys.stderr.flush()
            return
        except (OSError, ValueError):
            pass
    try:
        os.write(2, line.encode("utf-8", "backslashreplace"))
    except (OSError, ValueError):
        pass


def die(msg):
    complain(msg)
    raise SystemExit(2)


def norm_key(path):
    """One key per file body, folding every repo-relative spelling of it.

    Backslashes fold to '/' first (a Windows-style spelling is not a second
    file), then posixpath.normpath folds the './' '../' '//' family, then the
    key is casefolded, then NFC-normalised.

    Case is folded deliberately, not overlooked: on the case-insensitive
    filesystems this pack runs on (macOS, Windows) 'Src/A.py' and 'src/a.py'
    ARE one file, so keeping case significant would hand the gate a free
    bypass; on a case-sensitive filesystem two paths differing only in case are
    themselves a defect worth the flag.

    Unicode form is folded for the same reason and it is not exotic: macOS
    hands out NFD filenames while editors, git and shells hand back NFC, so
    'panier-caf\\u00e9.py' and 'panier-cafe\\u0301.py' are routinely the same
    body typed two ways. NFC is applied AFTER casefold because casefold can
    itself decompose (e.g. \\u1e9e).

    Paths that are not repo-relative never reach here — parse() refuses them
    (exit 2) rather than let '/repo/src/a.py' or '../repo/src/a.py' key apart
    from 'src/a.py'.
    """
    folded = posixpath.normpath(path.replace("\\", "/")).casefold()
    return unicodedata.normalize("NFC", folded)


def parse(lines, src):
    rows = []
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("#"):   # anchored at column 0 — see module docstring
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 5:
            die(f"{src}:{n}: expected 5 tab-separated fields, got {len(parts)}")
        task, path, kind, tokens, reason = parts
        kind, reason = kind.lower(), reason.lower()
        if not TASK_RE.match(task):
            die(f"{src}:{n}: bad task_id {task!r}")
        if not path:
            die(f"{src}:{n}: empty path")
        # An invisible character is the one spelling difference the eye cannot
        # see, so it is refused rather than folded: 'src/a﻿.py' renders
        # exactly like 'src/a.py' and would otherwise key apart from it.
        invisible = next((c for c in path if unicodedata.category(c) in ("Cc", "Cf")), None)
        if invisible is not None:
            die(f"{src}:{n}: path {path!a} carries the invisible character "
                f"U+{ord(invisible):04X}; it cannot be told apart on the page from the "
                f"same body typed without it, so it is refused rather than keyed apart")
        slashed = path.replace("\\", "/")
        if NONREL_RE.match(slashed):
            die(f"{src}:{n}: non-relative path {path!r}; log repo-relative paths so one body has one key")
        normed = posixpath.normpath(slashed)
        if normed == ".." or normed.startswith("../"):
            die(f"{src}:{n}: path {path!r} escapes the repo root; log repo-relative paths so one body has one key")
        if kind not in KINDS:
            die(f"{src}:{n}: unknown kind {kind!r}, expected one of {'|'.join(KINDS)}")
        if not INT_RE.match(tokens):
            die(f"{src}:{n}: tokens {tokens!r} is not a non-negative integer")
        rows.append((task, path, kind, int(tokens), reason, f"{src}:{n}"))
    return rows


def bp_text(bp):
    """Basis points as a percentage string, exact integer arithmetic, no float."""
    return f"{bp // 100}.{bp % 100:02d}%"


def spelt_hint(prev_path, path):
    """Name the earlier spelling. When the two render identically — the NFC/NFD
    case — show the ascii-escaped repr so the difference is visible on the page
    instead of looking like the gate flagged a row against itself."""
    if prev_path == path:
        return ""
    if unicodedata.normalize("NFC", prev_path) == unicodedata.normalize("NFC", path):
        return f" (spelt {prev_path!a}, same body in a different Unicode form)"
    return f" (spelt {prev_path})"


def audit(rows, ceiling_bp):
    # Task ids are grouped casefolded, for the same reason paths are: 'T-43'
    # and 't-43' are one label typed two ways, and keying them apart would let
    # one over-read split into two individually-clean tasks. The label PRINTED
    # is the spelling as first given, so the fold never rewrites the ledger.
    tasks, findings = {}, []
    order = []
    for r in rows:
        tkey = r[0].casefold()
        if tkey not in tasks:
            tasks[tkey] = []
            order.append((tkey, r[0]))
        tasks[tkey].append(r)
    for tkey, task in order:
        spec_seen, seen, impl_tokens, total = False, {}, 0, 0
        for _, path, kind, tok, reason, where in tasks[tkey]:
            total += tok
            if kind in ("interface", "test"):
                spec_seen = True
            else:
                impl_tokens += tok
                if not spec_seen:
                    findings.append((task, "IMPL-FIRST", f"{where} {path} loaded before any interface or test"))
                if reason not in REASONS:
                    findings.append((task, "UNJUSTIFIED", f"{where} {path} reason {reason!r} not in the vocabulary"))
            key, tier = norm_key(path), TIERS[kind]
            prev = seen.get(key)
            if prev is None or tier > prev[0]:
                # first sight, or a strictly upward tier move on one path — a
                # signature extract followed by the body is a subset then the
                # whole, which is the escalation this island prescribes, not
                # the same fact bought twice.
                seen[key] = (tier, kind, where, path)
            else:
                _, prev_kind, prev_where, prev_path = prev
                findings.append((task, "RE-READ",
                                 f"{where} {path} {kind} already loaded as {prev_kind} "
                                 f"at {prev_where}{spelt_hint(prev_path, path)}"))
        # Basis points, rounded UP: the verdict fires iff the exact share
        # exceeds the ceiling, and ceil() over an integer ceiling preserves that
        # iff exactly — so a printed share can never read as equal to a ceiling
        # it just breached (35.40%, never a rounded-down '35%').
        share_bp = -(-impl_tokens * SCALE // total) if total else 0
        if total and impl_tokens * SCALE > ceiling_bp * total:
            findings.append((task, "OVER-BUDGET",
                             f"impl {impl_tokens}/{total} tokens = {bp_text(share_bp)} "
                             f"over ceiling {bp_text(ceiling_bp)}"))
        print(f"task {task}: {len(tasks[tkey])} loads, {total} tokens, impl share {bp_text(share_bp)}")
    return findings


def read_source(s):
    """Return the decoded text of one ledger source. Every failure here is an
    input failure, so every one of them exits 2 — including a closed stdin,
    where sys.stdin is None and the attribute access would otherwise raise and
    hand a CI consumer exit 1, the code reserved for a real verdict."""
    if s == "-":
        stream = getattr(sys.stdin, "buffer", None)
        if stream is None:
            die("cannot read stdin: no stdin is attached (closed or detached)")
        try:
            return stream.read().decode("utf-8-sig"), "stdin"
        except (OSError, ValueError, UnicodeDecodeError) as e:
            die(f"cannot read stdin: {e}")
    # Decode explicitly and catch the decode failure beside the IO failure:
    # UnicodeDecodeError is a ValueError, not an OSError, so an un-decodable
    # ledger would otherwise escape as a traceback and exit 1. 'utf-8-sig'
    # drops a leading BOM if one is there and is plain utf-8 otherwise, so a
    # ledger saved by a Windows editor gates instead of failing on row 1 —
    # a BOM is UTF-8, and the docstring promises UTF-8 is readable.
    try:
        return Path(s).read_bytes().decode("utf-8-sig"), s
    except (OSError, ValueError, UnicodeDecodeError) as e:
        die(f"cannot read {s}: {e}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--impl-share-max", type=float, default=0.35)
    ap.add_argument("ledgers", nargs="*", default=[])
    args = ap.parse_args()
    # NaN fails every comparison, so `not (0 <= x <= 1)` refuses it here rather
    # than letting it silently disable OVER-BUDGET downstream.
    if not (0.0 <= args.impl_share_max <= 1.0):
        die(f"--impl-share-max {args.impl_share_max} outside 0.0..1.0")
    ceiling_bp = int(round(args.impl_share_max * SCALE))

    rows = []
    for s in args.ledgers or ["-"]:
        # The source label is the path AS GIVEN, never its basename: two
        # ledgers named led.tsv in different directories must not both cite
        # 'led.tsv:1'. Every finding pointer resolves to exactly one file.
        text, label = read_source(s)
        rows += parse(text.splitlines(), label)
    if not rows:
        die("empty ledger: nothing to gate")

    findings = audit(rows, ceiling_bp)
    for task, rule, detail in findings:
        print(f"VIOLATION [{rule}] task {task}: {detail}")
    print(f"{len(rows)} loads, {len(findings)} violations, ceiling {bp_text(ceiling_bp)} impl share")
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        # fd 1 closed at interpreter start makes sys.stdout None, and print()
        # with a None stdout silently discards every line — the whole report,
        # verdict included. That is an input failure exactly as a closed stdin
        # is, so it dies at 2 rather than letting an AttributeError at the final
        # flush escape as CPython's exit 1, the code reserved for a real verdict.
        if sys.stdout is None:
            die("stdout is closed or detached; the report cannot be written")
        try:
            # A path this gate can print in UTF-8 must not abort the run under an
            # ASCII pipeline (PYTHONIOENCODING=ascii is set by real CI images):
            # degrade the character to the same escaped form spelt_hint() already
            # uses, so the findings survive to be read.
            sys.stdout.reconfigure(errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            pass
        code = main()
        sys.stdout.flush()
    except (BrokenPipeError, OSError, ValueError) as e:
        # A report that could not be written is not a verdict either — and the
        # failure can be a closed pipe (BrokenPipeError), a bad fd (OSError) or
        # an un-encodable character (UnicodeEncodeError, a ValueError).
        complain(f"stdout lost before the report finished: {e}")
        code = 2
    except SystemExit as e:
        # Every die() lands here, and so do argparse's own exits: a usage error
        # and --help. They must not sail PAST this block into interpreter
        # shutdown — the flush CPython runs there can fail on a dead stream, and
        # when it does CPython DISCARDS the status and exits 120, a code in no
        # table this gate publishes. Caught here, the code goes through the
        # sealed flush below like any other.
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except KeyboardInterrupt:
        raise   # signals are never handled here; re-raised untouched → 130
    except BaseException as e:
        # A crash is not a verdict either. Keep the traceback for debugging,
        # but never let CPython's exit-1-on-unhandled-exception impersonate a
        # violation the gate never computed.
        if sys.stderr is not None:
            traceback.print_exc()
        complain(f"internal error, not a verdict: {type(e).__name__}: {e}")
        code = 2
    # Flush both streams HERE, while the exit code is still this script's to
    # set. A buffered byte that never lands is not a report, so a stream that
    # fails to flush downgrades a 0 or a 1 to 2; then the fd is pointed at
    # /dev/null so the flush at interpreter shutdown cannot raise and re-code
    # the exit to CPython's own 120 behind us.
    sealed = True
    for _stream, _fd, _name in ((sys.stdout, 1, "stdout"), (sys.stderr, 2, "stderr")):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException as _e:
            if code in (0, 1):
                complain(f"{_name} lost before the report finished: {_e}")
                code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                sealed = False
    if not sealed:
        # /dev/null itself is unavailable, so the shutdown flush would raise and
        # CPython would exit 120. Leave by the one door that runs no shutdown.
        os._exit(code)
    sys.exit(code)
