#!/usr/bin/env python3
"""plan-decay.py - compare a plan's stated assumptions against observed repo state.

Usage:
  python3 plan-decay.py --root DIR ASSUMPTIONS.tsv
  python3 plan-decay.py --root DIR --digest PATH

--root is REQUIRED and has no default. A default of '.' silently retargets a plan at
whichever directory the process happens to sit in, and an all-'absent' plan - the shape
the kind table blesses for a batch that only creates files - then holds vacuously
against an empty or unrelated tree and exits 0. A wrong working directory is an
ordinary CI and agent condition, not hostile input, so the omission is argparse's
usage error (exit 2), never a verdict.

A plan decays when the tree stops matching what the planner believed. This tool reads
the assumptions the plan wrote down, checks each one against the tree as it is now, and
refuses to consent when any of them has stopped being true.

Assumption file: UTF-8, one assumption per line, fields separated by TAB.
  exists     PATH                 the plan expects this path to be there
  absent     PATH                 the plan expects to create it; nothing may be there yet
  contains   PATH  LITERAL        the file still holds this literal substring
  lacks      PATH  LITERAL        the file still does not hold it
  unchanged  PATH  SHA256         the file is byte-for-byte what the planner read
                                  (digest over normalised text - see --digest)
A line whose first non-blank character is '#' and that holds no TAB is a comment.
A '#' line that DOES hold a TAB is ambiguous and is refused rather than dropped.

Exit codes:
  0  every stated assumption still holds - the plan describes this tree
     (argparse's --help also exits 0 and computes no verdict)
  1  at least one assumption diverged - HALT and re-plan
  2  usage, IO, or malformed input - never a verdict, always fail-closed
  3  informational: --digest printed a digest and checked no plan
"""
import argparse
import hashlib
import os
import re
import sys
import unicodedata
from pathlib import Path

HEX64 = re.compile(r"\A[0-9a-fA-F]{64}\Z")
TWO_FIELD = ("exists", "absent")
THREE_FIELD = ("contains", "lacks", "unchanged")
KINDS = TWO_FIELD + THREE_FIELD
LINE_BREAKING = ("\r", "\n", "\u2028", "\u2029", "\x85")
DRIVE = re.compile(r"\A[A-Za-z]:")
# Cc control, Cf format (U+FEFF ZWNBSP, U+200B-adjacent joiners, bidi marks), Cs
# surrogate, Co private use. None of these can be seen in an editor, so a path or a
# literal carrying one is a spelling no reader can verify and no directory entry can
# be trusted to equal. Refused rather than folded away.
INVISIBLE = ("Cc", "Cf", "Cs", "Co")
# Script sets a single word may legitimately mix. Japanese runs Han with both kana,
# Korean and Chinese run Han with Hangul/Bopomofo, and all three take Latin inside one
# word. Every other mixture inside one word (LATIN+CYRILLIC, LATIN+GREEK) is a
# confusable respelling, not a name an editor or a filesystem produces.
MIXABLE = (
    frozenset({"LATIN", "CJK", "HIRAGANA", "KATAKANA"}),
    frozenset({"LATIN", "CJK", "HANGUL"}),
    frozenset({"LATIN", "CJK", "BOPOMOFO"}),
)
# Character-name first tokens that name the same script under a different heading.
SCRIPT_ALIAS = {"KATAKANA-HIRAGANA": "KATAKANA"}


class Fault(Exception):
    """Anything that is not a verdict: usage, IO, malformed input. Always exit 2."""


def nfc(s):
    return unicodedata.normalize("NFC", s)


def script_of(ch):
    """The script a cased/uncased letter belongs to, or None if it carries no script.

    Only true letters (Lu/Ll/Lt/Lo) key a script. Modifier letters and combining marks
    ride along with the letter before them, and digits, punctuation and symbols are
    script-neutral, so none of them can manufacture a mixture on their own.
    """
    if unicodedata.category(ch) not in ("Lu", "Ll", "Lt", "Lo"):
        return None
    try:
        token = unicodedata.name(ch).split()[0]
    except ValueError:                     # an unnamed letter cannot be keyed at all
        return "UNNAMED"
    return SCRIPT_ALIAS.get(token, token)


