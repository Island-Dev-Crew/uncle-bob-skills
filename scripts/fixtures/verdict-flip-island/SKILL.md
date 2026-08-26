---
name: verdict-flip-island
description: A deliberately broken fixture whose gate reports a breach with exit 1 but flips to a false clean exit 0 when its stdout is closed, so closed-stream-check.py must flag it as a LEAK. Never distributed; exists only so the check's verdict-comparison is a captured red run. Trigger phrases - "verdict flip fixture", "closed-stream red test".
---

# Verdict flip island

A gate that answers 1 when watched and 0 when not (C4). closed-stream-check.py must catch it.

- `enforced`: closed-stream-check.py reports this gate leaking when its stdout is closed.
- `advisory`: nothing else here is real.

```bash
python3 scripts/flip-gate.py   # exit 1
```
