#!/usr/bin/env python3
"""metric-register.py - rule on a register of enforced metrics.

Usage: python3 metric-register.py [--today YYYY-MM-DD] REGISTER.tsv
       python3 metric-register.py --help

REGISTER.tsv lists one *enforced* metric per line in four TAB-separated fields:

    metric <TAB> threshold <TAB> corrupts <TAB> review

`corrupts` names the behaviour that enforcing this metric might corrupt. `review`
is the ISO date (YYYY-MM-DD) on which the threshold is next re-examined. There is
no header line: a line whose first non-space character is '#' AND which contains
no TAB is a comment, while a '#' line that does contain TABs is parsed as data, so
a metric named '#-of-functions-over-30' is ruled on rather than silently dropped.

Verdicts, one per row, first breach reported:
    REVIEWED   clean - a behaviour is named and the review date has not arrived
    UNGUARDED  the row names no metric (empty, or only spacing and punctuation),
               no enforced threshold (empty, punctuation, or an evasion such as
               'TBD' / 'tbd (see JIRA-12)'), or no corruptible behaviour ('none',
               '- none -', 'none yet' - an evasion trailed only by hedge words is
               still that evasion)
    DUE        the review date has arrived or passed - the threshold is unexamined
    DUPLICATE  a second row under the same metric key - case, Unicode form,
               spacing, dashes, connectors, math symbols and trailing sentence
               punctuation are all folded away before the join, so one twin
               cannot go stale unseen behind a respelling

Exit codes:
    0  every row REVIEWED
    1  at least one UNGUARDED, DUE, or DUPLICATE row
    2  --help, a usage error, an unreadable or undecodable file, a row without
       exactly four fields, an unparseable date, an empty register, an internal
       failure of any kind, or a stream that could not be flushed

The gate rules on *declaration*, never on whether the named behaviour is the real
one or the review actually happened. Both of those are judgment; see SKILL.md.
"""
import argparse
import os
import re
import sys
import unicodedata
from datetime import date

# ASCII digits only. `\d` would admit fullwidth and Arabic-Indic digits, which
# int() then happily parses into a date nobody wrote.
ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# Control, format (incl. zero-width), and every space separator. Folded to spaces
# so an "empty" field padded with U+200B cannot read as substance.
INVISIBLE = {"Cc", "Cf", "Zs", "Zl", "Zp"}

# Exact phrases only, tested after folding - never a substring test, so
# "none of the coverage behaviours survive" is not mistaken for "none".
EVASIONS = {
    "-", "--", "---", ".", "..", "...", "?", "??", "???", "*",
    "n/a", "na", "n.a", "n.a.", "n a", "nil", "null", "no", "nope", "nah",
    "none", "none known", "no known risk", "no risk", "no idea", "no clue",
    "no comment", "dunno", "nothing", "not applicable", "not known",
    "not sure", "tbc", "tbd", "to be confirmed", "to be determined", "todo",
    "unclear", "undecided", "unknown", "pending", "wip",
}

# A hedge adds no behaviour and no number. An evasion trailed by nothing but
# these tokens is still that evasion, so "nil" cannot become substance by
# growing one word into "nil so far". The remainder must be *entirely* hedge,
# which is what keeps "none of the coverage behaviours survive" substantive.
HEDGE_TOKENS = {
    "a", "afaik", "and", "as", "at", "atm", "can", "clue", "comment",
    "currently", "far", "for", "guess", "i", "idea", "ideas", "if", "know",
    "knowledge", "known", "moment", "much", "my", "now", "of", "or", "really",
    "right", "so", "still", "sure", "that", "the", "then", "think", "this",
    "time", "to", "yet",
}

# A bracketed aside can hide an evasion behind a pointer: "tbd (see JIRA-12)".
# Stripped only for the evasion test, never for display or for the join key.
ASIDE = re.compile(r"[(\[{][^()\[\]{}]*[)\]}]")

# Wrappers a clause can be dressed in without changing a word of it: "none",
# 'none', (none) and [none] are one evasion wearing four costumes.
WRAPPERS = "\"'`“”‘’()[]{}<>«»"
TRAILING = ".!;,:"

# Separator categories squeezed out of a metric's join key: dash punctuation
# (Pd - hyphen, en dash, non-breaking hyphen), connector punctuation
# (Pc - underscore) and math symbols (Sm - U+2212 MINUS SIGN, which is not Pd
# and would otherwise spell one metric two ways). Space classes are already
# folded to " " by fold().
SEPARATORS = {"Pd", "Pc", "Sm"}

MIN_LETTERS = 3


class Fault(Exception):
    """Input this tool cannot rule on. Always exit 2, never a verdict."""


def fold(text):
    """The one normalization every text field passes through: NFKC (which also
    composes NFD input), invisibles to spaces, whitespace runs collapsed, trimmed."""
    t = unicodedata.normalize("NFKC", text)
    t = "".join(" " if unicodedata.category(ch) in INVISIBLE else ch for ch in t)
    return " ".join(t.split())


