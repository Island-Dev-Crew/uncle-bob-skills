#!/usr/bin/env python3
"""ratchet.py - no-regression gate on touched files, plus a legacy project budget.

Consumes metrics that were already computed upstream (the CRAP formula, its
thresholds and the absolute per-function ceiling belong to the crap-gate island;
this script only compares numbers). Records are TSV, one row per file:

    path <TAB> worst_crap <TAB> max_complexity <TAB> coverage_pct

Blank lines are ignored, and so is a '#' line that carries no tab - the anchor is
the tab, not the '#', so a data row whose path legitimately starts with '#' (the
Emacs autosave '#file#') parses as data instead of vanishing from the record.

The path field is the join key. key_of() is the single normalization: './a/b.py',
'a//b.py' and 'a\\b.py' are one file. A key it cannot reduce to the baseline's
repo-relative form - absolute, drive-prefixed or tree-escaping - is refused
(exit 2) rather than passed to the lenient new-file branch, where a regression
would ride the ceiling unjoined. Two keys that differ only by letter case,
Unicode form (NFC/NFD, routine on macOS) or a trailing dot or space (which
Windows erases) are the same file on some filesystem but would not join each
other, so they are refused the same way. A key carrying an invisible codepoint -
a UTF-8 BOM that a Windows editor left mid-file, a zero-width space - joins
nothing at all and is refused on sight. Join or refuse, never reroute.

Exit codes:
  0  green   - nothing got worse, new files under the ceiling, budget respected
  1  verdict - at least one regression, new file over ceiling, or budget bust
  2  usage / IO / malformed input - never a verdict; an unreadable gate cannot
     pass, and neither can one whose verdict reached nobody
"""
import argparse
import math
import os
import posixpath
import re
import sys
import unicodedata
from pathlib import Path

# Anchored and deliberately narrow: rejects 'nan'/'inf' (whose comparisons are
# always False and would silently pass every check), exponent forms, and signs.
# The same hazard reaches the gate through --ceiling/--budget, which argparse
# parses with float() and so accepts 'nan'/'inf'/'1e400'; main() rejects both
# explicitly with math.isfinite rather than trusting a range comparison to.
NUM = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
# A Windows drive prefix survives normpath ('C:/api/x.py', 'C:api/x.py'), so it
# would never join a repo-relative baseline row - see parse_records.
DRIVE = re.compile(r"^[A-Za-z]:")
# Codepoints that render as nothing (or as an ordinary space) and so cannot be
# seen in a diff: controls, format characters (U+FEFF BOM, U+200B ZWSP) and the
# non-ASCII space separators. A plain U+0020 is a legal filename character and is
# excluded; everything else here makes a key that silently joins nothing.
INVISIBLE = ("Cc", "Cf", "Zl", "Zp", "Zs")
EPS = 1e-9
FIELDS = ("crap", "complexity", "coverage")


class InputError(Exception):
    """Malformed or unreadable input - exit 2, distinct from any verdict."""


def key_of(name):
    """The one join-key function. Reduces './x', 'x//y', 'x\\y', 'x/y/'."""
    return posixpath.normpath(name.replace("\\", "/"))


def fold_key(name):
    """The shadow of a join key under the spellings a filesystem erases.

    NFC folds the macOS-native decomposed form onto the composed one; casefold
    folds letter case; stripping a trailing dot or space from each segment folds
    the spelling Windows erases when it stores the name ('router.py.' is
    'router.py' there). Two distinct keys sharing a fold are one file on macOS or
    Windows, so they must never sit on opposite sides of a join.
    """
    folded = unicodedata.normalize("NFC", name).casefold()
    return "/".join(seg.rstrip(". ") or seg for seg in folded.split("/"))


def first_invisible(name):
    """The first codepoint in `name` that a reader cannot see, or None."""
    for ch in name:
        if ch != " " and unicodedata.category(ch) in INVISIBLE:
            return ch
    return None


