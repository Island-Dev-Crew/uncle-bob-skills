#!/usr/bin/env python3
"""check-excusals.py — deterministic gate for the mutant excusal ledger.

Usage: python3 check-excusals.py <survivors-file> <ledger-file>

survivors-file  one surviving-mutant id per line (blank lines and '#' comments
                ignored) — the survivor list a mutant-hunt run emits after
                kill-tasks are exhausted. The id is the first token per line.
ledger-file     excusal entries. An entry starts at column 0 with the mutant id
                followed by indented lines. Reader-visible duplicate detection
                ignores Markdown quote/list/heading markers, links and inline
                decoration, removes the enumerated zero-width characters wherever
                they occur, and casefolds. The raw id still must match the survivor
                list exactly.
                Exactly four field names are read as fields — mutation,
                argument, excused-by, head — and every other indented line is
                text continuing the field above it, so a wrapped argument may
                start a line with a URL or any other 'word:' of its own. The
                argument must be at least 40 characters — a substance proxy,
                not a truth check. One reader-visible block per id, one line per
                field, and no decorated or re-cased mutant id at the head of an
                indented line, including behind a numbered marker. A known field
                behind a list marker is still a field, including a duplicate.

Exit 0 iff every survivor has a complete excusal. Exit 1 otherwise, listing
every unexcused or incomplete id. Exit 2 on usage, on an unreadable input, and
on a ledger that does not read one way: an id opening two entries, an id
heading an indented line instead of opening its entry at column 0, or a field
stated twice inside one entry. Those are malformed input rather than verdicts,
because each one lets the ruling depend on which block or line the parser kept.
Stale excusals (an id absent from the survivor list) warn without failing.
Same inputs always produce the same verdict.
"""
import re
import os
import sys
from pathlib import Path

REQUIRED = ("mutation", "argument", "excused-by", "head")
# The whole field vocabulary, not just the required part of it. A 'word:' the island never
# defined is prose, because arguments cite things — 'https://…', 'note:', 'items[i]: the
# bound' — and a parser that promoted every such line to a field would turn two cited URLs
# inside one argument into a field stated twice, and refuse a ledger nobody wrote wrong.
KNOWN_FIELDS = frozenset(REQUIRED)
# Characters that change the bytes of an id without changing the id a reader sees. A ledger is
# Markdown, so quote/list prefixes and inline decoration are presentation, not a new ruling.
# Zero-width characters are the inverse: they are bytes a reader cannot see at all, including
# when buried in the middle of an id rather than placed at an edge.
_ZERO_WIDTH = "\u200b\u200c\u200d\ufeff\u2060"
_INLINE_MARKUP = "`*_~"
_EDGE_DECORATION = "[]()<>\"'“”‘’,.;:!?"
_MARKDOWN_PREFIX = re.compile(
    r"^(?:>\s*|(?:[-+*]|\d+[.)])(?:\s+|$)|#{2,6}(?:\s+|$))"
)
_MARKDOWN_LINK = re.compile(r"^\[([^\]]+)\]\([^)]*\)$")
FIELD_BODY = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")


def reader_id(line: str) -> str:
    """Return the raw id token after Markdown quote/list/heading prefixes.

    Inline decoration and invisible codepoints stay in this raw value so survivor identity
    remains byte-for-byte. They are removed only by `canonical_id`, the duplicate detector.
    """
    text = line.lstrip()
    while text:
        match = _MARKDOWN_PREFIX.match(text)
        if not match:
            break
        text = text[match.end():].lstrip()
    return text.split()[0] if text else ""


def canonical_id(raw: str) -> str:
    """The reader-visible duplicate key; never the survivor identity."""
    visible = "".join(ch for ch in raw if ch not in _ZERO_WIDTH)
    link = _MARKDOWN_LINK.fullmatch(visible)
    if link:
        visible = link.group(1)
    visible = "".join(ch for ch in visible if ch not in _INLINE_MARKUP)
    return visible.strip(_EDGE_DECORATION).casefold()


def field_match(line: str):
    """Read a field after indentation and reader-visible list/quote markers."""
    if not line or not line[0].isspace():
        return None
    text = line.lstrip()
    while text:
        match = _MARKDOWN_PREFIX.match(text)
        if not match or text.startswith("#"):
            break
        text = text[match.end():].lstrip()
    return FIELD_BODY.match(text)


MIN_ARGUMENT_CHARS = 40


def read_survivors(path: Path) -> list[str]:
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            ids.append(s.split()[0])
    return ids


class Malformed(Exception):
    """A ledger that does not read one way. Never a verdict about the code under
    test, so it exits 2 and not 1."""


def opens_entry(line: str) -> bool:
    """True for a line that starts an entry: content, not a comment, at column 0."""
    return bool(line.strip()) and not line.lstrip().startswith("#") and not line[0].isspace()


