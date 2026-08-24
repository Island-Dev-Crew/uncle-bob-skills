---
name: known-dirty-fixture
description: Acceptance ritual for any gate, checker, linter rule, or validator before it may guard anything - a gate earns authority only by first failing RED on a known-bad fixture, then passing GREEN on a known-good one, both kept in the repo beside it. Use when generating or adopting a checker, wiring a new CI gate, or when someone says 'add a validator', 'prove the gate works', or 'the gate passed so we are fine'. Differentiator - this island owns gate acceptance only; what each gate checks is that gate island's own concern, and empirical skill improvement is skill-tune's seat.
---

# Known-Dirty Fixture: no gate is trusted until it has failed

The repo law demands evidence from a check that could have failed ([`CONTEXT.md`](../../CONTEXT.md)). This island turns that law on the checkers themselves. A gate is a loop the agent cannot exit until the tool consents: *"you must change the code until this tool says that it's okay"* (C4). The loop is only real if the tool can say no. A gate that has never gone red is an unfalsified claim wearing a uniform. It may be a checker. It may equally be `exit 0` with a logo.

The pressure is sharpest on *generated* gates. The pack's whole method is *"point your agents at them… and then build one for you"* (C23). But the moment an agent builds you a checker, that checker is unverified code like everything else the agent writes. It earns guard duty the same way any claim earns authority: by surviving a check that could have failed.

## The ritual

1. **Build the dirty fixture alongside the gate.** Write a minimal artifact that embodies exactly the violation class the gate exists to catch: the wrong name, the missing field, the smell, the forbidden dependency. Write it from the *rule*, before or while the gate is written. Then the fixture encodes what a violation is, independently of how the gate happens to detect one.
2. **RED.** Run the gate on the dirty fixture. Require failure (non-zero exit). If the gate passes it, the gate guards nothing. Fix the gate; the fixture stands.
3. **GREEN.** Run the gate on the known-good fixture. Require a pass (exit 0). A gate that rejects known-good is a false-positive machine, and it trains everyone to ignore it.
4. **Keep both fixtures in the repo, beside the gate.** They are the gate's evidence and its regression bed; deleting them returns the gate to unverified.
5. **Re-run the pair on every gate change.** A modified gate is a new gate. When a new violation class appears, extend the dirty fixture first (watch it go red), then teach the gate.

Verify-fix-reverify loop: red check fails → fix the gate → re-run; green check fails → fix the gate (or a genuinely broken fixture) → re-run; repeat until the pair passes in one run.

## The pair is necessary, not sufficient

A red/green pair proves the gate *can* say no. It does not prove the gate cannot be *fooled*, because the fixture only ever tries the input its author already imagined. This pack learned that the expensive way. Gates that separated their own fixtures cleanly were still walked past by inputs those fixtures never tried: a binding check satisfied by a string sitting inside an `echo`; a regression that vanished because its path was spelled with a capital letter; a crash that exited with the code reserved for a real verdict.

So after the pair passes, spend a few minutes trying to break your own gate. These six classes account for every bypass found while building this pack, and they recur across languages and gate kinds.

1. **An error path wearing a verdict's exit code.** A crash, unreadable file, decode error, closed stdin, or overflow exits `1`. That is the code reserved for "real violation", so the caller records a verdict the gate never computed. Give every error path its own code (`2` for usage/IO/malformed) and prove it with a fixture.
2. **Key normalization.** The same entity under a different spelling misses its join and falls to whichever branch is lenient: letter case, Unicode NFC vs NFD (routine on macOS), `./` and `../` and `//`, absolute vs relative. Normalize through one documented key function, or refuse the variant outright. Never silently reroute it.
3. **Silent row drops.** A comment rule (`startswith("#")`) applied to a field whose legitimate value can begin with that character deletes data without a word. A dropped row is a false green.
4. **Unanchored matching.** A required marker satisfied by a superstring, by text inside a comment or a string literal, or by a one-token idiom swap. Anchor patterns end to end, match whole tokens, and escape anything interpolated into a regex.
5. **Prose broader than the check.** The body says "every", "always", "refuses", while the code handles a narrower case. Widen the code or narrow the sentence; a claim the implementation cannot back is laundering under the first law.
6. **Numeric edges.** A printed percentage rounded away from the integer basis the verdict used; an unbounded integer conversion that raises; `NaN` slipping past a `<= 0` guard and quietly disabling the rule.

