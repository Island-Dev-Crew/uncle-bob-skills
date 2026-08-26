---
name: proof-grammar-malformed-command
description: A proof grammar fixture in which malformed off-allowlist shell rows sit between allowlisted commands and exit reports. Invalid syntax must still terminate report search. Never distributed. Trigger phrases - "malformed proof command", "unterminated report boundary test".
---

# Malformed command boundaries

Each report follows a different malformed off-allowlist row. It belongs to that row's shell
syntax failure, never to the Python command above it.

- `enforced`: `verify-proofs.py --strict` returns 4 with all three Python candidates pending.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(2)"
seat3-offlist 'unterminated
echo $? # -> 2
```

```bash
python3 -c "import sys; sys.exit(2)"
seat3-offlist "unterminated
echo $? # -> 2
```

```bash
python3 -c "import sys; sys.exit(2)"
seat3-offlist \
echo $? # -> 2
```
