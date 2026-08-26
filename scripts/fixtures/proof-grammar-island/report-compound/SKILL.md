---
name: proof-grammar-report-compound
description: A proof grammar fixture in which report-shaped prefixes carry pipes, commands, or extra operands. Only a complete pure report may annotate the candidate above it. Never distributed. Trigger phrases - "compound exit report", "report prefix borrowing test".
---

# Pure reports only

Each second row starts like an exit report but is a separate compound command. Its arrow belongs
to that row. None may donate the code to the Python candidate above it.

- `enforced`: `verify-proofs.py --strict` returns 4 with four Python candidates pending and four
  compound commands skipped.
- `advisory`: nothing else here is real.

```bash
python3 -c "import sys; sys.exit(0)"
echo $? | python3 -c "import sys; sys.exit(7)" # -> 0
```

```bash
python3 -c "import sys; sys.exit(0)"
echo $?; python3 -c "import sys; sys.exit(7)" # -> 0
```

```bash
python3 -c "import sys; sys.exit(0)"
rc=$?; echo "EXIT=$rc"; python3 -c "import sys; sys.exit(7)" # -> 0
```

```bash
python3 -c "import sys; sys.exit(0)"
echo $? unexpected-operand # -> 0
```
