---
name: proof-grammar-host-independent-command
description: A proof grammar fixture in which a syntactically command-shaped but nonexistent tool sits between an allowlisted command and an exit report. Classification must not depend on the review host PATH. Never distributed. Trigger phrases - "host-independent proof boundary", "absent command borrowed report test".
---

# Host-independent command boundary

The report belongs to the off-allowlist command, not to Python. Whether that executable happens
to exist on the verifier host cannot change which line owns the report.

- `enforced`: `verify-proofs.py --strict` returns 4 with Python pending and the unknown command skipped.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(127)"
seat3-offlist-no-script-operand --mode
echo $? # -> 127
```