def words(s):
    """Split on everything that is not letter-or-mark: one confusable lives in one word.

    A multilingual line legitimately mixes scripts BETWEEN words ('# \u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 (notes)');
    a respelling mixes them INSIDE one ('r\u0435funds' with a Cyrillic '\u0435'). Splitting first
    is what lets the gate refuse the second without refusing the first.
    """
    out, cur = [], []
    for ch in s:
        if unicodedata.category(ch)[0] in ("L", "M"):
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def refuse_unkeyable(s, where, what):
    """Refuse any spelling this gate cannot key against a real directory entry.

    Three classes, one mechanism. An invisible character (U+FEFF), a compatibility
    respelling (U+FF52 FULLWIDTH LATIN SMALL LETTER R) and a confusable respelling
    ('r\u0435funds' with U+0435 CYRILLIC SMALL LETTER IE) all produce a string that can
    never equal the entry it imitates, so `locate` reports 'missing' and every negative
    kind - `absent`, `lacks` - holds VACUOUSLY: a false green on a diverged tree.
    Refused at write time rather than folded away, because folding is lossy for
    filenames: NFKC is a refusal test here, never the matching fold.

    LIMIT, disclosed in SKILL.md and captured as scripts/fixtures/blind-spot-confusable/:
    a WHOLE-word confusable - every letter of one word respelled into a single other
    script ('\u0430\u0441\u0435' entirely in Cyrillic for 'ace') - mixes nothing and is not refused.
    """
    for ch in s:
        if ord(ch) < 32 or ch in ("\u2028", "\u2029", "\x85"):
            raise Fault(f"{where}: {what} {s!r} holds a control character")
        if unicodedata.category(ch) in INVISIBLE:
            raise Fault(
                f"{where}: {what} {s!r} holds the invisible character U+{ord(ch):04X} "
                f"(category {unicodedata.category(ch)}); an unseeable spelling cannot be checked"
            )
    folded = nfc(s)
    if unicodedata.normalize("NFKC", folded) != folded:
        raise Fault(
            f"{where}: {what} {s!r} holds a compatibility character (fullwidth, halfwidth "
            f"or ligature form); it looks like the plain spelling but can never equal it"
        )
    for word in words(folded):
        scripts = {sc for sc in (script_of(ch) for ch in word) if sc is not None}
        if len(scripts) > 1 and not any(scripts <= ok for ok in MIXABLE):
            raise Fault(
                f"{where}: {what} {s!r} mixes the scripts {', '.join(sorted(scripts))} inside "
                f"the single word {word!r}; that is a confusable respelling, not a name"
            )


def split_path(raw, where):
    """One documented key function for every path this tool reads.

    Refuses what it cannot key unambiguously instead of rerouting it to a lenient
    branch: absolute paths, drive letters, '..', backslashes, control characters, invisible
    format characters (U+FEFF and the rest of Unicode Cf/Cs/Co), compatibility and
    mixed-script respellings (see refuse_unkeyable), and components padded with
    whitespace. Folds only what is unambiguously one spelling of
    one path: '.' components and the empty components '//' produces.
    """
    if raw == "":
        raise Fault(f"{where}: empty path")
    if "\\" in raw:
        raise Fault(f"{where}: {raw!r} holds a backslash; write paths with '/' only")
    if raw.startswith("/") or DRIVE.match(raw):
        raise Fault(f"{where}: {raw!r} is absolute; assumptions are relative to --root")
    refuse_unkeyable(raw, where, "path")
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if not parts:
        raise Fault(f"{where}: {raw!r} resolves to the root itself")
    for p in parts:
        if p == "..":
            raise Fault(f"{where}: {raw!r} climbs out of --root with '..'")
        if p != p.strip():
            raise Fault(f"{where}: component {p!r} is padded with whitespace")
    return parts


