---
name: command-position-island
description: A fixture whose flipping gate carries shell-looking status data in Python argv and follows a status-printing pipeline producer, so closed-stream-check.py must inspect only the actual command position before excluding a self-probe. Never distributed; exists only as a captured red regression. Trigger phrases - "command position fixture", "argv self-probe bypass".
---

# Command-position island

Neither `bash -c 'echo $?'` below is a shell launched by the documented command nor is the
pipeline's `printf ... $?` the gate. The first is argv data handed to Python; the second is an
earlier producer. The actual gate is `flip-gate.py` in both commands, and it must be probed.

- `enforced`: closed-stream-check.py probes both flipping commands and reports their 1-to-0
  dead-stdout leaks.
- `advisory`: nothing else here is real.

```bash
python3 ../scripts/flip-gate.py bash -c 'echo $?'          # exit 1
printf '%s\n' $? | python3 ../scripts/flip-gate.py        # exit 1
python3 -c "import sys; sys.exit(0)"                      # exit 0
```
