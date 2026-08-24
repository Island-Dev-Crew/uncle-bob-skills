---
name: define-errors-out
description: Ousterhout's define-errors-out review pass. Delete error cases by redesigning the API instead of adding another handler for them, with the count of raised and propagated error paths before vs after as the verdict. Reach for it when an interface is accumulating exceptions, when an agent keeps answering a failure with one more try/except block, or when someone says "define errors out of existence", "too many error paths", "this API throws too much", or "stop adding handlers". Differentiator - this island removes branches by redesign; measuring complexity and enforcing its ceiling belong to crap-gate, and debugging a failure that actually happened belongs to the Forge.
---

# Define Errors Out: the case, not the handler

The cheapest error handler is the one you deleted along with the error. Ousterhout's move is not "handle it better". It is **redesign the interface so the failure case stops existing**, leaving nothing to raise, catch, document, or test ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)).

For an agent fleet the payoff is doubled. An error path is a branch, and a branch is a pathway the complexity score counts: *"a crap score of six means that there are six pathways through the function. They're all covered with tests"* (C6). Delete a case and the pathway goes with it. The score falls without anyone writing one more test. An error path is also a fact every caller must load. Agents read interfaces to avoid reading implementations (C16), and each declared failure mode is interface surface they cannot skip.

This island owns one pass: **inventory the error paths, interrogate each one, recount.** Quotes reach it only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## The pass

1. **Fix the boundary.** Name the module under review, then capture its current state as the baseline: `git show HEAD:path/to/mod.py > /tmp/before.py`.
2. **Inventory.** Run the counter over baseline and working copy. It lists every raise site, every except handler, and every assert with its enclosing scope. That listing is the worklist: one line per error path, nothing summarized away.
3. **Interrogate each path** with the four defusals below, in order. The first one that fits wins. A path that survives all four stays, and earns a one-line written justification naming why it is irreducible.
4. **Rewrite, then recount.** The gate is the delta. Loop until the tool consents (C4).

## The four defusals

Ask these of every path on the worklist, in this order. They run cheapest-redesign-first.

1. **Make the operation total.** Is there a definition under which the bad input is simply another legal input? Out-of-range endpoints clamp; deleting an absent key is a no-op; an empty range yields an empty result. The classic case is bounds checking that raises versus bounds checking that clips.
2. **Supply a default that is always correct.** Not a fallback the caller might reasonably disagree with, but a value the abstraction *defines* as the answer for that input. If two callers would want different defaults, this defusal does not fit. What you found is a missing parameter, not a missing default.
3. **Make the bad state unrepresentable.** Push the check up into a type or constructor so the invalid value cannot reach the function at all. One check at the edge replaces a raise in every function downstream.
4. **Absorb at one boundary.** The case is real, but it is not the caller's business. One module handles it so that N callers do not each grow a branch. This is aggregation, not suppression, and it lowers the count only when it genuinely removes the case from the callers' contracts.

Then the discipline that keeps all four honest: **a case you merely stopped mentioning is not a case you removed.** Defusal 4 degrades into swallowing the instant the absorbing module has no correct answer to give. If you cannot state what the caller now observes instead of the failure, the path survives.

All four defusals are `advisory`. No tool picks between them, and no tool can tell a redesign from a shrug. The count is the only enforced part.

## The gate

[`scripts/error-paths.py`](scripts/error-paths.py) parses both versions with `ast` and counts three things. Never grep: grep matches `raise` in comments and in strings.

- every `raise` site, bare re-raises included;
- every `except` handler, because a handler is itself a place the design still admits a failure;
- every `assert`, which is the same failure wearing a different statement.

Counting handlers is what gives the gate its teeth: **wrapping a case in one more `try` cannot lower the score**, since the wrapper is a new counted path. Counting asserts closes the cheapest rename beside it. Swapping `raise` for `assert` leaves the count exactly where it was (probed below). The verdict is the delta.

```bash
python3 scripts/error-paths.py BEFORE.py AFTER.py
```

