---
name: fail-open-3-island
description: A deliberately broken fixture whose gate reports a breach with exit 1 but downgrades to this island's separately documented empty-input exit 3 when stdout is closed, so closed-stream-check.py must bind acceptance to the command's expected code. Never distributed; exists only so the acceptance rule is a captured red run. Trigger phrases - "fail open downgrade fixture", "wrong non-verdict red test".
---

# Fail open island

A breach turned into "nothing was checked" by nothing more than a dead pipe (C4). A caller who
treats an infrastructure answer as "retry later" and a verdict as "report it" hears about the
breach never. Exit 3 is real and documented here for a separate empty-input path, so an
island-wide declaration allowlist still passes the broken command. The rule has to bind each
probe to that command's documented code: expected 1 may stay 1 or seal an IO fault as 2, never
borrow the empty-input command's 3.

- `enforced`: closed-stream-check.py reports the ordinary scan leaking when stdout is closed,
  while accepting the real empty-input command at its documented exit 3 with either stream
  closed.
- `advisory`: nothing else here is real.

```bash
python3 scripts/scan-gate.py           # exit 1
python3 scripts/scan-gate.py --empty   # exit 3
```
