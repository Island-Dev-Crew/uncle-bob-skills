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

# What a probe is allowed to return when its output stream is dead. Two things are fine, and
# nothing else is.
#
#   - the code the command DOCUMENTS: its verdict survived the closed stream intact.
#   - a NON-VERDICT code: the gate could not emit its report and fail-closed instead. A report
#     nobody received is not a verdict, so declining to claim one is correct.
#
# Everything else is a leak: a shutdown code (CPython's 120, a shell's 141), a signal, a
# TIMEOUT — OR, the dangerous one this check exists for, a DIFFERENT verdict than documented.
# A gate that documents 1 (a breach) and returns 0 (a clean pass) when its pipe dies is a
# breach silently reported as clean, and the previous rule — membership in a pack-wide union
# {0,1,2,3,4} — passed it, because 0 was in the set. The union was also justified as "measured",
# which was false: three islands document 130. This compares against the command's own code.
VERDICT = {0, 1}          # green / red — a real answer about the code under test
NON_VERDICT = {2, 3, 4}   # usage / IO / fail-closed / strict — explicitly "no answer"


def leaked(rc, expected):
    """A probe result is a leak unless the verdict survived or the gate fail-closed."""
    if rc == expected:
        return False
    if rc in NON_VERDICT:
        return False
    return True


def load_grammar():
    """Reuse the proof grammar rather than re-implementing it.

    A second copy of "what counts as a documented command" would drift from the first, and
    then this harness would quietly probe a different set than the one the pack reports.
    """
    here = Path(__file__).resolve().parent / "verify-proofs.py"
    # A checker must not modify the tree it is checking. Importing by path compiles the
    # module and drops `scripts/__pycache__/verify-proofs.*.pyc` into the repo — the same
    # class of defect this pack caught in v1.0, when a syntax check wrote a byte-cache into
    # every island it validated. It is gitignored and would never ship, which is exactly why
    # it would have gone unnoticed.
    sys.dont_write_bytecode = True
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
        rc = subprocess.run(["bash", "-c", script], cwd=cwd, timeout=60, **kw).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    finally:
        try:
            os.close(w)
        except OSError:
            pass
    # A child killed by a signal reaches Python as the NEGATIVE signal number, while a shell
    # reports the same death as 128+n. Comparing the raw value against shell-convention
    # constants meant the SIGPIPE half of this tool could never fire on the common path:
    # `bash -c '<one command>'` exec-optimises, so bash IS the gate, and its SIGPIPE death
    # arrived here as -13 while the table was looking for 141. Fourteen real deaths across ten
    # islands were reported as clean, by the very gate built to catch them.
    return 128 - rc if rc < 0 else rc


def main(argv):
    vp = load_grammar()
    args = argv[1:] or sorted(str(p) for p in Path("skills").glob("*/"))
    probed = 0
    leaks = []
    refused = 0
    examined = 0
    own_probes = 0
    explicit = bool(argv[1:])
    for arg in args:
        d = Path(arg)
        skill = d / "SKILL.md"
        if not skill.is_file():
            # Skipping a path the caller NAMED, and then counting it in the summary, certified a
            # scope this tool never looked at: one real island plus one typo reported "over 2
            # island(s)" and exited 0. A default sweep may pass over a non-island directory; an
            # explicit target that is not one is the caller being wrong.
            if explicit:
                print(f"closed-stream-check: not an island (no SKILL.md): {d}", file=sys.stderr)
                return 2
            continue
        examined += 1
        for block in vp.blocks(skill.read_text(encoding="utf-8")):
            for cmd, expected, setup, _gapped in vp.commands(block):
                if expected is None or not vp.is_runnable(cmd):
                    continue
                if vp.PLACEHOLDER.search(cmd):
                    continue
                # A command that already closes a stream on purpose is the island's own
                # probe of this very defect; re-closing it would test the harness, not it.
                # Counted and printed, not pruned in silence — a quiet prune is the same
                # false green this pack names elsewhere, and 19 candidates land here today.
                if ">&-" in cmd or "$?" in cmd:
                    own_probes += 1
                    continue
                script = "; ".join(setup + [cmd]) if setup else cmd
                # The refusal has to cover the whole script that will actually run. Testing only
                # the annotated command left a forbidden primitive in a replayed SETUP line free
                # to execute — twice, once per stream — while verify-proofs.py, reading the same
                # blocks, refused that very script. Two tools disagreeing about what is too
                # dangerous to run is worse than either answer alone.
                if vp.FORBIDDEN.search(script):
                    refused += 1
                    continue
                for stream in (1, 2):
                    probed += 1
                    rc = probe(script, d, stream)
                    if leaked(rc, expected):
                        leaks.append((d.name, "stdout" if stream == 1 else "stderr",
                                      rc, expected, cmd))
    for name, which, rc, expected, cmd in leaks:
        print(f"LEAK {name}: exit {rc} with {which} closed — documented {expected}, "
              f"and {rc} is neither that verdict nor a fail-closed non-verdict")
        print(f"      {cmd}")
    tail = f", {refused} refused" if refused else ""
    print(f"\n{probed} closed-stream probes over {examined} island(s), {len(leaks)} leak(s){tail}"
          f" ({own_probes} candidate(s) not re-probed: they close a stream themselves)")
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
