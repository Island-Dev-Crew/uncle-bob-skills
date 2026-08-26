---
name: unsafe-bare-assignment-island
description: A hostile proof fixture that assigns PATH without export before an allowlisted command. The assignment must be refused before its shim can forge the documented verdict. Never distributed. Trigger phrases - "bare PATH assignment", "assignment poison red test".
---

# Unsafe bare assignment island

`PATH` is already exported by the parent process. Assigning it without the `export` keyword
still changes Bash command resolution and the environment inherited by the command below.

- `enforced`: verify-proofs.py refuses the assignment and never runs the shim.
- `advisory`: nothing else here is real.

```bash
PATH=./fake:$PATH
python3 -c "import sys; sys.exit(1)"   # exit 0
```
