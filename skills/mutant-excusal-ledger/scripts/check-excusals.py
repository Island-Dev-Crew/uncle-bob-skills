#!/usr/bin/env python3
"""check-excusals.py — deterministic gate for the mutant excusal ledger.

Usage: python3 check-excusals.py <survivors-file> <ledger-file>

survivors-file  one surviving-mutant id per line (blank lines and '#' comments
                ignored) — the survivor list a mutant-hunt run emits after
                kill-tasks are exhausted. The id is the first token per line.
ledger-file     excusal entries. An entry starts at column 0 with the mutant id
                (first whitespace-separated token) followed by indented
                'field: value' lines; an indented line with no field name
                continues the previous field. Required fields: mutation,
                argument, excused-by, head. The argument must be at least 40
                characters — a substance proxy, not a truth check.

Exit 0 iff every survivor has a complete excusal. Exit 1 otherwise, listing
every unexcused or malformed id. Stale excusals (an id absent from the survivor
list) warn without failing. Same inputs always produce the same verdict.
"""
import re
import os
import sys
from pathlib import Path

REQUIRED = ("mutation", "argument", "excused-by", "head")
MIN_ARGUMENT_CHARS = 40
FIELD = re.compile(r"^\s+([A-Za-z][\w-]*):\s*(.*)$")


def read_survivors(path: Path) -> list[str]:
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            ids.append(s.split()[0])
    return ids


def read_ledger(path: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    current = last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = line.split()[0]
            entries.setdefault(current, {})
            last = None
            continue
        if current is None:
            continue
        m = FIELD.match(line)
        if m:
            last = m.group(1).lower()
            entries[current][last] = m.group(2).strip()
        elif last:
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
    ledger = read_ledger(ledger_path)

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