def peelable(ch):
    """True for a mark that dresses a clause without changing a word of it.

    A category test, not an enumeration. Hand-listed wrappers and sentence
    punctuation left every other mark as a way through: 'none?' and '-none-'
    read as substance and the row passed REVIEWED, which is the natural way an
    unsure author fills a corruption clause rather than hostile input.
    """
    category = unicodedata.category(ch)
    return category.startswith("P") or category in ("Sm", "Sk")


def bare(text):
    """A folded, casefolded field stripped of wrapping and punctuation marks,
    peeled until stable, for the exact-phrase evasion test. Spaces are kept, so
    'none known' still matches."""
    t = fold(text).casefold()
    while True:  # peels alternating layers: (none). -> (none) -> none
        start, end = 0, len(t)
        while start < end and peelable(t[start]):
            start += 1
        while end > start and peelable(t[end - 1]):
            end -= 1
        peeled = t[start:end]
        if peeled == t:  # length strictly decreases until it does, so this ends
            return " ".join(peeled.split())
        t = peeled


def metric_key(text):
    """The join key for duplicate detection: `bare` with every space, dash and
    connector punctuation squeezed out. Letter case, NFC/NFD, spacing, and the
    hyphen / underscore / en-dash / non-breaking-hyphen / soft-hyphen spellings
    of one metric therefore collide instead of each passing separately. What it
    still does not join - interior punctuation, abbreviations, plurals, synonyms
    - is a disclosed limit; see fixtures/duplicate-blind-spot.tsv.

    A name made only of these squeezed characters folds to the empty string.
    That is not a join failure: corruption_fault refuses such a row as naming no
    metric before judge() ever reaches the duplicate lookup."""
    t = bare(text).rstrip("?*" + TRAILING)
    return "".join(
        ch for ch in t
        if ch != " " and unicodedata.category(ch) not in SEPARATORS
    )


def substance(text):
    """`bare` with purely decorative tokens dropped - a token every character of
    which is a dash, connector or math symbol. '- none -' and '– none –' are
    both 'none'; a field that is only decoration reduces to the empty string."""
    return " ".join(
        token for token in bare(text).split()
        if any(unicodedata.category(ch) not in SEPARATORS for ch in token)
    )


def evasion_phrase(text):
    """Return the evasive phrase this field reduces to, or None if it says something.

    Passes, all exact-phrase and all whole-token, never substring:
      1. the bare field itself ('none', '(NONE).', 'TBD');
      2. the bare field with bracketed asides removed ('tbd (see JIRA-12)');
      3. either of those with decorative dash tokens dropped ('– none –');
      4. any of those as a leading evasion whose entire remainder is hedge
         tokens ('none yet', 'n/a for now', 'none that i can think of').
    A remainder carrying any non-hedge word keeps the field, so 'none of the
    coverage behaviours survive' and 'probably nothing much' are not evasions."""
    phrase = bare(text)
    unpeeled = " ".join(fold(text).casefold().split())
    if not phrase:
        # The category peel empties a punctuation-only field, and that spelling is
        # itself an evasion ('?', '--', '...'), so test it before giving up.
        return unpeeled if unpeeled in EVASIONS else None
    candidates = [phrase]
    if unpeeled and unpeeled not in candidates:
        candidates.append(unpeeled)
    trimmed = bare(ASIDE.sub(" ", fold(text)))
    if trimmed and trimmed != phrase:
        candidates.append(trimmed)
    for plain in list(candidates):
        stripped = substance(plain)
        if stripped and stripped not in candidates:
            candidates.append(stripped)
    for candidate in candidates:
        if candidate in EVASIONS:
            return candidate
    for candidate in candidates:
        tokens = candidate.split()
        for cut in range(min(len(tokens), 4), 0, -1):
            if " ".join(tokens[:cut]) not in EVASIONS:
                continue
            rest = [t.strip(WRAPPERS + TRAILING + "-") for t in tokens[cut:]]
            if rest and all(t in HEDGE_TOKENS for t in rest if t):
                return candidate
            break
    return None


def letter_count(text):
    return sum(1 for ch in fold(text) if unicodedata.category(ch).startswith("L"))


def parse_date(text):
    """Return a datetime.date, or None if the text is not an ASCII ISO date."""
    token = "".join(ch for ch in text if unicodedata.category(ch) not in INVISIBLE)
    if not ISO_DATE.fullmatch(token):
        return None
    try:
        return date(int(token[0:4]), int(token[5:7]), int(token[8:10]))
    except ValueError:  # 2026-02-30, month 00, day 00
        return None


