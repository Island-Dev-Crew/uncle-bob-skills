#!/usr/bin/env python3
"""secret-manifest.py - refuse a module list unless every module DECLARES the design
decision it hides (Parnas 1972, "decompose by what a module hides").

This gate checks that a declaration EXISTS, is non-empty, is not declared twice in the
manifest, does not read as a placeholder, and carries at least --min-chars SUBSTANTIVE
characters. It cannot tell whether a declaration is TRUE, whether the named decision is
really hidden, or whether the split is a good one. Those judgments stay with the human
and are marked advisory in SKILL.md.

A SUBSTANTIVE character is a Unicode letter or digit (category L* or N*), counted after
NFC normalization, minus the four Hangul filler code points U+115F, U+1160, U+3164 and
U+FFA0 - which are category Lo and pass str.isalnum() while rendering as nothing. Dots,
underscores, combining marks and format characters (U+200B and friends) are length, not
substance, and do not count. A declaration holding ZERO substantive characters is
refused unconditionally, at every value of --min-chars including 0 - like an empty one,
because that is what it is.

The placeholder markers, in full. Bare (whole declaration, case-insensitive, surrounding
punctuation ignored): todo, tbd, tba, fixme, xxx+, wip, n/a, placeholder, unknown,
undecided, undetermined, unspecified, undocumented, pending, later, none, null, nil, a
run of ? or of -. Marker-plus-text (declaration OPENS with it): todo, tbd, tba, fixme,
xxx+, wip; the spelled-out stubs "to be <determined|decided|...>" and
"not [yet] <determined|decided|...>"; and placeholder / unknown / undecided /
undetermined / unspecified / undocumented / pending / later / n/a ONLY when an end of
phrase or a "not yet" tail follows (`unknown at this time`, `placeholder, fill this in
later`).
A soft marker glued to more sentence is honest prose and passes: `Later-binding of the
codec dispatch table` and `NAT traversal strategy used for peer connections` both pass.

Usage:
  python3 secret-manifest.py --manifest MANIFEST.tsv --modules MODULES.txt [--min-chars N]

MANIFEST.tsv - one row per module, exactly one TAB: <module-path>TAB<the hidden decision>
  A line is a comment ONLY when its first character is '#' AND the line contains no TAB
  (a real row always has a TAB, so a path may legitimately start with '#').
  Blank lines are ignored. UTF-8, optional BOM, LF / CRLF / CR all accepted.
MODULES.txt - one module path per line. Blank lines ignored. No comment syntax at all.

Key function (documented, applied identically to both files): strip surrounding spaces,
tabs and newlines; Unicode-NFC-normalize; drop '.' path segments; resolve '..' textually;
collapse repeated '/'; strip one trailing '/'. Letter case is NOT folded and an absolute
path is NOT conflated with a relative one - a spelling variant fails to join and the
module reads as undeclared, which refuses rather than consents. Two DIFFERENT raw module
paths that collapse to one key are an ambiguity, not a verdict, and exit 2.

Exit codes:
  0  every listed module carries a non-duplicated, non-placeholder declaration holding
     >= min-chars substantive characters. `--help` also exits 0, after printing usage.
  1  at least one listed module is undeclared, empty-declared, declared with no
     substantive characters at all, placeholder-declared, short of min-chars substantive
     characters, or declared more than once in the manifest
  2  usage error, unreadable or non-UTF-8 input, malformed manifest row, empty module
     list, ambiguous module key, or any internal failure - never a verdict. A failed
     flush of stdout or stderr, and a stream missing entirely because its fd was closed
     before launch, also land here: a report that never reached the caller is not a pass.

A module path of "." is a usage error by design, not a module: it normalizes to nothing
and exits 2. Generate the module list with directories only.

Known blind spot, deliberately not closed: manifest rows for modules that are NOT in the
module list are ignored, so a stale declaration left behind by a deleted module passes.
Captured in scripts/fixtures/stale-blind-spot/ as an exit-0 run.
"""
import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path

