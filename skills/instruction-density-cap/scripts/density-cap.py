#!/usr/bin/env python3
"""density-cap.py - count the simultaneous directives in a prompt file, fail past a cap.

Usage:
  python3 density-cap.py FILE [--cap N] [--profile NAME] [--show]

Counting rule (deterministic; at most ONE unit per line):
  D-a  a markdown list item outside a fenced code block: a bullet marker
       ("-", "*", "+", and the non-markdown glyphs bullet/triangle/square/circle/
       middot/en-dash/em-dash/arrow/guillemet) or an ordinal ("1.", "1)", "R1.",
       "a)", and a short word label in front of one: "Rule 1.", "Step 3)"), followed
       by whitespace.
  D-b  a markdown table row outside a fenced code block (a line whose first non-space
       character is "|"), excluding the single |---|:--:| delimiter row that immediately
       follows a table's header - a rules table spends one row per rule, so each row is
       a unit. The delimiter is positional: a body row whose cells hold only dashes or
       colons ("| - | -- |") is a row and is counted.
  D-c  any other line outside a fenced code block carrying a whole-word directive
       modal: must, shall, should, never, always, required, mandatory, forbidden,
       prohibited, avoid, ensure, "do not", "don't" (straight or curly apostrophe).

Robustness, by construction:
  - decoded UTF-8 strict (a decode failure is exit 2, never a verdict);
  - a decoded NUL character is exit 2, never a verdict: UTF-16LE/BE and UTF-32 without
    a BOM are VALID UTF-8 when the text is ASCII, and would otherwise count 0 in silence
    because every marker and modal is split by U+0000. The class is closed by the NUL,
    not by enumerating encodings;
  - a leading BOM is dropped; CR, CRLF and LF line endings all split the same way;
  - text is normalised to NFKC before matching, so NFD input (routine on macOS) counts
    identically AND the invisible-space class folds to a plain space: a marker followed
    by NBSP (U+00A0), FIGURE SPACE (U+2007), NARROW NBSP (U+202F) or IDEOGRAPHIC SPACE
    (U+3000) counts exactly like its ASCII twin. Pasting from Word, Google Docs, Notion
    or a web page emits these routinely, and no editor or diff renders them. Every
    remaining Unicode space separator (category Zs, i.e. U+1680) is then folded to
    U+0020 too, so the class is closed by definition, not by enumeration;
  - zero-width and bidi format characters (U+200B-200F, U+202A-202E, U+2060-2064,
    U+00AD, U+FEFF) are removed before matching, so "-" + ZWSP + " " is still a marker;
  - matching is case-insensitive and whole-word, so MUST, Must and must all count and
    "mustard" does not;
  - a blockquote prefix (">", nested) is stripped before classifying, so indenting a
    rule into a quote does not hide it;
  - a list marker is recognised at any indent, so a deeply nested rule still counts.

Fenced code blocks (``` or ~~~, opener indented up to 3 spaces, closer of the same
character and at least as long) are EXCLUDED - a documented blind spot, evidenced by
scripts/fixtures/fence-blind-spot.md. A fence need not be deliberate: ANY line that begins,
after up to three spaces or tabs, with 3+ backticks or tildes opens one, so a prose line
about fencing silences every rule after it up to the next closer - evidenced by
scripts/fixtures/prose-fence.md. An UNTERMINATED fence is not honoured: its body
is counted as ordinary text, so an unclosed fence cannot silence the rest of the file.
Indented (4-space) code blocks are not detected at all; their lines are counted.

NOT counted, by construction: a rule written as a bare imperative sentence with no
list marker, no table pipe and no modal ("Use two-space indentation everywhere.")
scores zero. Closing that would need a semantic judge, which this proxy is not; the
hole is evidenced by scripts/fixtures/imperative-blind-spot.md.

Caps:
  --cap N        integer 1..100000; wins over --profile.
  --profile NAME advisory default cap per model class, case-insensitive:
                 reasoning=150, standard=75. Unknown name is exit 2.
  With neither flag the cap is the "reasoning" profile default.

Flags:
  --show         list every counted unit as "line:kind:excerpt" (ASCII-escaped).

Exit codes (the complete set this script can emit):
  0  success: units <= cap (also the code for --help on a live stdout; --help with a
     dead stdout exits 2, like any other unflushable stream)
  1  units > cap - the verdict
  2  usage error, unreadable file, an undecodable file, a file containing a NUL, an
     output stream that could not be flushed, or any internal failure
"""
import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path

PROFILES = {"reasoning": 150, "standard": 75}
CAP_MIN = 1
CAP_MAX = 100000

