---
name: proof-grammar-bash-builtin
description: A proof grammar fixture in which an off-allowlist Bash builtin sits between an allowlisted command and an exit report. The earlier candidate must not borrow the builtin's status. Never distributed. Trigger phrases - "Bash builtin proof boundary", "builtin borrowed report test".
---

# Bash builtin command boundary

The report belongs to Bash's `help` builtin, not to the Python candidate above it. Every Bash
builtin and keyword is a command boundary even when it is outside the verifier's run allowlist.

- `enforced`: `verify-proofs.py --strict` returns 4 with Python pending and `help` skipped.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)"
help printf
echo $? # -> 0
```
