---
name: pending-only-island
description: A fixture whose whole proof block is candidates with no documented exit code, so nothing runs and PENDING is the only class present - the case where `--strict` and the nothing-ran path both apply at once. Never distributed; exists so the precedence between them is a captured run rather than a claim. Trigger phrases - "pending only fixture", "strict precedence red test".
---

# Pending only island

Two runnable candidates, neither carrying a code. Both classes are true at once here: nothing was
executed, and a caller who asked for full coverage has candidates that document nothing (C4).
`--strict` is the caller saying which of the two they came to hear, so it outranks the other.

- `enforced`: verify-proofs.py exits 3 here, and `--strict` exits 4.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)"
python3 -c "import sys; sys.exit(1)"
```
