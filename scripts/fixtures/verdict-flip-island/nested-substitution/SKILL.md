---
name: nested-substitution-island
description: A fixture whose flipping gate carries a benign command substitution that closes only the substitution stream or reports only the substitution status, so closed-stream-check.py must still probe the outer gate. Never distributed; exists only as a captured red regression. Trigger phrases - "nested substitution fixture", "outer gate exemption bypass".
---

# Nested-substitution island

The redirection and status report below belong to the command substitution, not to the outer
Python gate. A command substitution gets its own capture pipe; none of the three spellings
closes the outer gate's stream or turns the outer gate into a self-probe. The `bash -c` case is
load-bearing: bash removes the backslash from `\$(` in its double-quoted operand before the
inner shell sees it, while a generic word parser may retain it. The broken outer gate must
remain eligible for dead-stream probing in every form.

The final command keeps the old buggy checker from returning NOTHING PROBED: before this
fixture's guard landed, all three leaking commands were falsely exempted and this safe control
made the run return a genuine false green.

- `enforced`: closed-stream-check.py probes all three outer gate commands and reports their 1-to-0
  dead-stdout leaks; the safe control remains clean.
- `advisory`: nothing else here is real.

```bash
python3 ../scripts/flip-gate.py $(printf x >&-)          # exit 1
python3 ../scripts/flip-gate.py $(echo ok; exit $?)     # exit 1
bash -c "python3 ../scripts/flip-gate.py \$(printf x >&-)" # exit 1
python3 -c "import sys; sys.exit(0)"                    # exit 0
```