def read_rows(path):
    """Return [(lineno, [metric, threshold, corrupts, review])]. Raises Fault."""
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("utf-8-sig")  # utf-8-sig strips a leading BOM
    except UnicodeDecodeError as exc:
        raise Fault(f"{path}: not valid UTF-8: {exc}") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    rows = []
    for lineno, line in enumerate(text.split("\n"), start=1):
        # Both skips are guarded on "\t" not in line, so no line carrying TAB-separated
        # fields can ever be dropped in silence - not a comment-shaped metric name, and
        # not a row of four empty fields, which must reach the parser and be refused.
        if "\t" not in line and (not line.strip() or line.lstrip().startswith("#")):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise Fault(
                f"{path} line {lineno}: expected 4 tab-separated fields, found {len(fields)}"
            )
        rows.append((lineno, fields))
    return rows


def corruption_fault(metric, threshold, corrupts):
    """Return the reason this row guards nothing, or None if it names a behaviour."""
    # metric_key, not fold: a name made only of spaces, dashes, connectors or
    # math symbols folds to an empty join key, and an empty key skips the
    # duplicate lookup. Refusing it here means two rows both named '-' are
    # UNGUARDED rather than a silent pair of REVIEWED twins.
    if not metric_key(metric):
        return "row names no metric"
    if not fold(threshold):
        return "names no enforced threshold - there is nothing to review"
    if not substance(threshold):
        return (
            f"names no enforced threshold - {fold(threshold)!r} is punctuation, "
            "not a threshold"
        )
    if not any(unicodedata.category(ch).startswith(("L", "N")) for ch in fold(threshold)):
        return (
            f"names no enforced threshold - {fold(threshold)!r} carries no letter or "
            "digit, so there is nothing to review"
        )
    evasive = evasion_phrase(threshold)
    if evasive is not None:
        return f"names no enforced threshold - {evasive!r} is an evasion, not a threshold"
    folded = fold(corrupts)
    if not folded:
        return "names no behaviour it might corrupt: the field is empty"
    phrase = evasion_phrase(corrupts)
    if phrase is not None:
        return f"names no behaviour it might corrupt: {phrase!r} is an evasion, not a behaviour"
    restated = metric_key(corrupts)
    if restated and restated in (metric_key(metric), metric_key(threshold)):
        return "names no behaviour it might corrupt: it restates the metric"
    if letter_count(corrupts) < MIN_LETTERS:
        return (
            f"names no behaviour it might corrupt: {folded!r} carries fewer than "
            f"{MIN_LETTERS} letters"
        )
    return None


def judge(rows, today):
    """Return (lines, counts). One verdict per row; the first breach found wins."""
    lines, seen = [], {}
    counts = {"REVIEWED": 0, "UNGUARDED": 0, "DUE": 0, "DUPLICATE": 0}
    for lineno, (metric, threshold, corrupts, review) in rows:
        label = fold(metric) or f"(line {lineno})"
        key = metric_key(metric)
        when = parse_date(review)
        if when is None:
            raise Fault(f"line {lineno}: review date is not an ISO YYYY-MM-DD date: {review!r}")
        reason = corruption_fault(metric, threshold, corrupts)
        if key and key in seen:
            verdict = "DUPLICATE"
            note = f"same metric key as line {seen[key]}; one twin goes stale unnoticed"
        elif reason is not None:
            verdict, note = "UNGUARDED", reason
        elif when <= today:
            days = (today - when).days
            verdict = "DUE"
            note = f"review {when.isoformat()} came due " + ("today" if days == 0 else f"{days} days ago")
        else:
            verdict = "REVIEWED"
            note = f"corrupts: {fold(corrupts)} | review {when.isoformat()}, {(when - today).days} days out"
        if key and key not in seen:
            seen[key] = lineno
        counts[verdict] += 1
        lines.append(f"{verdict:<10} {label}  [{note}]")
    return lines, counts


def main():
    parser = argparse.ArgumentParser(add_help=False, prog="metric-register.py")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--today", default=None, metavar="YYYY-MM-DD")
    parser.add_argument("register", nargs="?")
    args = parser.parse_args()

    if args.help or args.register is None:
        print(__doc__.strip())
        return 2

    today = date.today()
    if args.today is not None:
        today = parse_date(args.today)
        if today is None:
            print(f"error: --today must be an ASCII YYYY-MM-DD date, got {args.today!r}", file=sys.stderr)
            return 2

    try:
        rows = read_rows(args.register)
        if not rows:
            raise Fault(f"{args.register}: register lists no metrics - an empty register does not pass")
        lines, counts = judge(rows, today)
    except Fault as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {args.register}: {exc}", file=sys.stderr)
        return 2

    for line in lines:
        print(line)
    print(
        f"{len(rows)} enforced metrics, {counts['REVIEWED']} reviewed, "
        f"{counts['UNGUARDED']} unguarded, {counts['DUE']} due, {counts['DUPLICATE']} duplicate"
    )
    return 1 if (counts["UNGUARDED"] or counts["DUE"] or counts["DUPLICATE"]) else 0


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
