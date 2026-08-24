#!/usr/bin/env python3
"""mutating-stub.py — the known-dirty half of readonly-probe.py's pair.

Not part of the audit and never invoked by it. It exists so the probe can be watched
failing: run from a sandbox copy of these fixtures it appends one line to prompt.md,
which is exactly the mutation a REPORT-mode run must never make. A probe that has only
ever been seen green has not been proven able to go red.

Exit code: always 0. The write is the point; the probe, not this file, is what must
turn red on it.
"""
from pathlib import Path

with Path("prompt.md").open("a", encoding="utf-8") as fh:
    fh.write("- injected by the mutating stub\n")