# A list marker at any indent; the trailing space requirement keeps *emphasis* and
# thematic breaks (---, ***) out. The glyph class covers markers markdown does not
# define but rules files use anyway (bullet, triangle, squares, circles, middot,
# en/em dash, arrow, guillemet); the ordinal branch accepts a short alphabetic label
# ("R1.", "A2)"), an optional short word label before it ("Rule 1.", "Step 3)") and a
# bare letter ("a)"), not only bare digits. Over-counting an em-dash aside or a
# "Section 3." cross-reference is the safe direction for a gate whose failure mode is a
# false green.
# Markers are recognised by Unicode PROPERTY, not by an enumeration. A fixed list of
# glyphs silently missed every marker outside it: a bolded "**1.**", an emoji bullet,
# and U+25A0 (Google Docs' level-3 bullet, while its level-1 and level-2 glyphs were on
# the list) each counted as zero, so a rules file a human plainly reads as a numbered
# list consented against any cap. Total silence is the worst false-green shape here.
# Over-counting an em-dash aside or a "Section 3." cross-reference is the safe
# direction for a gate whose failure mode is a false green.
MARKER_CATEGORIES = frozenset(("Pd", "Po", "Sm", "Sk", "So"))
# Handled by other branches, so never treated as a list marker.
MARKER_EXCLUDED = frozenset("#|>`")
# The ordinal branch accepts a short alphabetic label ("R1.", "A2)"), an optional short
# word label before it ("Rule 1.", "Step 3)") and a bare letter ("a)"), not only digits.
ORDINAL_RE = re.compile(
    r"^[ \t]*(?:(?:[A-Za-z]{1,8}[ \t]+)?[A-Za-z]{0,3}\d{1,9}[.)]"
    r"|[A-Za-z][.)])[ \t]+\S"
)
# A leading emphasis run is stripped before classifying, so "**1.** Rebase before ..."
# reaches the ordinal branch instead of vanishing. Only stripped when the same run
# closes later on the line, which leaves a real "* item" bullet untouched.
EMPHASIS_RE = re.compile(r"^([ \t]*)([*_]{1,3})(?=\S)")


def strip_emphasis(line):
    """Remove a leading emphasis run and its closer, or return the line unchanged."""
    m = EMPHASIS_RE.match(line)
    if not m:
        return line
    run, rest = m.group(2), line[m.end():]
    close = rest.find(run)
    if close == -1:
        return line
    return m.group(1) + rest[:close] + rest[close + len(run):]


def is_list_line(line):
    """True when the line opens with a list marker or an ordinal label."""
    line = strip_emphasis(line)
    stripped = line.lstrip(" \t")
    if stripped:
        head = stripped[0]
        if head not in MARKER_EXCLUDED and (
            head in "-*+" or unicodedata.category(head) in MARKER_CATEGORIES
        ):
            rest = stripped[1:]
            if rest[:1] in (" ", "\t") and rest.strip():
                return True
    return bool(ORDINAL_RE.match(line))


# Zero-width and bidi format characters: invisible in every editor and diff, so they
# are removed rather than trusted. U+FEFF here is an interior one; a leading BOM is
# reported separately.
INVISIBLE_RE = re.compile(
    "[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u00ad\ufeff]"
)
# Nested blockquote prefix, stripped before classifying.
QUOTE_RE = re.compile(r"^[ \t]*(?:>[ \t]?)+")
# A markdown table row, and the |---|:--:| delimiter row that is not one. The delimiter
# is POSITIONAL, as markdown requires: only the line immediately after a table's header
# row is dropped. A later body row whose cells happen to hold nothing but dashes or
# colons ("| - | -- |") is a row and is counted.
TABLE_RE = re.compile(r"^[ \t]*\|")
TABLE_SEP_RE = re.compile(r"^[ \t]*\|[ \t|:-]*$")

_MODAL_WORDS = (
    "must", "shall", "should", "never", "always", "required", "mandatory",
    "forbidden", "prohibited", "avoid", "ensure",
)
_MODAL_ALTS = [re.escape(w) + r"\b" for w in _MODAL_WORDS]
_MODAL_ALTS += [r"do[ \t]+not\b", "don[\u2019\u02bc']t\\b"]
MODAL_RE = re.compile(r"\b(?:" + "|".join(_MODAL_ALTS) + ")", re.IGNORECASE)

FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")


def fenced_indices(lines):
    """Line indices inside a CLOSED fenced code block. An unterminated opener is
    discarded, so its body falls back to ordinary counted text (fail closed)."""
    inside = set()
    i, n = 0, len(lines)
    while i < n:
        m = FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        marker = m.group(1)
        char, width = marker[0], len(marker)
        close = None
        j = i + 1
        while j < n:
            m2 = FENCE_RE.match(lines[j])
            if m2 and m2.group(1)[0] == char and len(m2.group(1)) >= width and not m2.group(2).strip():
                close = j
                break
            j += 1
        if close is None:
            i += 1  # unterminated: not a fence at all
            continue
        inside.update(range(i, close + 1))
        i = close + 1
    return inside


def ascii_excerpt(s, limit=60):
    s = s.strip()[:limit]
    return s.encode("ascii", "backslashreplace").decode("ascii")


