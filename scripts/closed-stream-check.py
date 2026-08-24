#!/usr/bin/env python3
"""closed-stream-check.py — no gate may answer a dead output stream with a verdict.

Usage: python3 scripts/closed-stream-check.py [island-dir ...]   (default: skills/*/)

Every gate in this pack states a closed set of exit codes, and a caller reads that set to
decide whether the code under test passed. Two shutdown paths break that promise without
touching a single line of gate logic:

  120  CPython replaces the status a script chose when its own shutdown flush hits a dead
       stdout — the ordinary `gate.py … | head` idiom is enough to trigger it.
  141  a shell gate killed by SIGPIPE, which is 128+13 and likewise names no verdict.

Neither is in any island's table, so either one is a code the caller cannot interpret —
and the failure is silent, because the gate did its work and only died on the way out.

WHAT IT DOES. It re-runs the commands the islands already document as proofs — the same
grammar `verify-proofs.py` reads — with stdout connected to a pipe whose reader is already
closed, then with stderr the same way. A gate that survives both with its own documented
code is sealed. This probes the REAL verdict paths rather than `--help`, which is the
distinction that matters: an early usage exit often survives a dead pipe while the path
that actually prints a report does not.

Exit 0 when every probed invocation kept a plausible verdict code, 1 when any leaked, 2 on
usage or IO, and 3 when nothing was probed at all — a harness that ran nothing has proven
nothing, which is the failure this pack names as its worst gate shape.

LIMIT, stated rather than discovered. It can only probe what the islands document. A gate
path with no documented invocation is not covered here, and this file is not evidence about
it. It also inherits `verify-proofs.py`'s trust boundary: it RUNS commands taken from the
repository it is checking, so point it only at a tree you trust.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

LEAKED = {120, 141}


def load_grammar():
    """Reuse the proof grammar rather than re-implementing it.

    A second copy of "what counts as a documented command" would drift from the first, and
    then this harness would quietly probe a different set than the one the pack reports.
    """
    here = Path(__file__).resolve().parent / "verify-proofs.py"
    spec = importlib.util.spec_from_file_location("verify_proofs", here)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def probe(script, cwd, stream):
    """Run one invocation with `stream` (1 or 2) already closed; return its exit code."""
    r, w = os.pipe()
    os.close(r)                                   # the reader is gone before the write
    kw = {"stdout": w, "stderr": subprocess.DEVNULL} if stream == 1 else \
         {"stderr": w, "stdout": subprocess.DEVNULL}
    try:
        return subprocess.run(["bash", "-c", script], cwd=cwd, timeout=60, **kw).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    finally:
        try:
            os.close(w)
        except OSError:
            pass


def main(argv):
    vp = load_grammar()
    args = argv[1:] or sorted(str(p) for p in Path("skills").glob("*/"))
    probed = 0
    leaks = []
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            continue
        for block in vp.blocks(skill.read_text(encoding="utf-8")):
            for cmd, expected, setup, _gapped in vp.commands(block):
                if expected is None or not vp.is_runnable(cmd):
                    continue
                if vp.PLACEHOLDER.search(cmd) or vp.FORBIDDEN.search(cmd):
                    continue
                # A command that already closes a stream on purpose is the island's own
                # probe of this very defect; re-closing it would test the harness, not it.
                if ">&-" in cmd or "$?" in cmd:
                    continue
                script = "; ".join(setup + [cmd]) if setup else cmd
                for stream in (1, 2):
                    probed += 1
                    rc = probe(script, d, stream)
                    if rc in LEAKED:
                        leaks.append((d.name, "stdout" if stream == 1 else "stderr", rc, cmd))
    for name, which, rc, cmd in leaks:
        print(f"LEAK {name}: exit {rc} with {which} closed — no island names that code")
        print(f"      {cmd}")
    print(f"\n{probed} closed-stream probes over {len(args)} island(s), {len(leaks)} leak(s)")
    if leaks:
        return 1
    if probed == 0:
        print("NOTHING PROBED - this is not a pass", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        _code = main(sys.argv)
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:
        print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
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