def fmt_close(value, other, spec=".2f", wide=".12g"):
    """Format `value` at the narrowest precision that still differs from `other`.

    The verdict compares full floats; a message that prints 'crap 3.20 -> 3.20'
    on a WORSE line hides the difference the verdict actually turned on. Widening
    once is not enough - at CRAP 1000 (complexity 32 at zero coverage) a gap
    larger than EPS still vanishes at .12g - so the widening walks out to '.17g',
    which round-trips a double and therefore renders two distinct floats
    distinctly. Equal floats print at `spec`, because there is nothing to show.
    """
    if value == other:
        return format(value, spec)
    for candidate in (spec, wide, ".17g"):
        if format(value, candidate) != format(other, candidate):
            return format(value, candidate)
    return repr(value)


def parse_records(path):
    try:
        # utf-8-sig, not utf-8: a leading U+FEFF is what PowerShell's Out-File,
        # .NET StreamWriter and Excel's CSV export all write, and utf-8 keeps it
        # as the first character of line 1 - where it becomes part of a path key
        # that joins nothing. It decodes BOM-less UTF-8 unchanged, and still
        # raises UnicodeDecodeError on latin-1 or UTF-16.
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError is a ValueError, not an OSError: a latin-1 or UTF-16
        # record is an unreadable gate, and must exit 2 like any other IO fault
        # rather than crash out on the exit code reserved for a real verdict.
        raise InputError(f"cannot read {path}: {exc}") from exc
    rows = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        # Anchor comment detection on the ABSENCE of a tab. '#' also begins a
        # legal path, and a line-skipping rule applied to the path field silently
        # deletes the row - a dropped regression is a false green. A 4-field row
        # is always data; header comments carry no tab and still skip.
        if line.lstrip().startswith("#") and "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            raise InputError(f"{path}:{lineno}: expected 4 tab-separated fields, got {len(parts)}")
        name = parts[0].strip()
        if not name:
            raise InputError(f"{path}:{lineno}: empty path field")
        # The path IS the join key, so a cosmetic variant ('./a/b.py', 'a//b.py',
        # 'a\\b.py') must not miss the baseline row and fall to the lenient
        # new-file branch. Normalize to one platform-independent form first; the
        # duplicate check then runs on the key, so two spellings of one file in
        # one record collide as a duplicate (exit 2) instead of double-counting.
        name = key_of(name)
        # A BOM that survived the file-level strip (one left mid-file by an editor
        # that appended to an already-BOM'd record), a zero-width space, an NBSP:
        # str.strip() does not remove them (U+FEFF is category Cf, not whitespace),
        # key_of does not touch them, and fold_key has nothing to fold them onto -
        # so the key joins nothing and rides the lenient new-file branch with a
        # regression aboard. Refuse rather than guess which file was meant.
        ghost = first_invisible(name)
        if ghost is not None:
            raise InputError(
                f"{path}:{lineno}: path key {ascii(name)} contains U+{ord(ghost):04X}, "
                "an invisible codepoint that joins nothing; emit the path as plain text"
            )
        # normpath reduces './x', 'x//y' and 'x\\y'; it does NOT reduce an absolute
        # key ('/repo/api/x.py' - routine istanbul/jest coverage-final.json output),
        # a drive prefix, or a tree-escaping '../x.py'. Those can never match a
        # repo-relative baseline row, so they must not reach the lenient new-file
        # branch, where a regression on all three axes would report green. Fail
        # closed instead: an unjoinable key is malformed for this gate's purpose.
        if name.startswith("/") or DRIVE.match(name) or name == ".." or name.startswith("../"):
            raise InputError(
                f"{path}:{lineno}: path key '{name}' is not repo-relative; "
                "pass paths relative to the repo root so they join the baseline"
            )
        if name in rows:
            raise InputError(f"{path}:{lineno}: duplicate row for '{name}' (path keys are normalized)")
        values = []
        for label, raw in zip(FIELDS, parts[1:]):
            token = raw.strip()
            if not NUM.match(token):
                raise InputError(f"{path}:{lineno}: {label} '{token}' is not a plain non-negative number")
            value = float(token)
            # NUM admits any digit run, and float() turns a long enough one into
            # inf without raising. An inf baseline makes 'crap > b_crap' False
            # forever - the crap axis silently switched off, exactly the nan
            # hazard NUM exists to block. Reject it on the same terms.
            if not math.isfinite(value):
                raise InputError(f"{path}:{lineno}: {label} '{token[:24]}...' overflows to a non-finite number")
            values.append(value)
        if values[2] > 100.0:
            raise InputError(f"{path}:{lineno}: coverage {values[2]:g} exceeds 100")
        rows[name] = tuple(values)
    if not rows:
        raise InputError(f"{path}: no data rows (an empty gate cannot pass)")
    return rows