def count_units(text):
    """Return (units, notes) where units is a list of (lineno, kind, excerpt)."""
    notes = []
    if text.startswith("\ufeff"):
        text = text[1:]
        notes.append("note: leading BOM dropped before counting")
    # NFKC, not NFC: NFC folds NFD accents but leaves the Unicode space separators
    # alone, so "-" + U+00A0 would miss the D-a marker and the whole file would count
    # zero. NFKC maps NBSP / FIGURE SPACE / NARROW NBSP / IDEOGRAPHIC SPACE to U+0020.
    text = unicodedata.normalize("NFKC", text)
    # NFKC folds every Unicode space separator except U+1680 (OGHAM SPACE MARK).
    # Fold the Zs category by definition rather than by enumeration, so no space
    # separator can sit between a list marker and its text unrecognised.
    text = "".join(" " if ch != " " and unicodedata.category(ch) == "Zs" else ch for ch in text)
    text, removed = INVISIBLE_RE.subn("", text)
    if removed:
        notes.append(f"note: {removed} zero-width/bidi character(s) removed before counting")
    lines = text.splitlines()
    skip = fenced_indices(lines)
    if skip:
        notes.append(f"note: {len(skip)} line(s) inside closed code fences excluded")
    units = []
    # None = not in a table; "header" = the previous line opened one, so the next pipe
    # line may be its delimiter; "body" = the delimiter slot is spent, every further
    # pipe line is a row. Any blank, skipped or non-pipe line ends the table.
    table_state = None
    for idx, raw in enumerate(lines):
        if idx in skip:
            table_state = None
            continue
        line = QUOTE_RE.sub("", raw)
        if not line.strip():
            table_state = None
            continue
        if is_list_line(line):
            table_state = None
            units.append((idx + 1, "list", ascii_excerpt(line)))
        elif TABLE_RE.match(line):
            if table_state == "header" and TABLE_SEP_RE.match(line):
                table_state = "body"          # the one delimiter row, dropped
            else:
                units.append((idx + 1, "row", ascii_excerpt(line)))
                table_state = "body" if table_state else "header"
        else:
            table_state = None
            if MODAL_RE.search(line):
                units.append((idx + 1, "modal", ascii_excerpt(line)))
    return units, notes


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Count simultaneous directives in a prompt file and fail past a cap.",
        add_help=True,
    )
    ap.add_argument("file", help="prompt file to count (CLAUDE.md, AGENTS.md, a system prompt)")
    ap.add_argument("--cap", type=int, default=None, help=f"integer cap {CAP_MIN}..{CAP_MAX}; wins over --profile")
    ap.add_argument("--profile", default=None, help="advisory cap per model class: reasoning|standard")
    ap.add_argument("--show", action="store_true", help="list every counted unit")
    args = ap.parse_args()

    if args.profile is not None:
        key = args.profile.strip().lower()
        if key not in PROFILES:
            print(f"error: unknown --profile {args.profile!r}; choose from {sorted(PROFILES)}", file=sys.stderr)
            return 2
        cap, source = PROFILES[key], f"profile {key}"
    else:
        cap, source = PROFILES["reasoning"], "profile reasoning (default)"
    if args.cap is not None:
        if not (CAP_MIN <= args.cap <= CAP_MAX):
            print(f"error: --cap must be an integer {CAP_MIN}..{CAP_MAX}, got {args.cap}", file=sys.stderr)
            return 2
        cap, source = args.cap, "--cap"

    path = Path(args.file)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        print(f"error: cannot read {ascii_excerpt(str(path), 200)}: {type(exc).__name__}", file=sys.stderr)
        return 2
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"error: {ascii_excerpt(str(path), 200)} is not valid UTF-8: {exc.reason}", file=sys.stderr)
        return 2
    if "\x00" in text:
        # UTF-16LE/BE and UTF-32 WITHOUT a BOM holding ASCII are valid UTF-8: every
        # character arrives followed by U+0000, so no marker and no modal can ever
        # match and the file would count 0 in total silence. A NUL is never legitimate
        # in a prompt, so refuse the whole class by definition rather than by encoding.
        print(
            f"error: {ascii_excerpt(str(path), 200)} contains a NUL character; it is not a "
            "text prompt (UTF-16/UTF-32 without a BOM decodes this way and would count 0)",
            file=sys.stderr,
        )
        return 2

    units, notes = count_units(text)
    for note in notes:
        print(note)
    if args.show:
        for lineno, kind, excerpt in units:
            print(f"  {lineno}:{kind}:{excerpt}")
    total = len(units)
    if total > cap:
        print(f"FAIL D1 {total} directives exceeds cap {cap} ({source})")
        print(f"     over by {total - cap}: split the task, gate the checkable rules, or cut")
        return 1
    print(f"OK   D1 {total} directives within cap {cap} ({source})")
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
