---
name: escaped-name-island
description: A deliberately hostile fixture that reaches network and device-destructive primitives through ordinary shell quoting and escaping - `cur\l`, `'cur'l`, `CURL` - so verify-proofs.py must parse the line into words the way bash does and REFUSE all of them rather than run them. Never distributed; exists only so the word-parse refusal is a captured run instead of a claim. Trigger phrases - "escaped name refusal fixture", "quoted primitive red test".
---

# Escaped name island

Comparing basenames closed the path-qualified spelling. It did not close the class, because both
refusal patterns read the line as TEXT and the shell does not (C4). `cur\l`, `'cur'l`, `"cur"l` and
`c''url` are four spellings of one word; bash resolves every one to `curl` and executes the same
binary. `CURL` is a fifth on any case-insensitive volume, which is every default macOS install.

Each spelling below was measured against bash itself rather than reasoned about: `printf '%s\n'`
over the same word prints what the kernel would be handed. Before the fix these ran, and the
harness that shares this refusal then ran them twice more each.

The paths are unreachable on purpose, so a regression costs 127 rather than a connection. The
defect is that they were EXECUTED at all. That is not a theoretical distinction: the same block
written without the `/nonexistent/` prefix, in a scratch island during the repair, reached the real
`curl` and came back with its own exit 6 - a DNS failure, raised from inside a proof verifier.

- `enforced`: verify-proofs.py refuses all four commands and exits 1. closed-stream-check.py
  refuses the same four - both tools take the test from one function and cannot disagree about it -
  and so has nothing left to probe, which it answers with exit 3 rather than a pass.
- `advisory`: nothing else here is real.

```bash
python3 -c "print('ok')" && /nonexistent/bin/cur\l https://example.invalid/x    # exit 127
python3 -c "print('ok')" && /nonexistent/bin/'cur'l https://example.invalid/x   # exit 127
python3 -c "print('ok')" && /nonexistent/bin/CURL https://example.invalid/x     # exit 127
bash -c '/nonexistent/sbin/d\d --version'                                       # exit 127
```