Exit codes carry distinct meanings and never share one: `0` the after version exposes strictly fewer error paths; `1` a real negative verdict (same, more, or a baseline with nothing to remove); `2` misuse, meaning bad arguments, an unreadable or undecodable file, unparseable source, a `BEFORE` declaring no top-level `def`/`class`, or an `AFTER` missing any top-level `def`/`class` `BEFORE` declared.

That last check anchors on the whole definition set, not the error-bearing subset, because a redesign of one module does not delete its unrelated siblings. So deleting the raising function is exit 2. So is an unrelated file, the moment the baseline has one sibling the forgery lacks. Only `def`/`async def`/`class` count as definitions: `Window = "unrelated"` is a name, not a definition, and can never stand in for the `class Window` it replaced. A baseline whose error paths sit at module scope has no definition to anchor on at all, so it is misuse rather than a free pass.

What the check does **not** decide is whether two files are the same module. A baseline whose entire top-level surface is a single definition can still be matched by an unrelated file declaring that one name. That residue is the fourth known hole below; it is not closed here.

**Red/green proof.** Recompute from this island's directory:

```bash
python3 scripts/error-paths.py scripts/fixtures/before.py scripts/fixtures/after-defined-out.py  # exit 0 — 3 → 0, PASS
python3 scripts/error-paths.py scripts/fixtures/before.py scripts/fixtures/after-handled.py      # exit 1 — 3 → 5, FAIL
```

Both fixtures hold the same two functions. `after-defined-out.py` clamps the endpoints, so every input is legal and all three paths vanish. `after-handled.py` leaves the out-of-range cases exactly where they were, and adds a handler plus a new raise. The dirty fixture fails **because the error paths grew**, which is the check this island claims, not because the input was malformed. Deleting either fixture returns the gate to `unverified`, the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual.

Captured probes, same run:

- `AFTER` with the raising function deleted → exit 2
- `class Window` (3 paths) replaced by `Window = "unrelated"` → exit 2
- a module-scope baseline (raise + except + assert at module level) against an unrelated file sharing only an assigned `CONFIG` → exit 2
- a `main`-carrying baseline with one sibling definition, against an unrelated banner program declaring only `main` → exit 2
- missing file → exit 2; a binary (`/bin/ls`) → exit 2; unparseable source → exit 2; any flag → exit 2
- a `raise`→`assert` rename with nothing else changed → exit 1 (3 → 3, no credit)
- a baseline with zero error paths → exit 1 with *"nothing to define out, the pass is a no-op"*, so an empty gate cannot pass

Source is read as bytes, so `ast` honours a PEP 263 coding cookie. A legitimate latin-1 module returns a real verdict (exit 0 on a 3 → 0) instead of dying in the decoder, which would have spent the FAIL code on a crash.

One probe stays **red**, recorded rather than hidden. Strip that sibling, and the same baseline (a lone `main(argv)` holding all three paths) greens against the same unrelated banner `main`, exit 0. Single-definition modules are the shape the guard cannot separate.

## The known holes, named rather than hidden

The counter is arithmetic. *Why* a path disappeared is judgment. Each move below lowers the count without removing a case, and each was probed live. **The list is open**: a mechanical count can never enumerate every way a failure survives its statement.

