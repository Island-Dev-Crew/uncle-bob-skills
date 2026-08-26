---
name: quoted-status-island
description: A fixture whose flipping gate carries a quoted `$?` and a quoted `>&-` as ARGUMENT DATA, so a substring test excludes it from the closed-stream probe and its 1-to-0 flip goes unseen. Never distributed; exists only so the narrowed self-probe test is a captured red run. Trigger phrases - "quoted status fixture", "self-probe skip red test".
---

# Quoted status island

The harness skips a command that closes a stream itself, because re-closing it would test the
harness rather than the gate. That exclusion was a substring test over the whole line, so two
characters inside a quoted argument bought a gate its way out of the check (C4). Both commands
below carry the characters as DATA and manipulate nothing; the third is an ordinary proof, so
the run has probes and reports success while the flip goes unseen.

The same gate as this island's own, with one argument added. That argument is the whole
difference between a leak that is reported and a leak that is not.

- `enforced`: closed-stream-check.py probes both flipping commands and reports them leaking.
- `advisory`: nothing else here is real.

```bash
python3 ../scripts/flip-gate.py 'exit was $?'       # exit 1
python3 ../scripts/flip-gate.py 'writes >&- here'   # exit 1
python3 -c "import sys; sys.exit(0)"                # exit 0
```
