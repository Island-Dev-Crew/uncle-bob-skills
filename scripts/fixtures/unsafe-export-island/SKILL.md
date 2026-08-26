---
name: unsafe-export-island
description: A deliberately hostile fixture whose proof block exports a poisoned PATH before an allowlisted command, so verify-proofs.py must REFUSE the export rather than replay it into the shell that runs the proof. Never distributed; exists only so the refusal is a captured run. Trigger phrases - "unsafe export fixture", "PATH poison red test".
---

# Unsafe export island

A fork could export a shim ahead of the very tool the block then runs (C4). The replay must refuse.

- `enforced`: verify-proofs.py refuses the unsafe export and does not replay it.
- `advisory`: nothing else here is real.

```bash
export PATH=./fake:$PATH
python3 -c "print('ran')"   # exit 0
```