# Two rules, built from ONE marker vocabulary so they cannot drift apart. PLACEHOLDER is
# .fullmatch()ed against the whole stripped declaration and catches a bare marker.
# PLACEHOLDER_PREFIX is .match()ed at the start and catches the marker-plus-text form
# (`TODO: decide the layout`, `to be determined`), which fullmatch alone accepts as a
# superstring. Hard stubs (`todo`, `tbd`, `fixme`, ...) never open an honest declaration, so
# they fire on a word boundary alone. Soft markers (`later`, `pending`, `unknown`,
# `placeholder`, `n/a`) DO open honest declarations - `Later-binding of the codec
# dispatch table`, `N/A handling in the CSV importer` - so they fire only when an end
# of phrase or a "not yet" tail follows.
_STUB = r"(?:todo|tbd|tba|fixme|xxx+|wip)"
_SOFT = (r"(?:placeholder|unknown|undecided|undetermined|unspecified|undocumented"
         r"|pending|later|n/?a)")
_UNSETTLED = (
    r"(?:determined|decided|defined|specified|documented|written|known|named|chosen"
    r"|settled|picked|filled(?:\s+in)?|figured\s+out|sorted\s+out|worked\s+out"
    r"|nailed\s+down)"
)
_SOFT_TAIL = (
    r"(?=\s*(?:$|[,;:.\u2013\u2014]|at\s+this\s+time\b|at\s+present\b|for\s+now\b"
    r"|as\s+yet\b|so\s+far\b|until\b))"
)
PLACEHOLDER = re.compile(
    r"[\s\W_]*(?:" + _STUB + r"|" + _SOFT + r"|none|null|nil|\?+|-+)[\s\W_]*",
    re.IGNORECASE,
)
PLACEHOLDER_PREFIX = re.compile(
    r"[\s\W_]*(?:"
    + _STUB + r"\b"
    + r"|to\s+be\s+" + _UNSETTLED + r"\b"
    + r"|(?:still\s+)?not\s+(?:yet\s+)?" + _UNSETTLED + r"\b"
    + r"|" + _SOFT + r"\b" + _SOFT_TAIL
    + r")",
    re.IGNORECASE,
)
# The four Hangul fillers are category Lo and satisfy str.isalnum() - and so satisfy \w -
# while rendering as blank. A floor counted in \w alone is buyable with them.
INVISIBLE_LETTERS = frozenset("\u115f\u1160\u3164\uffa0")
DIGITS = re.compile(r"[0-9]+")


def substantive_chars(text):
    """Letters and digits only, NFC-normalized first so an NFD spelling is not penalized,
    and the invisible Hangul fillers removed. Marks, format characters, punctuation and
    the underscore are length without substance and are not counted."""
    total = 0
    for ch in unicodedata.normalize("NFC", text):
        if ch in INVISIBLE_LETTERS:
            continue
        if unicodedata.category(ch)[0] in ("L", "N") and unicodedata.combining(ch) == 0:
            total += 1
    return total


class GateError(Exception):
    """An input the gate cannot judge. Always exit 2, never 0 or 1."""


def bounded_int(text):
    t = text.strip()
    # Bound the digit count before int(): CPython raises on integers past 4300 digits,
    # and an exception is not a verdict.
    if len(t) > 6 or not DIGITS.fullmatch(t):
        raise argparse.ArgumentTypeError("expected a non-negative integer of at most 6 digits")
    return int(t)


def read_lines(path, label):
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise GateError(f"cannot read {label} {path!r}: {type(exc).__name__}: {exc}")
    if data.startswith(b"\xef\xbb\xbf"):          # editor-written UTF-8 BOM
        data = data[3:]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"{label} {path!r} is not valid UTF-8: {exc}")
    text = text.replace("\r\n", "\n").replace("\r", "\n")   # CRLF and classic-Mac CR
    return text.split("\n")


def norm_key(raw, label, lineno):
    s = raw.strip(" \t\r\n")
    if not s:
        raise GateError(f"{label} line {lineno}: empty module path")
    s = unicodedata.normalize("NFC", s)
    leading = "/" if s.startswith("/") else ""
    out = []
    for seg in s.split("/"):
        if seg == "" or seg == ".":
            continue
        if seg == ".." and out and out[-1] != "..":
            out.pop()
            continue
        out.append(seg)
    key = leading + "/".join(out)
    if not key:
        raise GateError(f"{label} line {lineno}: module path {raw!r} normalizes to nothing")
    return key


