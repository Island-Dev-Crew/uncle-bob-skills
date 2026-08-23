#!/usr/bin/env python3
"""review-record.py - refuse a review record that is a bare approval.

Usage: python3 review-record.py [--min N] <record-file>

Checks the SHAPE of a review record, never the judgment inside it.

A LINE is a run of characters between LF bytes - the file is split on '\\n'
alone, never str.splitlines(), which also breaks on \\r, \\x0b, \\x0c, \\x1c,
\\x1d, \\x1e, U+0085, U+2028 and U+2029 and would let one physical line the
reader sees as a '#' comment carry counted entries behind it. Before any line
is read, the whole record is refused (exit 2) if it holds a control character
other than TAB, LF and the CR of a CRLF pair, or U+2028/U+2029: those are the
characters that make the parser and the reader see different text, and a
record no reader can check is not a verdict. A line is BLANK when it is empty
after stripping whitespace.

Every line is either blank, a comment/prose line whose first non-space
character is '#', or an entry:

    FOUND      <id> <text...>
    FALSIFIED  <id> <text...>

Keywords are case-sensitive and must be uppercase; <id> is any run of
non-space characters; <text> must be non-empty. Ids must be distinct after
NFKC + casefold + NFC normalization, so 'A1' and 'a1' collide instead of both
counting, and so do fullwidth 'Ａ１' and NFD 'café'. An id carrying an
invisible character - Unicode category Cf, Cc, Zl or Zp, e.g. a zero-width
space no normalization form removes - is refused (exit 2) rather than counted
as a second id, because two ids that render identically are one id to every
reader. Anything else on a line is refused by line number - this parser drops
nothing silently.

Options:
    --min N     require at least N entries (default 1; N must be >= 1)
    -h, --help  print this usage and exit 0

Exit codes:
    0  the record carries >= N entries with distinct ids (also: --help)
    1  refused: too few entries, a duplicate id, or a line that is neither
       blank, comment, nor a well-formed entry
    2  usage error; unreadable/non-regular/oversize/undecodable file; a record
       carrying an invisible character (a control character anywhere, or a
       format character inside an id) that would make the parser and the
       reader see different text; or an internal failure - an error is never
       a verdict
"""
import os
import re
import stat
import sys
import unicodedata

ENTRY = re.compile(r"(FOUND|FALSIFIED)[ \t]+(\S+)[ \t]+(\S.*)")
KEYWORD_ISH = re.compile(r"(?i)(found|falsified)\b")
MIN_RE = re.compile(r"[0-9]{1,9}")
MAX_BYTES = 4 * 1024 * 1024
USAGE = "usage: review-record.py [--min N] <record-file>"

# Every control character except TAB (\x09) and LF (\x0a, the splitter), plus
# U+007F, the C1 range U+0080-U+009F (U+0085 NEL lives there) and the two
# Unicode separators U+2028/U+2029. CR (\x0d) is out of the class and handled
# by the first alternative: the CR of a CRLF pair is ordinary Windows line
# ending, a CR anywhere else is a line break str.splitlines() would honour and
# split("\n") would not. Checked BEFORE the comment rule, so a '#' line can
# never carry a hidden second line past the reader.
CONTROL_RE = re.compile(r"\r(?!\n)|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]")

# Invisible-but-not-control characters that cannot appear inside an entry id.
# Cc/Zl/Zp are already refused file-wide by CONTROL_RE; naming them here keeps
# the id rule true on its own terms rather than by borrowing another guard's
# coverage. Cf is the one this adds: zero-width and bidi format characters
# that no normalization form removes, so 'R<ZWSP>2' would otherwise count as a
# second id that renders exactly like the first.
INVISIBLE_CATEGORIES = ("Cf", "Cc", "Zl", "Zp")


def norm_key(text):
    """The one documented key function for id joins: NFKC, casefold, then NFC.

    NFKC folds compatibility spellings (fullwidth 'Ｒ２', superscript 'R²')
    onto their plain forms; casefold folds case and ligatures; the closing NFC
    re-composes what casefold may have decomposed, so the key is a single
    normal form and not a mixture.
    """
    return unicodedata.normalize(
        "NFC", unicodedata.normalize("NFKC", text).casefold()
    )


def invisible_in(text):
    """Return the first character of text in INVISIBLE_CATEGORIES, or None."""
    for ch in text:
        if unicodedata.category(ch) in INVISIBLE_CATEGORIES:
            return ch
    return None


def parse_args(argv):
    """Return (path, min_entries, error_or_None, help_wanted)."""
    path = None
    min_entries = 1
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-h", "--help"):
            return None, 0, None, True
        if arg == "--min" or arg.startswith("--min="):
            if arg == "--min":
                if i + 1 >= len(argv):
                    return None, 0, "error: --min needs a value", False
                value = argv[i + 1]
                i += 2
            else:
                value = arg[len("--min="):]
                i += 1
            if not MIN_RE.fullmatch(value):
                return None, 0, f"error: --min needs an integer of 1..9 digits, got {value!r}", False
            min_entries = int(value)
            if min_entries < 1:
                return None, 0, "error: --min must be >= 1; a record with no entries is the thing this gate refuses", False
            continue
        if arg.startswith("-") and arg != "-":
            return None, 0, f"error: unknown option {arg!r}", False
        if path is not None:
            return None, 0, "error: exactly one record file expected", False
        path = arg
        i += 1
    if path is None:
        return None, 0, "error: no record file given", False
    return path, min_entries, None, False


