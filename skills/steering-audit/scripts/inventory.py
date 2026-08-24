#!/usr/bin/env python3
"""inventory.py — deterministic rule inventory for a standing-prompt audit.

Usage:
  inventory.py extract <prompt.md>
      Emit one candidate rule per line: R<n> TAB <lineno> TAB <text>.
      Candidates are markdown list items (-, *, +, 1., 1)) outside code fences.
  inventory.py check <prompt.md> <audit.md>
      Exit 0 iff every R<n> that extract emits appears in <audit.md> on a line
      that also carries a destination word ('generative' or 'gate').
      Exit 1 otherwise, listing every unaccounted rule id.

Deterministic: same input, same output; no model, no network.
"""
import re
import os
import sys
from pathlib import Path

LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)")
FENCE = re.compile(r"^\s*(```|~~~)")
DEST = re.compile(r"\b(generative|gate)\b", re.IGNORECASE)


def extract(path: Path):
    rules, in_fence, n = [], False, 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = LIST_ITEM.match(line)
        if m:
            n += 1
            rules.append((f"R{n}", lineno, m.group(1)))
    return rules


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    mode, prompt = sys.argv[1], Path(sys.argv[2])
    if not prompt.is_file():
        print(f"no such file: {prompt}", file=sys.stderr)
        return 2
    rules = extract(prompt)
    if mode == "extract":
        for rid, lineno, text in rules:
            print(f"{rid}\t{lineno}\t{text}")
        print(f"# {len(rules)} candidate rules", file=sys.stderr)
        return 0
    if mode == "check":
        if len(sys.argv) < 4:
            print(__doc__)
            return 2
        audit = Path(sys.argv[3])
        if not audit.is_file():
            print(f"no such file: {audit}", file=sys.stderr)
            return 2
        lines = audit.read_text(encoding="utf-8").splitlines()
        missing = [
            (rid, lineno, text)
            for rid, lineno, text in rules
            if not any(re.search(rf"\b{rid}\b", ln) and DEST.search(ln) for ln in lines)
        ]
        if missing:
            for rid, lineno, text in missing:
                print(f"UNACCOUNTED {rid} (prompt line {lineno}): {text[:80]}")
            print(f"{len(missing)}/{len(rules)} rules lack a destination", file=sys.stderr)
            return 1
        print(f"all {len(rules)} candidate rules carry a destination")
        return 0
    print(__doc__)
    return 2


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
