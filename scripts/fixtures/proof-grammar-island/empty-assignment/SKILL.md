---
name: proof-grammar-empty-assignment
description: A proof grammar fixture in which an ordinary block-local variable is deliberately emptied before an allowlisted command. The empty binding must replay. Never distributed. Trigger phrases - "empty proof assignment", "empty local replay test".
---

# Empty ordinary assignment

The first assignment makes a stale value observable. The second must clear it; silently dropping
`D=` leaves `poison` in place and makes the documented proof fail.

- `enforced`: verify-proofs.py replays both assignments and the proof exits 0.
- `advisory`: nothing else here is real.

```bash
D=poison
D=
python3 -c "import sys; sys.exit(0 if sys.argv[1] == '' else 1)" "$D"   # exit 0
```
