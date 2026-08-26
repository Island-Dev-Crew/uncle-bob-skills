---
name: unsafe-empty-assignment-island
description: A hostile proof fixture that empties PATH without export before an allowlisted command. The binding must be refused rather than dropped from the grammar. Never distributed. Trigger phrases - "empty PATH assignment", "empty assignment poison red test".
---

# Unsafe empty assignment island

An empty value is still an assignment. Replaying `PATH=` would disable command lookup; dropping
it would run the proof under the verifier's ordinary path and manufacture a green result.

- `enforced`: verify-proofs.py refuses the empty unsafe binding and gaps the later proof;
  closed-stream-check.py returns the non-verdict 2 without probing a modified script.
- `advisory`: nothing else here is real.

```bash
PATH=
python3 -c "import sys; sys.exit(0)"   # exit 0
```
