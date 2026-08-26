---
name: proof-grammar-unrecognized-command
description: A proof grammar fixture in which an off-allowlist command sits between an allowlisted command and an exit report. The earlier candidate must not borrow the later command's status. Never distributed. Trigger phrases - "unrecognized proof command", "borrowed exit report red test".
---

# Unrecognized command boundary

The report belongs to `ruby`, not to the Python candidate above it. The verifier must leave
Python `PENDING` and print Ruby as `SKIPPED`; a green run would certify the wrong execution.

- `enforced`: `verify-proofs.py --strict` returns 4 with one pending and one skipped command.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)"
ruby second.rb
echo $? # -> 0
```
