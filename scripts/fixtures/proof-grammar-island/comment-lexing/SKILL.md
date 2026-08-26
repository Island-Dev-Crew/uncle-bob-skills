---
name: proof-grammar-comment-lexing
description: A proof grammar fixture whose data contains hashes protected by ANSI-C quoting and an escaped space. The verifier must not truncate either command into a false match. Never distributed. Trigger phrases - "proof comment lexer", "escaped hash proof test".
---

# Shell comment boundaries

Both commands really exit 7. The deliberately wrong annotations capture the old false green:
the verifier truncated each row at a data hash, executed a different prefix, and matched 2 or 0.

- `enforced`: `verify-proofs.py` returns 1, never 0; both complete commands are mismatches, not
  verified proofs of the truncated fragments.
- `advisory`: nothing else here is real.

```bash
printf '%s\n' $'\' #' | python3 -c 'import sys; sys.exit(7)' # exit 2
printf '%s\n' foo\ #bar | python3 -c 'import sys; sys.exit(7)' # exit 0
```