def locate(root, comps, where):
    """Walk components against real directory entries.

    Returns (status, realpath, shown) with status in {'exact', 'variant', 'missing'}.
    'exact' means every component equalled a real entry name after NFC folding - the
    one fold that is genuinely the same file. A name that matches only case-folded is
    reported 'variant' and never treated as a match, in EITHER direction: a spelling the
    tree does not use is a plan that does not describe this tree.
    """
    cur = root
    walked = []
    for want in comps:
        try:
            names = os.listdir(cur)
        except FileNotFoundError:
            return "missing", None, "/".join(walked + [want])
        except NotADirectoryError:
            return "missing", None, "/".join(walked) + " (not a directory)"
        except OSError as e:
            raise Fault(f"{where}: cannot read directory {cur}: {e}")
        want_nfc = nfc(want)
        exact = sorted(n for n in names if nfc(n) == want_nfc)
        if len(exact) > 1:
            raise Fault(
                f"{where}: {cur} holds {len(exact)} entries that normalise to {want_nfc!r} "
                f"({', '.join(repr(n) for n in exact)}); this gate cannot say which one the plan meant"
            )
        if exact:
            walked.append(exact[0])
            cur = os.path.join(cur, exact[0])
            continue
        fold = want_nfc.casefold()
        variant = sorted(n for n in names if nfc(n).casefold() == fold)
        if variant:
            return "variant", os.path.join(cur, variant[0]), "/".join(walked + [variant[0]])
        return "missing", None, "/".join(walked + [want])
    return "exact", cur, "/".join(walked)


def read_normalised(path, where):
    """Decode a target file to the one text form every text check keys on."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise Fault(f"{where}: cannot read {path}: {e}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise Fault(f"{where}: {path} is not UTF-8 text, so it cannot be compared as text: {e}")
    return nfc(text.replace("\r\n", "\n").replace("\r", "\n"))


def digest_of(path, where):
    return hashlib.sha256(read_normalised(path, where).encode("utf-8")).hexdigest()


def load(path):
    """Parse the assumption file. Every unparseable row is refused, never dropped."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise Fault(f"cannot read assumptions file {path}: {e}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise Fault(f"assumptions file {path} is not UTF-8: {e}")
    rows = []
    for n, line in enumerate(text.split("\n"), 1):
        if line.endswith("\r"):
            line = line[:-1]
        if line.strip() == "":
            continue
        if line.lstrip()[0] == "#":
            if "\t" in line:
                raise Fault(
                    f"line {n}: a '#' line holding a TAB is ambiguous - comment, or an "
                    f"assumption whose first field starts with '#'? Rewrite it"
                )
            continue
        where = f"line {n}"
        parts = line.split("\t")
        kind = parts[0]
        if kind not in KINDS:
            raise Fault(f"{where}: unknown assumption kind {kind!r}; expected one of {', '.join(KINDS)}")
        if kind in TWO_FIELD:
            if len(parts) != 2:
                raise Fault(f"{where}: '{kind}' takes exactly 2 TAB-separated fields, got {len(parts)}")
            arg = None
        elif kind == "unchanged":
            if len(parts) != 3:
                raise Fault(f"{where}: 'unchanged' takes exactly 3 TAB-separated fields, got {len(parts)}")
            arg = parts[2]
            if not HEX64.match(arg):
                raise Fault(f"{where}: 'unchanged' needs a bare 64-character sha256 hex digest, got {arg!r}")
            arg = arg.lower()
        else:
            if len(parts) < 3:
                raise Fault(f"{where}: '{kind}' takes 3 TAB-separated fields, got {len(parts)}")
            arg = line.split("\t", 2)[2]
            if arg.strip() == "":
                raise Fault(f"{where}: '{kind}' needs a literal with non-blank content; an empty "
                            f"or all-blank one holds against almost any file and checks nothing")
            if arg != arg.strip():
                raise Fault(f"{where}: the literal {arg!r} is padded with whitespace; a trailing "
                            f"space or TAB is an editor artefact that matches almost nothing, so "
                            f"a '{kind}' row would hold vacuously forever")
            for ch in LINE_BREAKING:
                if ch in arg:
                    raise Fault(f"{where}: the literal holds a line-breaking character; it cannot be written on one line")
            refuse_unkeyable(arg, where, "the literal")
            arg = nfc(arg)
        rows.append((n, kind, parts[1], split_path(parts[1], where), arg))
    if not rows:
        raise Fault(
            f"{path} states no assumptions. A plan that writes down nothing checkable "
            f"cannot be checked, and must not be consented to"
        )
    return rows


