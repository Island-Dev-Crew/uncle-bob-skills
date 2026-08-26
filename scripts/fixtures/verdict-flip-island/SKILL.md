---
name: verdict-flip-island
description: A deliberately broken fixture whose gate reports a breach with exit 1 but flips to a false clean exit 0 when its stdout is closed, so closed-stream-check.py must flag it as a LEAK. Never distributed; exists only so the check's verdict-comparison is a captured red run. Trigger phrases - "verdict flip fixture", "closed-stream red test".
---

# Verdict flip island

A gate that answers 1 when watched and 0 when not (C4). closed-stream-check.py must catch it.

- `enforced`: closed-stream-check.py reports this gate leaking when its stdout is closed.
- `advisory`: nothing else here is real.

```bash
python3 scripts/flip-gate.py             # exit 1
python3 check-nested-substitution.py     # exit 0
```

Two neighbours carry the shapes this one does not. [`fail-open-3/`](fail-open-3/SKILL.md) hides the
breach in exit 3 borrowed from a separate, honestly documented empty-input command, and
[`quoted-status/`](quoted-status/SKILL.md) hides this very gate from the probe behind a quoted
argument. [`nested-substitution/`](nested-substitution/SKILL.md) proves that a redirection or status
report inside a command substitution cannot exempt the outer gate; its regression runner requires
all three bypass spellings — including an escaped substitution passed through `bash -c` — to be
probed and named as leaks.