def load_modules(path):
    pairs = []
    seen = {}
    for lineno, line in enumerate(read_lines(path, "module list"), start=1):
        if not line.strip(" \t\r\n"):
            continue
        raw = line.strip(" \t\r\n")
        key = norm_key(raw, "module list", lineno)
        if key in seen:
            if seen[key] != raw:
                raise GateError(
                    f"module list line {lineno}: {raw!r} and {seen[key]!r} are different "
                    f"paths that collapse to the same key {key!r}; refusing to guess"
                )
            continue                              # byte-identical repeat, harmless
        seen[key] = raw
        pairs.append((key, raw))
    if not pairs:
        raise GateError(f"module list {path!r} contains no modules; a gate with nothing to check does not pass")
    pairs.sort()
    return pairs


def load_manifest(path):
    declared = {}
    duplicates = set()
    for lineno, line in enumerate(read_lines(path, "manifest"), start=1):
        if not line.strip(" \t\r\n"):
            continue
        if line.startswith("#") and "\t" not in line:
            continue                              # comment: no TAB, so not a data row
        fields = line.split("\t")
        if len(fields) != 2:
            raise GateError(
                f"manifest line {lineno}: expected exactly one TAB "
                f"(module path, then the hidden decision), found {len(fields) - 1}"
            )
        key = norm_key(fields[0], "manifest", lineno)
        secret = fields[1].strip()
        if key in declared:
            duplicates.add(key)
        declared[key] = secret
    return declared, duplicates


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="secret-manifest.py",
        description="Refuse a module list unless every module declares the decision it hides.",
    )
    ap.add_argument("--manifest", required=True, help="TSV of module path TAB hidden decision")
    ap.add_argument("--modules", required=True, help="file listing one module path per line")
    ap.add_argument("--min-chars", type=bounded_int, default=12,
                    help="minimum substantive characters - letters and digits - in a "
                         "declaration (default 12)")
    args = ap.parse_args()

    try:
        modules = load_modules(args.modules)
        declared, duplicates = load_manifest(args.manifest)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    violations = []
    for key, raw in modules:
        if key in duplicates:
            violations.append(f"{raw}: declared more than once in the manifest")
            continue
        if key not in declared:
            violations.append(f"{raw}: no hidden decision declared")
            continue
        secret = declared[key]
        if not secret:
            # Unconditional: presence is checked at every value of --min-chars, including 0.
            violations.append(f"{raw}: declaration is empty")
            continue
        if PLACEHOLDER.fullmatch(secret) or PLACEHOLDER_PREFIX.match(secret):
            violations.append(f"{raw}: placeholder declaration {secret!r}")
            continue
        # Count SUBSTANTIVE characters, not raw length: a run of dots, of underscores, of
        # U+200B (category Cf, which str.strip() does not remove) or of U+3164 HANGUL
        # FILLER (category Lo, which \w accepts) is length without substance.
        chars = substantive_chars(secret)
        if chars == 0:
            # Unconditional, exactly like the empty rule above: a declaration with nothing
            # visible in it is empty in effect, at every value of --min-chars including 0.
            violations.append(f"{raw}: declaration has no substantive characters: {secret!r}")
            continue
        if chars < args.min_chars:
            violations.append(
                f"{raw}: declaration has {chars} substantive characters "
                f"(letters and digits), minimum is {args.min_chars}"
            )

    if violations:
        print(f"REJECTED: {len(violations)} of {len(modules)} module(s) do not name the decision they hide")
        for v in violations:
            print(f"  - {v}")
        return 1
    print(f"ACCEPTED: {len(modules)} module(s) each name one hidden design decision "
          f"(declaration presence only; truth is not checked)")
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
    # An fd closed before launch (`cmd 1>&-`) leaves sys.stdout None, print() returns
    # silently, and the flush loop below finds nothing to fail on. A verdict nobody
    # could read is not a verdict.
    if sys.stdout is None or sys.stderr is None:
        if _code in (0, 1):
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