def run(root, rows):
    """Check every row. Returns the number that diverged."""
    diverged = 0

    def say(verdict, n, kind, raw, detail):
        print(f"{verdict:<7} line {n}: {kind} {raw}{' - ' + detail if detail else ''}")

    for n, kind, raw, comps, arg in rows:
        where = f"line {n}"
        status, real, shown = locate(root, comps, where)
        if kind == "exists":
            if status == "exact":
                say("HOLD", n, kind, raw, "")
                continue
            diverged += 1
            say("DIVERGE", n, kind, raw,
                f"the tree spells it {shown!r}" if status == "variant" else "not present")
            continue
        if kind == "absent":
            if status == "missing":
                say("HOLD", n, kind, raw, "")
                continue
            diverged += 1
            say("DIVERGE", n, kind, raw,
                f"a spelling variant is already present: {shown!r}" if status == "variant"
                else "already present - something created it since the plan was written")
            continue
        if status != "exact":
            diverged += 1
            say("DIVERGE", n, kind, raw,
                f"the tree spells it {shown!r}, so the assumption cannot be evaluated as stated"
                if status == "variant" else "not present, so the assumption cannot be evaluated")
            continue
        if kind == "unchanged":
            got = digest_of(real, where)
            if got == arg:
                say("HOLD", n, kind, raw, "")
            else:
                diverged += 1
                say("DIVERGE", n, kind, raw, f"planner read {arg[:12]}..., tree now holds {got[:12]}... (full: {got})")
            continue
        text = read_normalised(real, where)
        found = arg in text
        if (kind == "contains") == found:
            say("HOLD", n, kind, raw, "")
        else:
            diverged += 1
            say("DIVERGE", n, kind, raw,
                "the literal is gone" if kind == "contains" else "the literal has appeared")
    return diverged


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="plan-decay.py", allow_abbrev=False,
        description="Halt a fleet when the plan it is running stops describing the repo.")
    ap.add_argument("assumptions", nargs="?", help="TAB-separated assumption file written by the plan")
    # REQUIRED, no default. A default of '.' aims the whole plan at the process's
    # working directory without saying so, and an all-'absent' plan then holds
    # vacuously against an unrelated tree and exits 0 - a false green produced by an
    # ordinary wrong-cwd CI step, invisible to a caller that reads only the code.
    ap.add_argument("--root", required=True,
                    help="directory the assumption paths are relative to (required)")
    ap.add_argument("--digest", metavar="PATH", help="print this file's normalised-text digest and exit 3")
    args = ap.parse_args()
    try:
        # CPython hands back sys.stdout is None when fd 1 was closed before the process
        # started, and print() then silently does nothing. The verdict would still be
        # computed and still be returned - and every line of the report proving it would
        # be gone. Under this pack's first law a verdict nobody can read is a claim, so
        # the run is a fault, not a green.
        if sys.stdout is None:
            raise Fault("stdout is closed; a verdict whose report cannot be written is not evidence")
        root = Path(args.root)
        if not root.is_dir():
            raise Fault(f"--root {args.root!r} is not a directory")
        rootstr = str(root)
        if args.digest is not None:
            if args.assumptions is not None:
                raise Fault("--digest computes no verdict; do not pass an assumptions file with it")
            comps = split_path(args.digest, "--digest")
            status, real, shown = locate(rootstr, comps, "--digest")
            if status != "exact":
                raise Fault(f"--digest {args.digest!r}: {status} under --root {rootstr!r}"
                            + (f" (the tree spells it {shown!r})" if status == "variant" else ""))
            print(f"DIGEST {args.digest} {digest_of(real, '--digest')}")
            return 3
        if args.assumptions is None:
            raise Fault("an assumptions file is required (or --digest PATH)")
        rows = load(args.assumptions)
        diverged = run(rootstr, rows)
        print(f"CHECKED {len(rows)} assumption(s) against {rootstr} - "
              f"{len(rows) - diverged} held, {diverged} diverged")
        if diverged:
            print("HALT: the plan no longer describes this tree. Stop, back up, re-plan from the repo as it is.")
            return 1
        print("PLAN HOLDS: every stated assumption still matches the tree.")
        return 0
    except Fault as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        _code = main()
    except SystemExit as _exc:          # argparse usage errors and --help
        # The pack's standard tail maps a non-int payload onto 1 and None onto 0. Both
        # are VERDICT codes, and this script raises no SystemExit of its own: argparse
        # always passes an int (--help 0, usage 2). A SystemExit carrying anything else
        # is therefore a fault reaching the seal, not a divergence, so it leaves as 2.
        _code = _exc.code if isinstance(_exc.code, int) else 2
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
            # The pack's standard tail coerces (0, 1). This script also emits the
            # informational 3, which asserts "--digest printed a digest" - a claim a
            # failed flush falsifies, so 3 is coerced with the verdicts.
            if _code in (0, 1, 3):
                _code = 2
            try:
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