def read_ledger(path: Path) -> dict[str, dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    # Inventory every top-level header before parsing any fields. Duplicate detection must run
    # before two blocks can be merged or one can be accepted as a stale neighbour. The key strips
    # only what a Markdown reader cannot distinguish; the raw id still keys `entries` and still
    # has to match the survivor list byte-for-byte before it excuses anything.
    entry_ids: dict[str, tuple[str, int]] = {}
    header_ids: dict[int, str] = {}
    for n, line in enumerate(lines, 1):
        if not opens_entry(line):
            continue
        raw = reader_id(line)
        key = canonical_id(raw)
        header_ids[n] = raw
        if key and key in entry_ids:
            prior, first = entry_ids[key]
            raise Malformed(
                f"{path}:{n}: '{raw}' opens a second reader-visible entry for '{prior}'; "
                f"the first is at line {first}. A mutant gets one ruling even when case, "
                "Markdown decoration, or invisible characters make the bytes differ."
            )
        if key:
            entry_ids[key] = (raw, n)
    # A Markdown heading is comment-shaped to the ledger grammar, but `## M1` is visibly a
    # second M1 block, not prose. Compare only headings whose first visible token collides with
    # an opened id, so ordinary fixture commentary remains commentary.
    for n, line in enumerate(lines, 1):
        if opens_entry(line) or not re.match(r"^\s*#{2,6}\s+", line):
            continue
        named = reader_id(line)
        opened = entry_ids.get(canonical_id(named))
        if opened:
            real, first = opened
            raise Malformed(
                f"{path}:{n}: heading '{named}' opens a second reader-visible entry for "
                f"'{real}'; the first is at line {first}. Markdown headings do not mint a "
                "second mutant identity."
            )
    entries: dict[str, dict[str, str]] = {}
    unmeasured: dict[str, list[str]] = {}
    current = last = None
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if opens_entry(line):
            mid = header_ids[n]
            entries[mid] = {}
            current, last = mid, None
            continue
        m = field_match(line)
        name = m.group(1).lower() if m else None
        if name not in KNOWN_FIELDS:
            # Not a field, so it is either prose continuing the field above or an entry
            # header somebody pushed off column 0 — and those two read very differently
            # to a human while parsing identically. An id at the head of the line settles
            # it: a reader sees a second block there, so the parser must not quietly file
            # the lines under it into the block above.
            named = reader_id(line)
            key = canonical_id(named)
            opened = entry_ids.get(key)
            if opened:
                real, first = opened
                if key == canonical_id(current or ""):
                    site = f"heads an indented line inside its own block, which opens at line {first}"
                elif current:
                    site = f"heads an indented line inside '{current}'s block"
                    site += f", and the ledger opens '{real}' at line {first}"
                else:
                    site = "heads an indented line before any block has opened"
                raise Malformed(
                    f"{path}:{n}: '{named}' {site}. Entries begin at column 0; an "
                    "indented one hides a second ruling inside the first instead of "
                    "joining them. Markdown quote, bullet, and numbered-list markers do "
                    "not change the id. Give this mutant one block at column 0 stating "
                    "the one ruling it gets, or fold its fields into the block above and "
                    "delete the header. Argument prose names a mutant inside a sentence, "
                    "never at the head of a line."
                )
        if current is None:
            continue
        if name in KNOWN_FIELDS:
            # Same reason one level down: last-wins would hand the verdict to line
            # order, so an effort claim placed above a real argument would be erased
            # by it. A continuation line (the elif below) extends one field and is
            # not a second statement of it.
            if name in entries[current]:
                raise Malformed(
                    f"{path}:{n}: '{current}' states '{name}:' twice — a field the reader "
                    "and the parser could resolve differently is not evidence"
                )
            entries[current][name] = m.group(2).strip()
            last = name
        elif last:
            # A field-shaped line whose name this island does not define — `note:`, `todo:`, a
            # bare `https://…` — is not an error (treating it as one turned two cited URLs inside
            # one argument into MALFORMED). But it is not argument SUBSTANCE either, and counting
            # it as continuation let it pad a thin argument past the 40-character floor: a
            # 17-character "could not kill it", the island's own canonical example of effort worn
            # as equivalence, went from FAIL to GREEN behind one `note:` line. It is carried so
            # nothing is lost from the record, and excluded from what the floor measures.
            if m and m.group(1).lower() not in KNOWN_FIELDS:
                unmeasured.setdefault(current, []).append(line.strip())
            else:
                entries[current][last] = (entries[current][last] + " " + line.strip()).strip()
    return entries


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    survivors_path, ledger_path = Path(sys.argv[1]), Path(sys.argv[2])
    for p in (survivors_path, ledger_path):
        if not p.is_file():
            print(f"FAIL missing input file: {p}")
            return 2
    survivors = read_survivors(survivors_path)
    try:
        ledger = read_ledger(ledger_path)
    except Malformed as exc:
        print(f"MALFORMED {exc}")
        return 2

    problems = []
    for mid in survivors:
        entry = ledger.get(mid)
        if entry is None:
            problems.append(f"{mid}: UNEXCUSED — no ledger entry; kill it or argue equivalence")
            continue
        missing = [f for f in REQUIRED if not entry.get(f)]
        if missing:
            problems.append(f"{mid}: entry incomplete — missing {', '.join(missing)}")
        arg = entry.get("argument", "")
        if arg and len(arg) < MIN_ARGUMENT_CHARS:
            problems.append(
                f"{mid}: argument too thin ({len(arg)} chars < {MIN_ARGUMENT_CHARS}) — "
                "state why NO test can observe the change"
            )
    for mid in ledger:
        if mid not in survivors:
            print(f"WARN {mid}: stale excusal — not in the current survivor list; prune it")

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        print(f"{len(problems)} problem(s) across {len(survivors)} survivor(s); gate RED")
        return 1
    print(f"OK   {len(survivors)} survivor(s), all excused with complete entries; gate GREEN")
    return 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython flushes
    # the std streams after main() returns, and if that flush raises — a pipe whose reader
    # has already gone, which is the ordinary `gate.py … | head` idiom — it REPLACES the
    # status this script chose with 120, a code no table here names. An unhandled exception
    # is the other leak, and the worse one: it exits 1, and 1 is a VERDICT here, so a crash
    # would be read as a real finding about the code under test.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse raises this from inside
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:
        _code = 2
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
