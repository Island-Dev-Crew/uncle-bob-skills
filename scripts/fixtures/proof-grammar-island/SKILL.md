---
name: proof-grammar-island
description: A fixture whose proof block carries every shape of the proof grammar at once - a bare island-relative script, a distant exit-report line, an off-allowlist command, a usage template, and a candidate with no exit code. Never distributed; exists so the extractor's classification is a captured run rather than a claim. Trigger phrases - "proof grammar fixture", "pending red test".
---

# Proof grammar island

One block, five classifications. The first four shapes were each silently dropped or
silently misread before the grammar was written down (C4).

- `enforced`: verify-proofs.py runs the two proofs, and `--strict` goes red on the PENDING.
- `advisory`: nothing else here is real.

```bash
scripts/probe.sh dirty   # exit 1
$ scripts/probe.sh clean
PASS  nothing dirty
$ echo $?   # → 0
python3 -c "import sys; sys.exit(0)"
scripts/probe.sh <mode>
true   # exit 0
```

The five, in order: a bare island-relative script with an inline code; the same script
whose code sits on a report line two lines below its output; a candidate carrying no code
at all (PENDING); a usage template with a `<placeholder>` (TEMPLATE); an off-allowlist
leading token that still states a code (SKIPPED).

Two proofs run here, so the PENDING is not the only thing `--strict` has to weigh.
[`pending-only/`](pending-only/SKILL.md) is the island where it is, and where the two answers
compete.
