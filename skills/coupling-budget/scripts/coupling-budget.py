#!/usr/bin/env python3
"""coupling-budget.py - gate the cross-module coupling one change adds.

Usage:
    python3 coupling-budget.py CHANGE.json [--budget N] [--min-reason N]

Reads one JSON change spec - declared modules, the baseline cross-module edge set,
the current one, and a justification per added edge - and judges the DELTA:

    added   = current_cross - baseline_cross
    removed = baseline_cross - current_cross   (reported as credit, never spent)

Verdicts:
    OVER-BUDGET   count(added) is greater than the declared budget
    UNJUSTIFIED   an added edge with no justification entry
    THIN-REASON   a justification whose reason carries fewer VISIBLE characters
                  than --min-reason. Visible means: NFC-normalised, then drop
                  every codepoint whose Unicode category is control/format (C),
                  combining mark (M) or separator (Z), and drop the named blank
                  glyphs listed in BLANKS. Twenty zero-width joiners cannot buy
                  a green, and neither can twenty Braille blanks.

Exit codes:
    0  no violations. (-h/--help also exits 0, printing usage without judging.)
    1  one or more violations
    2  usage error, unreadable or non-UTF-8 file, malformed spec, internal failure
"""
import argparse
import json
import os
import sys
import unicodedata

TOP_KEYS = {"note", "budget", "modules", "baseline", "current", "justifications"}
JUST_KEYS = {"edge", "reason"}

# Blank glyphs that draw nothing but sit OUTSIDE categories C, M and Z, so the category
# filter alone would count each of them as one visible character: the Hangul fillers
# (Lo), the Braille blank (So), the Khmer inherent vowels and the Mongolian vowel
# separator. Named one at a time because no Unicode category collects them.
BLANKS = frozenset("\u115f\u1160\u3164\uffa0\u2800\u17b4\u17b5\u180e")


class SpecError(Exception):
    """A malformed spec or an unusable input - never a verdict."""


def key(value, where):
    """The one key function: Unicode NFC, then strip. Case is NOT folded."""
    if not isinstance(value, str):
        raise SpecError(f"{where}: expected a string, got {type(value).__name__}")
    name = unicodedata.normalize("NFC", value).strip()
    if not name:
        raise SpecError(f"{where}: module name is empty")
    return name


