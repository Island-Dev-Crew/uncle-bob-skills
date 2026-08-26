---
name: quoted-self-probe-island
description: A fixture whose flipping gate carries `$?` inside DOUBLE quotes, where a shell expands it, so a self-probe test built on expansion drops the command from the closed-stream probe and its 1-to-0 flip goes unseen. Never distributed; exists only so the position-based self-probe test is a captured red run. Trigger phrases - "double quoted status fixture", "self-probe expansion red test".
---

# Quoted self-probe island

A proof block hostile to the HARNESS rather than to the machine it runs on. closed-stream-check.py
skips a command that closes a stream or reads its status itself, because re-closing it would test
the harness rather than the gate. Reading `$?` wherever a shell would EXPAND it left that exemption
one keystroke wide (C4): the single-quoted spelling was closed off, and its double-quoted twin
expands, so the same gate walked straight back out of the probe set.

The gate below is [`verdict-flip-island`](../../verdict-flip-island/SKILL.md)'s - it answers 1 when
watched and 0 when its stdout is dead. The second command is an ordinary proof, so the run has
probes and reports success while the flip goes unseen. Expansion was never the property that
mattered; POSITION is. `rc=$?` and `echo $?` are a command acting on its own status. An argument is
an argument however it is quoted.

- `enforced`: closed-stream-check.py probes the flipping command and reports it leaking.
- `advisory`: nothing else here is real.

```bash
python3 ../../verdict-flip-island/scripts/flip-gate.py "exit was $?"   # exit 1
python3 -c "import sys; sys.exit(0)"                                   # exit 0
```