- **The swallow.** Replacing three raise sites with one blanket `except Exception: pass` scores 3 → 1 and exits 0. Adding a handler cannot help you; collapsing many raises into one silent catch can. Mitigation is `advisory`. The pass records, per removed path, which defusal removed it, and mutation testing (this pack's `mutant-hunt`, roster line 5 in [`02-ROSTER-50.md`](../../02-ROSTER-50.md)) is what kills a branch that now silently returns garbage.
- **The relocation.** The definition stays where it is and now delegates to an imported helper that raises. Moving the *raise* next door that way scores 3 → 1 and exits 0, with the case alive one file over. (Moving the whole error-bearing definition out is caught by the check above: exit 2.) Mitigation is `advisory`: run the pass over every file the change touched, and require the delta to hold across the set, not per file.
- **The sentinel return.** Replacing the raises with `return None` scores 3 → 0 and exits 0, but the caller still writes `if window is None:`. The branch moved into the caller rather than leaving the design, so the complexity score this island promises to lower is unchanged. It is the C-style error code, the classic anti-pattern this pass exists to prevent, and no AST count can tell it from a genuinely total function. Mitigation is `advisory`, and it is the attribution rule above: **state what the caller now observes instead of the failure**. A sentinel the caller must branch on is not an observation. It is the same case renamed.
- **The substituted module.** The definition-set check asks *did every declared definition survive*, never *are these two files the same module*. When the baseline declares exactly one top-level definition, one shared name is the whole identity test: a wholly unrelated file carrying that name scores 3 → 0 and exits 0 (probed red above). One sibling definition is enough to bite, so the hole narrows as the module widens. It never closes here. Mitigation is `advisory`, and it is **same-path discipline**: derive the baseline from the module's own path, as the pass already prescribes (`git show HEAD:path/to/mod.py`), so an unrelated-file comparison is never constructed in the first place. A verdict whose two inputs came from different paths is `unverified`.

A gate whose holes are written down is worth more than one whose holes are discovered later by a reviewer.

## Boundaries

- **Measuring cyclomatic complexity, and holding its ceiling, belong to [`crap-gate`](../crap-gate/SKILL.md).** It owns the formula, the threshold regimes, and the fix-until-green verdict on complexity. This island reduces branches; it never measures or scores them. The two compose in one direction only: define errors out first, then let the CRAP gate observe the lower number.
- **Debugging a failure that actually happened belongs to [`diagnose`](../../COMPANION.md#diagnose).** Reproduce, minimise, hypothesise, fix with a regression test. This island is a design review over an interface at rest. If something is broken right now, that island runs first and this one runs after, on the shape the fix left behind.
- **Interface-shape vocabulary belongs to [`deep-modules`](../../COMPANION.md#deep-modules).** That covers deep versus shallow, the deletion test, and the entry-point rules. This island borrows nothing but the premise that interface surface is expensive.
- **The captured before/after report enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format** as one rung of a verification ladder, never a second evidence format.

## Enforced vs advisory

- `enforced`: the count and the verdict, and nothing wider than this list. `error-paths.py` derives both figures from the AST (raises, handlers, asserts). It exits 1 when the after version does not expose strictly fewer error paths, exits 1 on a zero-path baseline, and exits 2 fail-closed on bad arguments, an unreadable/undecodable/unparseable file, a `BEFORE` declaring no top-level `def`/`class`, and an `AFTER` missing any top-level `def`/`class` `BEFORE` declared. Both directions were executed above. The guarantee is **definition-shaped**, not module-shaped: it never certifies that the two inputs are one module. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: everything that is judgment. Whether the two inputs are even the same module (same-path discipline, the fourth hole's mitigation). Which defusal applies to a given path. Whether a surviving path is genuinely irreducible. Whether a removal was a redesign, a swallow, or a sentinel. The whole-changed-set scoping that closes the relocation hole. And the language reach: the counter reads Python only today, and the two counted constructs port to any language with throw/catch, but no other parser ships here.

Claiming more than this would launder advisory into enforced, and the pack's first law forbids it ([CONTEXT.md](../../CONTEXT.md)).

## Done means

- [ ] Baseline captured and the worklist printed: every raise site, handler, and assert in the module under review, none summarized away
- [ ] Every path on the worklist either removed by a named defusal (1–4) or kept with a one-line written justification
- [ ] `error-paths.py BEFORE AFTER` exits 0 across every file the change touched
- [ ] Removals attributed, each one naming its defusal, so a swallow cannot be read as a redesign
- [ ] The captured report filed as evidence, with the known holes' mitigation status stated

An open box means the verdict stays `unverified`: redesign, recount, re-check the boxes.

**Handle it and you own it forever; define it out and there is nothing left to own.**