def collapse(text):
    """The display form of a reason: NFC, whitespace runs to single spaces, ends stripped."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def visible_len(text):
    """The one reason basis: NFC, then count the codepoints left after two subtractions.

    First the three Unicode category groups that occupy no width of their own come out
    - C (control and format, where a zero-width joiner lives), M (combining marks) and
    Z (spaces and separators). Then the BLANKS set comes out, because a few blank
    glyphs sit outside all three: U+2800 BRAILLE PATTERN BLANK is category So and
    U+3164 HANGUL FILLER is Lo, and raw codepoint counting once let either of them buy
    a green. BLANKS is a named list, not a rendering test - a codepoint that draws
    nothing and is not on the list still counts 1. The printed count and the
    THIN-REASON message both use this number, so the verdict and the figure it prints
    share one basis.
    """
    return sum(
        1
        for char in unicodedata.normalize("NFC", text)
        if unicodedata.category(char)[0] not in "CMZ" and char not in BLANKS
    )


def reject_constant(token):
    raise SpecError(f"non-finite JSON constant {token!r} is not allowed")


def load(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise SpecError(f"cannot read {path}: {exc}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SpecError(f"{path} is not valid UTF-8: {exc}")
    try:
        data = json.loads(text, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise SpecError(f"{path} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise SpecError(f"{path}: top level must be a JSON object")
    unknown = sorted(set(data) - TOP_KEYS)
    if unknown:
        raise SpecError(f"{path}: unknown top-level key(s): {', '.join(unknown)}")
    return data


def modules_of(data):
    raw = data.get("modules")
    if not isinstance(raw, list) or not raw:
        raise SpecError("'modules' must be a non-empty list of module names")
    declared = set()
    folded = {}
    for index, item in enumerate(raw):
        name = key(item, f"modules[{index}]")
        if name in declared:
            raise SpecError(f"'modules' declares {name!r} twice")
        clash = folded.get(name.casefold())
        if clash is not None:
            raise SpecError(
                f"'modules' declares both {clash!r} and {name!r}, which differ only by "
                "case - refused rather than silently joined"
            )
        declared.add(name)
        folded[name.casefold()] = name
    return declared


def edge_of(item, modules, where):
    if not isinstance(item, list) or len(item) != 2:
        raise SpecError(f"{where}: an edge must be a 2-element array [from, to]")
    src = key(item[0], f"{where}[0]")
    dst = key(item[1], f"{where}[1]")
    for name in (src, dst):
        if name not in modules:
            raise SpecError(f"{where}: {name!r} is not declared in 'modules'")
    return (src, dst)


def edge_set(data, field, modules):
    raw = data.get(field)
    if not isinstance(raw, list):
        raise SpecError(f"'{field}' must be a list of [from, to] edges")
    cross, intra = set(), 0
    for index, item in enumerate(raw):
        src, dst = edge_of(item, modules, f"{field}[{index}]")
        if src == dst:
            intra += 1
        else:
            cross.add((src, dst))
    if field == "current" and not cross:
        # The empty gate is the CROSS set, not the raw array. A roll-up bug that maps
        # every path to one module turns real cross-module imports into self-edges, so a
        # failed extraction arrives non-empty far more often than it arrives as [].
        what = (
            "'current' is empty"
            if not raw
            else f"'current' contains no cross-module edges ({intra} intra-module edge(s) only)"
        )
        raise SpecError(
            f"{what} - a coupling-free extraction is a failed extraction far more often "
            "than a coupling-free repo, and an empty gate must not pass"
        )
    return cross, intra


def justifications_of(data, modules):
    raw = data.get("justifications", [])
    if not isinstance(raw, list):
        raise SpecError("'justifications' must be a list of {edge, reason} objects")
    out = {}
    for index, item in enumerate(raw):
        where = f"justifications[{index}]"
        if not isinstance(item, dict):
            raise SpecError(f"{where}: must be an object with 'edge' and 'reason'")
        present = set(item)
        if present != JUST_KEYS:
            listed = ", ".join(sorted(present)) or "(none)"
            raise SpecError(f"{where}: keys must be exactly 'edge' and 'reason', got: {listed}")
        edge = edge_of(item["edge"], modules, f"{where}.edge")
        reason = item["reason"]
        if not isinstance(reason, str):
            raise SpecError(f"{where}.reason: must be a string")
        if edge in out:
            raise SpecError(f"{where}: duplicate justification for {edge[0]} to {edge[1]}")
        out[edge] = collapse(reason)
    return out


def budget_of(data, override):
    if override is not None:
        return override, "--budget"
    if "budget" not in data:
        raise SpecError("'budget' is missing - the budget must be declared; there is no default")
    value = data["budget"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SpecError(f"'budget' must be a non-negative integer, got {value!r}")
    return value, "spec"


def main():
    parser = argparse.ArgumentParser(
        prog="coupling-budget.py",
        description="Gate the cross-module coupling one change adds.",
    )
    parser.add_argument("change", help="path to the JSON change spec")
    parser.add_argument("--budget", type=int, default=None,
                        help="the budget the run is judged against; always wins over the "
                             "spec's declared value, so pin it here in CI")
    parser.add_argument("--min-reason", type=int, default=20,
                        help="minimum visible characters in a justification reason (default 20)")
    args = parser.parse_args()

    try:
        if args.min_reason < 0:
            raise SpecError("--min-reason must be 0 or greater")
        if args.budget is not None and args.budget < 0:
            raise SpecError("--budget must be 0 or greater")
        data = load(args.change)
        modules = modules_of(data)
        budget, source = budget_of(data, args.budget)
        baseline, base_intra = edge_set(data, "baseline", modules)
        current, intra = edge_set(data, "current", modules)
        justified = justifications_of(data, modules)
    except SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    added = sorted(current - baseline)
    removed = sorted(baseline - current)
    violations = []
    if len(added) > budget:
        violations.append(f"OVER-BUDGET added {len(added)}, budget {budget}")

    print(f"budget {budget} (from {source}), min-reason {args.min_reason}")
    note = (
        f", {base_intra} baseline / {intra} current intra-module edge(s) excluded"
        if (base_intra or intra)
        else ""
    )
    print(f"cross-module edges: baseline {len(baseline)}, current {len(current)}{note}")
    print(f"added {len(added)}, budget {budget}, removed {len(removed)}")

    for edge in added:
        label = f"{edge[0]} to {edge[1]}"
        reason = justified.get(edge)
        if reason is None:
            print(f"  ADDED {label} [no justification]")
            violations.append(f"UNJUSTIFIED {label} (no justification entry)")
            continue
        seen = visible_len(reason)
        if seen < args.min_reason:
            print(f"  ADDED {label} [reason {seen} visible chars]")
            violations.append(
                f"THIN-REASON {label} (reason {seen} visible chars, minimum {args.min_reason})"
            )
        else:
            shown = reason if len(reason) <= 60 else reason[:57] + "..."
            print(f"  ADDED {label} justified ({seen} visible chars): {shown}")

    for edge in removed:
        print(f"  REMOVED {edge[0]} to {edge[1]} [credit reported, never spent]")

    if added:
        spend = {}
        for src, _dst in added:
            spend[src] = spend.get(src, 0) + 1
        print("spend by module: " + ", ".join(f"{m} +{n}" for m, n in sorted(spend.items())))

    for edge in sorted(set(justified) - set(added)):
        print(f"  note: STALE justification for {edge[0]} to {edge[1]} (not an added edge, not a violation)")

    for line in violations:
        print(f"VIOLATION {line}")
    print(f"{len(violations)} violation(s)")
    return 1 if violations else 0


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