Each hole you close this way earns a fixture of its own, so the next reader inherits a captured run instead of a warning.

## One command

[`scripts/prove-gate.sh`](scripts/prove-gate.sh) runs the whole ritual: gate on bad fixture must fail, gate on good fixture must pass, anything else exits non-zero.

```bash
<this-skill-dir>/scripts/prove-gate.sh <bad-fixture> <good-fixture> -- <gate-command...>
# e.g., proving this pack's own validator — run from the pack root (unclebob/):
skills/known-dirty-fixture/scripts/prove-gate.sh scripts/fixtures/bad-island scripts/fixtures/good-island -- python3 scripts/validate-island.py
```

The fixture path is appended as the gate command's final argument.

## Enforced vs advisory

- `enforced` — the red/green acceptance itself: `prove-gate.sh` exits non-zero unless red-on-bad AND green-on-good both hold (syntax-checked with `bash -n`, run live below).
- `enforced` — this island's own structure: the pack validator `../../scripts/validate-island.py` checks F1–F11 mechanically, exit-code gated.
- `advisory` — fixture *quality*: whether the dirty fixture truly embodies the violation class, whether it was written from the rule rather than from the gate's behavior, and whether the pair is re-run on every gate change. No hook wires the pair into CI today, so steps 1 and 5 rest on discipline until a later wave installs one.

### This gate's own red/green proof

`prove-gate.sh` judges a *gate*, so its fixture pair is a pair of gates in [`scripts/fixtures/`](scripts/fixtures/). Run from this island's directory:

```bash
./scripts/prove-gate.sh scripts/fixtures/sample-bad.txt scripts/fixtures/sample-good.txt -- ./scripts/fixtures/dirty-gate.sh   # exit 1
./scripts/prove-gate.sh scripts/fixtures/sample-bad.txt scripts/fixtures/sample-good.txt -- ./scripts/fixtures/clean-gate.sh   # exit 0
```

`dirty-gate.sh` is a rubber stamp (`exit 0` always), so it is rejected: "FAIL red: … it guards nothing". `clean-gate.sh` is a real checker (no `TODO` may remain), so it is accepted: "ACCEPTED: red/green proven". Both exit codes were observed in this island's hardening run. Recompute them instead of trusting this line.

## Construction proof

This island demonstrates its own discipline twice, both runs captured in its build session:

- The pack's `validate-island.py` was accepted only after failing 6 checks red (F4–F9, exit 1) on [`../../scripts/fixtures/bad-island`](../../scripts/fixtures/bad-island/SKILL.md) and passing green (12/12, exit 0) on [`../../scripts/fixtures/good-island`](../../scripts/fixtures/good-island/SKILL.md). Recompute it with the command block above.
- `prove-gate.sh` is itself a gate, so it took the ritual too: run against a gate that cannot fail (`true`), it went red (exit 1, "guards nothing"); run against `validate-island.py` on the pack fixture pair, it went green (exit 0, ACCEPTED).

## Boundaries

- This island owns gate *acceptance* only: the red/green ritual by which any checker earns the right to guard. *What* a gate checks (a CRAP threshold, a dependency fence, mutation kills) is each gate island's own concern; this island never opines on thresholds or rules.
- Ongoing empirical improvement of a skill is [`skill-tune`](../../COMPANION.md#skill-tune)'s seat. Acceptance happens once per gate version; tuning is a measured loop that starts after acceptance.

## Done when

- [ ] The dirty fixture and the good fixture both live in the repo, beside the gate.
- [ ] `prove-gate.sh <bad> <good> -- <gate>` exits 0 in a single run.
- [ ] The exact pair command is written down where the gate lives, so anyone can recompute the acceptance instead of trusting it.

**No gate guards until it has failed — red on the dirty fixture, green on the clean one, both kept in the repo.**
