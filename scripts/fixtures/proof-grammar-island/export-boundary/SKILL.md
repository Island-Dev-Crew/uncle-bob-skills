---
name: proof-grammar-export-boundary
description: A proof grammar fixture in which a safe export sits between an allowlisted command and an exit report. The export owns that status while remaining setup for later proofs. Never distributed. Trigger phrases - "export report boundary", "safe export continuation test".
---

# Export report boundary

`export` is status-producing shell syntax. The first report belongs to it, not to Python. The
second block proves an accepted export still replays as setup when a later proof is inline.

- `enforced`: strict mode returns 4 for the pending first Python candidate; the continuation control runs and matches 0.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)"
export LANG=C
echo $? # -> 0
```

```bash
export LANG=C
python3 -c "import os,sys; sys.exit(0 if os.environ.get('LANG') == 'C' else 1)"   # exit 0
```
