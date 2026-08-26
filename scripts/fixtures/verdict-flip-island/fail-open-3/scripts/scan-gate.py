#!/usr/bin/env python3
"""scan-gate.py — a gate that downgrades its breach to "nothing was checked".

Deliberately broken, for one purpose: to be the red test for the closed-stream harness's
acceptance rule. With a live stdout it reports a breach and exits 1, the verdict its island
documents. With a dead stdout it scanned exactly the same thing and exits 3 instead. This
island also uses 3 honestly for a separate empty-input path, so accepting any code the island
declares would launder the ordinary breach. The command's own documented result is the boundary.

That is the laundering shape, and it is not the 1-to-0 flip its sibling fixture carries: a
caller who retries on an infrastructure answer and reports only a verdict retries forever and
hears about the breach never. The old rule waved it through because another command in this
island declares 3; the rule that catches it binds the probe to this command's documented 1.
"""
import os
import sys

if sys.argv[1:] == ["--empty"]:
    # Real no-work control: no output is attempted, so closing either stream must leave this
    # command's documented 3 intact.
    sys.exit(3)

try:
    print("BREACH: this gate found a problem")
    sys.stdout.flush()
    sys.exit(1)
except BrokenPipeError:
    # Silence the dead fd so the shutdown flush cannot raise, then answer 3 instead of the 1
    # that was true.
    try:
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
    except OSError:
        pass
    sys.exit(3)
