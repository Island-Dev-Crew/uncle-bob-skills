---
name: nonstring-metadata
description:
  text: This description is a YAML mapping, not a string. Its repr is long enough that a validator measuring len(str(desc)) reads it as a well-sized description and passes.
---

# Non-string metadata

One concern (C8): every metadata field here parses, is non-empty, and is the wrong
shape. `name` is the only string in the file, so F4 stays green and the three checks
that flip — F3, F6, F7 — are exactly the ones this fixture exists to prove.

It sits under `bad-island/` rather than beside it because `bad-island` is cited by
line and count elsewhere in the pack (6 of 12 red, F4-F9); a nested directory is
ignored by `validate()`, so that verdict is untouched. Point the validator at this
path directly.

- `enforced`: `python3 scripts/validate-island.py scripts/fixtures/bad-island/nonstring-metadata`
  must exit 1 with F3, F6 and F7 red.
- `advisory`: nothing here. This island is never distributed and describes no practice.
