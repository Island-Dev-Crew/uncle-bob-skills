---
name: actual-self-probe-island
description: A fixture containing only a command that deliberately closes its own stdout, so closed-stream-check.py must count it as an own-probe and return NOTHING PROBED rather than re-probing shell redirection syntax. Never distributed; exists as a regression for command-position parsing. Trigger phrases - "actual self probe fixture", "redirection position regression".
---

# Actual self-probe island

This command closes its own stdout in the actual gate position. Re-closing it would test the
harness, so the checker must exclude it explicitly and return 3 because nothing else ran.

- `enforced`: closed-stream-check.py reports one own-probe, zero probes, and exit 3.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)" 1>&-   # exit 0
```