def read_record(path):
    """Return (text, bom_len, error_or_None). Refuses anything that is not a
    readable regular file of at most MAX_BYTES decodable as UTF-8 (BOM
    tolerated). bom_len is 3 when a BOM was stripped, so byte offsets reported
    later still point into the file on disk."""
    try:
        info = os.stat(path)
    except OSError as exc:
        return None, 0, f"error: cannot stat {path!r}: {exc.strerror or exc}"
    if not stat.S_ISREG(info.st_mode):
        return None, 0, f"error: {path!r} is not a regular file"
    if info.st_size > MAX_BYTES:
        return None, 0, f"error: {path!r} is {info.st_size} bytes, over the {MAX_BYTES}-byte limit"
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        return None, 0, f"error: cannot read {path!r}: {exc.strerror or exc}"
    if len(raw) > MAX_BYTES:
        return None, 0, f"error: {path!r} grew past the {MAX_BYTES}-byte limit while reading"
    bom_len = 3 if raw.startswith(b"\xef\xbb\xbf") else 0
    try:
        # utf-8-sig strips a leading BOM; invalid bytes still raise.
        return raw.decode("utf-8-sig"), bom_len, None
    except UnicodeDecodeError as exc:
        return None, 0, f"error: {path!r} is not valid UTF-8: {exc}"


def check_control(path, text, bom_len):
    """Return an error string if the record holds a character that would make
    the parser and the reader disagree about where a line ends, else None."""
    match = CONTROL_RE.search(text)
    if match is None:
        return None
    offset = bom_len + len(text[:match.start()].encode("utf-8"))
    char = match.group()
    return (
        f"error: {path!r}: control character U+{ord(char):04X} at byte offset {offset} - "
        "the parser and the reader would see different lines here; a record no reader "
        "can check is not a verdict"
    )


def diagnose(line):
    """Why a non-comment, non-blank line is not an entry."""
    head = line.split(maxsplit=1)[0] if line.split() else ""
    if head in ("FOUND", "FALSIFIED"):
        return "entry needs an id and non-empty text after the keyword"
    if KEYWORD_ISH.match(head):
        return "entry keyword must be uppercase FOUND or FALSIFIED"
    return "not a comment ('#...') and not a FOUND/FALSIFIED entry"


def scan(text):
    """Return (entries, problems, fatal_or_None).

    entries is a list of (kind, id, lineno). Lines are the runs between LF
    bytes; the trailing CR of a CRLF pair is dropped, and no other CR can
    reach here because check_control() refuses the file first. fatal is set
    when an id carries an invisible character - that is an exit-2 refusal, not
    a verdict, because the record cannot be read the way it renders.
    """
    entries = []
    problems = []
    seen = {}
    for lineno, raw in enumerate(text.split("\n"), start=1):
        if raw.endswith("\r"):
            raw = raw[:-1]
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ENTRY.fullmatch(line)
        if match is None:
            problems.append(f"line {lineno}: {diagnose(line)}: {line[:80]!r}")
            continue
        kind, ident = match.group(1), match.group(2)
        bad = invisible_in(ident)
        if bad is not None:
            return entries, problems, (
                f"error: line {lineno}: entry id {ident!r} carries invisible character "
                f"U+{ord(bad):04X} (category {unicodedata.category(bad)}) - two ids that "
                "render identically are one id to every reader"
            )
        key = norm_key(ident)
        if key in seen:
            problems.append(
                f"line {lineno}: duplicate entry id {ident!r} (first used on line {seen[key]})"
            )
            continue
        seen[key] = lineno
        entries.append((kind, ident, lineno))
    return entries, problems, None


def main():
    path, min_entries, err, help_wanted = parse_args(sys.argv[1:])
    if help_wanted:
        print(__doc__.strip())
        return 0
    if err is not None:
        print(err, file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    text, bom_len, err = read_record(path)
    if err is not None:
        print(err, file=sys.stderr)
        return 2
    err = check_control(path, text, bom_len)
    if err is not None:
        print(err, file=sys.stderr)
        return 2

    entries, problems, fatal = scan(text)
    if fatal is not None:
        print(fatal, file=sys.stderr)
        return 2
    found = sum(1 for kind, _, _ in entries if kind == "FOUND")
    falsified = len(entries) - found
    print(f"{path}: {len(entries)} entries ({found} FOUND, {falsified} FALSIFIED), "
          f"{len(problems)} malformed")
    for problem in problems:
        print(f"REFUSED {problem}")
    if problems:
        print("REFUSED: the record does not parse as a found-or-falsified list")
        return 1
    if len(entries) < min_entries:
        print(f"REFUSED: {len(entries)} entries, {min_entries} required - "
              "an approval without a found-or-falsified list is not a review")
        return 1
    print(f"OK: record carries a found-or-falsified list (min {min_entries}). "
          "Shape only - whether the hunt was real is a human's read.")
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
