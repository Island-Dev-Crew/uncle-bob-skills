---
name: proof-grammar-continuation
description: A proof grammar fixture for Bash backslash-newline removal. A welded command name must not be reconstructed with an invented space. Never distributed. Trigger phrases - "proof continuation grammar", "welded command proof test".
---

# Backslash-newline removal

The first pipeline spells `echo` across two physical rows and really exits 0. Its deliberately
wrong 127 annotation captures the old false green, which reconstructed `ec ho` and ran that
different command. The second block is the ordinary spaced continuation control.

- `enforced`: `verify-proofs.py` returns 1 with the welded command reported as a mismatch.
- `advisory`: the ordinary spaced continuation still runs and matches 0.

```bash
printf x | ec\
ho PAYLOAD_EXECUTED # exit 127
```

```bash
printf x | \
echo PAYLOAD_EXECUTED # exit 0
```
