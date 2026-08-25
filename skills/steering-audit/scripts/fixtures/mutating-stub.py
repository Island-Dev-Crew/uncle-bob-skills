#!/usr/bin/env python3
"""mutating-stub.py — the known-dirty half of readonly-probe.py's pair.

Not part of the audit and never invoked by it. It exists so the probe can be watched
failing: run from a sandbox copy of these fixtures it makes exactly one mutation, named
by its single argument, and every one of them is something a REPORT-mode run must never
do. A probe that has only ever been seen green has not been proven able to go red.

  append   (the default) adds a line to prompt.md
  mkdir    creates an empty directory
  chmod    tightens prompt.md's permission bits
  symlink  creates a dangling symlink

Only `append` changes any file's bytes. The other three are here because a manifest
that hashes regular-file contents and nothing else stays green straight through them.

Exit code: 0 once the mutation is made, 2 on an unknown kind. The write is the point;
the probe, not this file, is what must turn red on it.
"""
import sys
from pathlib import Path

kind = sys.argv[1] if len(sys.argv) > 1 else "append"

if kind == "append":
    with Path("prompt.md").open("a", encoding="utf-8") as fh:
        fh.write("- injected by the mutating stub\n")
elif kind == "mkdir":
    Path("injected-dir").mkdir()
elif kind == "chmod":
    Path("prompt.md").chmod(0o600)
elif kind == "symlink":
    Path("injected-link").symlink_to("nowhere.md")
else:
    print(f"mutating-stub: unknown mutation {kind!r}", file=sys.stderr)
    raise SystemExit(2)
