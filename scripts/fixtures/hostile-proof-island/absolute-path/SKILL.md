---
name: absolute-path-island
description: A deliberately hostile fixture that reaches a network and a device-destructive primitive through a PATH rather than a bare word, so verify-proofs.py must judge basenames and REFUSE both rather than run them. Never distributed; exists only so the path-qualified refusal is a captured run instead of a claim. Trigger phrases - "absolute path refusal fixture", "basename refusal red test".
---

# Absolute path island

The bare-word refusal cannot see `/usr/bin/curl`. The lookbehind that stops `scripts/dd-helper.py`
from reading as `dd` also blinds the pattern to a path-qualified name, so a fork could reach the
same binary by spelling out where it lives (C4). The refusal has to compare the name the kernel
would execute - the basename - not the word as written.

Both paths below are unreachable on purpose, so before the fix they cost 127 rather than a
connection. The defect is that they were EXECUTED at all.

- `enforced`: verify-proofs.py refuses both commands; closed-stream-check.py refuses them too, and
  the two tools agreeing about what is too dangerous to run is the point of sharing one refusal.
- `advisory`: nothing else here is real.

```bash
python3 -c "print('ok')" && /nonexistent/bin/curl https://example.invalid/x   # exit 127
bash -c '/nonexistent/sbin/dd --version'                                     # exit 127
```