def refuse_key_variants(labelled_records):
    """Refuse any two distinct keys that share a fold, wherever they appear.

    There is no exact-match pass ahead of this: the check groups every key from
    both records by fold_key and fires whenever one group holds two spellings,
    including a case-sensitive tree genuinely holding both 'api/router.py' and
    'API/Router.py' with each key joining its own baseline row. The gate names
    the collision rather than guessing, because on macOS or Windows that same
    record is one file counted twice. A record that spells every path one way -
    all caps included - has no fold partner and joins normally; only a mixture is
    refused. Checked across both records at once, so it also catches a fold-only
    duplicate that the per-row exact-key check cannot see.
    """
    groups = {}
    for label, rows in labelled_records:
        for name in rows:
            groups.setdefault(fold_key(name), {}).setdefault(name, label)
    for spellings in groups.values():
        if len(spellings) > 1:
            first, second = sorted(spellings)[:2]
            # NFC and NFD render identically; escape both so the message names two
            # visibly different keys rather than the same one twice.
            show = (lambda k: f"'{k}'") if first.isascii() and second.isascii() else ascii
            raise InputError(
                f"path key {show(first)} ({spellings[first]}) and {show(second)} "
                f"({spellings[second]}) differ only by case, Unicode form, or a trailing "
                "dot or space, and cannot join each other; emit one spelling per file"
            )


def compare(base, cur, ceiling):
    regressions, new_over = 0, 0
    for name in sorted(cur):
        crap, comp, cov = cur[name]
        if name in base:
            b_crap, b_comp, b_cov = base[name]
            worse = []
            if crap > b_crap + EPS:
                worse.append(f"crap {fmt_close(b_crap, crap)} -> {fmt_close(crap, b_crap)}")
            if comp > b_comp + EPS:
                worse.append(f"complexity {fmt_close(b_comp, comp, 'g')} -> {fmt_close(comp, b_comp, 'g')}")
            if cov < b_cov - EPS:
                worse.append(f"coverage {fmt_close(b_cov, cov, 'g')}% -> {fmt_close(cov, b_cov, 'g')}%")
            if worse:
                regressions += 1
                print(f"WORSE       {name}  " + "; ".join(worse))
            else:
                # The ok line widens on the same terms as the WORSE line: a file
                # that moved 3.20 -> 3.199 is green, but printing 'crap 3.20 ->
                # 3.20' into the evidence packet reads as no change at all.
                print(f"ok          {name}  "
                      f"crap {fmt_close(b_crap, crap)} -> {fmt_close(crap, b_crap)}, "
                      f"coverage {fmt_close(b_cov, cov, 'g')}% -> {fmt_close(cov, b_cov, 'g')}%")
        elif crap > ceiling + EPS:
            new_over += 1
            print(f"NEW-OVER    {name}  crap {crap:.2f} over ceiling {ceiling:g}")
        else:
            print(f"ok new      {name}  crap {crap:.2f} at or under ceiling {ceiling:g}")
    return regressions, new_over


