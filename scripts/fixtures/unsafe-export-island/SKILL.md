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

[`bare-assignment/`](bare-assignment/SKILL.md) is the sibling spelling that omits
`export`. Because the parent already exports `PATH`, Bash preserves that attribute; the shim
would still replace `python3`. The verifier must refuse both spellings.

[`empty-assignment/`](empty-assignment/SKILL.md) removes the value as well as the keyword.
`PATH=` is still an unsafe binding: dropping it silently runs the later proof under a different
path, while replaying it disables lookup. It is refused and the later proof is gapped.

[`refusal-with-eligible/`](refusal-with-eligible/SKILL.md) proves an independent eligible probe
cannot launder that refusal into a green closed-stream harness result.
