#!/usr/bin/env python3
"""readonly-probe.py — prove this island's REPORT toolkit cannot mutate what it reads.

Usage:
  readonly-probe.py           run inventory.py extract + check over a sandbox copy of
                              scripts/fixtures/ and assert the tree came back untouched
  readonly-probe.py --red     run scripts/fixtures/mutating-stub.py under the same
                              harness instead; it appends a line, so the probe must fail

An audit invoked observationally (REPORT) may print anything and must change nothing.
That claim is worth no more than the run behind it, so this probe copies the fixtures
into a temp tree, records (relative path, sha256) for every file, runs the commands
against the copy, records again, and diffs the two manifests. Created, deleted, and
modified paths are all breaches and all named.

Deterministic: same fixtures, same verdict; no model, no network, no shell.

Exit codes:
  0  every probed command ran and the sandbox tree is byte-identical afterwards
  1  the tree changed - each created/deleted/modified path is printed
  2  usage error, IO error, or a probed command that could not be launched at all
     (a probe that ran nothing has proven nothing, so that is never a pass)
"""
import hashlib
import shutil
import subprocess
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
INVENTORY = HERE / "inventory.py"
STUB = FIXTURES / "mutating-stub.py"


def manifest(root: Path):
    """(relative path -> sha256) for every file under root, sorted and deterministic."""
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> int:
    red = "--red" in sys.argv[1:]
    if [a for a in sys.argv[1:] if a != "--red"]:
        print(__doc__)
        return 2
    if not FIXTURES.is_dir() or not INVENTORY.is_file():
        print(f"readonly-probe: missing {FIXTURES} or {INVENTORY}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="steering-audit-probe-") as tmp:
        sandbox = Path(tmp) / "fixtures"
        shutil.copytree(FIXTURES, sandbox)
        if red:
            if not STUB.is_file():
                print(f"readonly-probe: missing red fixture {STUB}", file=sys.stderr)
                return 2
            cmds = [[sys.executable, str(STUB)]]
        else:
            cmds = [
                [sys.executable, str(INVENTORY), "extract", "prompt.md"],
                [sys.executable, str(INVENTORY), "check", "prompt.md", "audit-complete.md"],
            ]
        before = manifest(sandbox)
        if not cmds or not before:
            print("readonly-probe: nothing to probe; this is not a pass", file=sys.stderr)
            return 2
        for cmd in cmds:
            try:
                p = subprocess.run(cmd, cwd=sandbox, capture_output=True, timeout=60)
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"readonly-probe: cannot run {cmd[1:]}: {exc}", file=sys.stderr)
                return 2
            print(f"ran {' '.join(Path(c).name for c in cmd[1:])} -> exit {p.returncode}")
        after = manifest(sandbox)

    breaches = []
    for path in sorted(set(before) | set(after)):
        if path not in after:
            breaches.append(f"DELETED  {path}")
        elif path not in before:
            breaches.append(f"CREATED  {path}")
        elif before[path] != after[path]:
            breaches.append(f"MODIFIED {path}")
    for line in breaches:
        print(line)
    print(f"\n{len(before)} files probed, {len(breaches)} mutation(s)")
    return 1 if breaches else 0


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
