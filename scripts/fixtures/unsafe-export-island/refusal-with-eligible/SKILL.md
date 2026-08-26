---
name: unsafe-refusal-with-eligible-island
description: A closed-stream harness fixture combining a refused PATH block with an independent eligible proof. The eligible probe must not launder the refusal into green. Never distributed. Trigger phrases - "mixed refusal proof", "closed stream refusal laundering test".
---

# Refusal cannot be averaged away

The first block is non-verifiable and must never run. The second is independently eligible and
may be probed, but its success cannot turn the island green after a proof step was refused.

- `enforced`: closed-stream-check.py returns the non-verdict 2, with one refusal, one
  refusal-gapped candidate excluded, and two probes from the independent control.
- `advisory`: nothing else here is real.

```bash
PATH=
python3 -c "import sys; sys.exit(0)"   # exit 0
```

```bash
python3 -c "import sys; sys.exit(0)"   # exit 0
```