def silence(stream):
    """Point a failed stream's fd at the void so shutdown cannot re-raise on it.

    Catching a BrokenPipeError leaves the bytes that failed to write sitting in
    the stream's buffer. CPython flushes it again during interpreter shutdown,
    that second BrokenPipeError escapes past every handler, and the process exits
    120 - a fourth status no verdict means. Redirecting the fd makes the final
    flush a silent no-op, so the 2 returned below is the status the pipeline
    actually reads. Both streams need it: a broken stdout is the common case
    ('ratchet.py ... | head -1'), and a broken stderr would otherwise turn the
    error message itself into a 120.
    """
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stream.fileno())
        os.close(devnull)
    except Exception:  # noqa: BLE001 - best effort: the exit code matters, not the fd
        pass


def report(kind, message):
    """Every non-verdict exit goes through here, and every one of them is 2.

    The message is best-effort - a stderr that is closed, or itself broken, must
    not turn the 2 into a traceback or a shutdown-flush 120 - but the code is not.
    """
    try:
        if sys.stderr is not None:
            print(f"{kind}: {message}", file=sys.stderr)
            sys.stderr.flush()
    except Exception:  # noqa: BLE001 - see docstring
        silence(sys.stderr)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="No-regression ratchet over touched files.")
    ap.add_argument("--baseline", required=True, help="TSV of recorded per-file metrics")
    ap.add_argument("--current", required=True, help="TSV of the touched files as they stand now")
    ap.add_argument("--ceiling", type=float, default=6.0, help="absolute CRAP ceiling for new files (from crap-gate)")
    ap.add_argument("--budget", type=float, default=5.0, help="percent of project files allowed over the ceiling")
    args = ap.parse_args(argv)
    # A closed fd 1 leaves sys.stdout as None, and print() to None is a silent
    # no-op: the gate would return a verdict nobody could read. Refuse instead.
    if sys.stdout is None:
        return report("io error", "stdout is closed; a verdict that reaches nobody is not evidence")
    try:
        if not math.isfinite(args.ceiling) or args.ceiling <= 0:
            raise InputError(f"--ceiling must be a finite positive number, got {args.ceiling}")
        if not math.isfinite(args.budget) or not 0.0 <= args.budget <= 100.0:
            raise InputError(f"--budget must be a finite percentage in 0..100, got {args.budget}")
        base = parse_records(args.baseline)
        cur = parse_records(args.current)
        refuse_key_variants([("baseline", base), ("current", cur)])

        regressions, new_over = compare(base, cur, args.ceiling)
        merged = dict(base)
        merged.update(cur)
        over = [n for n, v in merged.items() if v[0] > args.ceiling + EPS]
        pct = 100.0 * len(over) / len(merged)
        bust = pct > args.budget + EPS
        shown = fmt_close(pct, args.budget, ".1f")
        print(f"budget: {len(over)}/{len(merged)} files over ceiling {args.ceiling:g} = "
              f"{shown}% (limit {args.budget:.1f}%)")
        if bust:
            print("BUDGET-BUST over-ceiling share exceeds the declared project allowance")
        print(f"{len(cur)} touched files, {regressions} regressions, {new_over} new over ceiling")
        sys.stdout.flush()
    except InputError as exc:
        return report("input error", exc)
    except (OSError, ValueError) as exc:
        # A write that failed carried away part of the verdict; it is an IO fault,
        # not a judgement, and must not borrow exit 0 or 1 from one - nor 120 from
        # the shutdown flush of the buffer whose write just failed.
        silence(sys.stdout)
        return report("io error", f"cannot emit the verdict: {exc}")
    except Exception as exc:  # noqa: BLE001 - no crash may wear a verdict's code
        return report("internal error", f"{type(exc).__name__}: {exc}")
    return 1 if (regressions or new_over or bust) else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython
    # flushes the std streams after main() returns, and if that flush raises - a pipe
    # whose reader has gone, the ordinary `| head` idiom - it REPLACES the status with
    # 120, a code no table here names. argparse is the other leak: it raises SystemExit
    # from inside, so a usage error would skip any seal placed after a bare call.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse usage errors and --help
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except BaseException as _exc:              # an exception is not a verdict
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
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 2
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
