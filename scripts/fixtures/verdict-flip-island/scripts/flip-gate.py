#!/usr/bin/env python3
"""flip-gate.py — a gate that hides its breach when nobody is reading.

Deliberately broken, for one purpose: to be the red test for closed-stream-check.py. With a
live stdout it reports a breach (exit 1). With a dead stdout it swallows the breach into a
CLEAN exit 0 — and neutralises its own output first, so it returns a genuine 0 rather than
leaking CPython's shutdown 120. That is the dangerous flip: a documented 1 becoming a 0 that
looks like every other clean pass. closed-stream-check's old membership rule ({0,1,2,3,4})
waved it through because 0 was in the set; the verdict-comparison rule catches it because 0 is
not the 1 this gate documents.
"""
import os
import sys

try:
    print("BREACH: this gate found a problem")
    sys.stdout.flush()
    sys.exit(1)
except BrokenPipeError:
    # Hide the evidence: redirect the dead fd to /dev/null so the shutdown flush cannot raise,
    # and return a verdict-shaped 0 instead of the 1 that was true.
    try:
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
    except OSError:
        pass
    sys.exit(0)
