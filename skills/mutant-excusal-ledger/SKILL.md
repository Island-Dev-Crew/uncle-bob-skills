---
name: mutant-excusal-ledger
description: The honest 100% for mutation testing - mutant equivalence is undecidable (Budd & Angluin 1982) and 4-39% of mutants are equivalent in practice, so a literal 100% kill score is unreachable and every excused survivor carries a written equivalence argument in a ledger, with unexcused survivors blocking. Reach for it when a mutation run leaves survivors nobody can kill, when ruling whether a survivor is equivalent or merely unkilled, or when the user says "excuse this mutant", "equivalent mutant", "survivors are blocking the mutation gate", or "we'll never hit 100%". Differentiator - mutant-hunt owns the run and the kill-tasks; this island owns the ruling on what remains, and never lets "could not kill" be recorded as "equivalent".
---

# Mutant Excusal Ledger: the honest 100%

The hardener seat is "absolutely merciless" (C9): a surviving mutant "must be killed" (C7). This ledger exists because mercilessness runs into a hard limit. Detecting mutant equivalence is undecidable (Budd & Angluin 1982), and 4–39% of mutants are equivalent in practice, so a literal 100% kill score is provably unreachable (grounding: [research/mutation-testing.md](../../research/mutation-testing.md)). The honest 100% is killed + argued-equivalent, nothing unexplained. Every survivor gets either a killing test or a written excusal here, and an unexcused survivor holds the gate red (C4) until one of the two arrives.

## The anti-laundering rule

An excusal is an equivalence claim. "Could not kill it" describes the author's effort; "equivalent" describes the program. Only the second may enter the ledger, and it has to be argued. The `argument` field states why *no possible test* can observe the mutation: the mutated program computes the same function. Three that qualify — a redundant bounds check the type system already guarantees, a boundary the loop body makes unreachable, an operand swap under commutativity. A survivor you failed to kill but cannot argue equivalent stays a survivor. It goes back to the hunt as a kill-task, or it blocks. There is no third state.

Rule each survivor into one of three dispositions:

1. **missing-test**: killable. Return it to [`mutant-hunt`](../mutant-hunt/SKILL.md) as a concrete kill-task, a test that fails on this exact change. Killable mutants stay out of the ledger.
2. **equivalent**: unkillable by any test. Write the excusal entry below.
3. **dead or arid code**: the mutant survives because the code it mutates is unreachable or meaningless. The fix is a code change (delete or simplify it), and the discovery is a finding, not an excusal.

## Entry shape

Keep the ledger beside the run's captured output, at `evidence/<story-slug>/out/excusals.md`, one entry per excused mutant:

```
M-src/pricing.ts-41-2  src/pricing.ts:41
  mutation:   `<` flipped to `<=` on the loop bound
  argument:   the loop body indexes items[i] with items.length as the bound; the
              mutant's extra iteration would throw before producing any observable
              output difference, so the mutated program computes the same function
              over the full input domain.
  excused-by: Claude Fable 5
  head:       full SHA of the run this excusal was ruled at
```

The id is whatever the mutation tool emits: a PIT mutator+line, a Stryker id. The one contract is that it matches the survivor list byte-for-byte. `excused-by` names a seat (`OpenAI Codex`, `Claude Fable 5`, `Jon Isaac`; see [repo law](../../CONTEXT.md)). `head` pins the ruling to the exact code it examined, because an equivalence argument about code that has since moved is void.

## The gate

[`scripts/check-excusals.py`](scripts/check-excusals.py) reads the survivor list (one id per line, as the hunt emits it) and the ledger. It exits non-zero on any survivor with no entry, on an entry missing a required field, and on an argument under 40 characters:

```bash
python3 <this-skill-dir>/scripts/check-excusals.py \
  evidence/<slug>/out/survivors.txt evidence/<slug>/out/excusals.md
```

The loop: run the gate → for each FAIL, either write a real equivalence argument or send the mutant back to the hunt as a kill-task → re-run the gate until exit 0. Strike an id from the survivor list only when the re-run hunt confirms the kill. Stale excusals (entries for mutants no longer surviving) warn — prune them; sediment in a ledger is how laundering starts.

## Enforced vs advisory

- **Enforced** (by `check-excusals.py`, exit code, today): an unexcused survivor blocks; every entry carries `mutation`, `argument`, `excused-by`, `head`; the argument meets a 40-character floor.
- **Enforced** (by the pack validator): this island's own structure and frontmatter.
The gate carries its own red/green proof ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)), fixtures shipped beside it. Run from this skill dir, these exact commands produced these exit codes:

```bash
python3 scripts/check-excusals.py scripts/fixtures/survivors.txt scripts/fixtures/dirty-excusals.md   # exit 1 — RED
python3 scripts/check-excusals.py scripts/fixtures/survivors.txt scripts/fixtures/clean-excusals.md   # exit 0 — GREEN
```

The dirty ledger fires all three enforced rules at once: an unexcused survivor, an entry missing `head`, and `argument: could not kill it` (17 chars) rejected as effort wearing equivalence's name. Recompute both instead of trusting this paragraph.

- **Advisory** (honestly, unavoidably): the *truth* of an equivalence argument. No script can verify equivalence in general, which is the undecidability that put this ledger here in the first place. The character floor is a substance proxy standing in for the judgment call, not a truth check. A reviewer recomputing the packet judges the argument itself. Expect the excusal rate to land inside the 4–39% band from the research, and read a rate far above it as laundering pressure rather than bad luck.

## Boundaries

- Upstream, [`mutant-hunt`](../mutant-hunt/SKILL.md) owns the run itself (diff-scoping, covered-lines-only, the runtime budget) and the kill-task loop. This island consumes its *survivors* — the mutants left after kill-tasks are exhausted — and owns only the ruling on them.
- The ledger is an evidence artifact in [`evidence-packet`](../../COMPANION.md#evidence-packet) terms. `excusals.md` and `survivors.txt` live in the packet's `out/`, the gate run is a ladder rung that could have failed, and the reviewer recomputes it instead of trusting the excusal count.
- Durable cross-story findings graduate to [`finding-register`](../../COMPANION.md#finding-register). A recurring equivalent-mutant pattern (an operator your codebase makes systematically arid), or dead code a survivor exposed, becomes a register entry with a head and a recomputable command. The ledger stays per-run and per-story; it is never a second register format.

## Done when

Every id in the run's survivor list has either (a) a ledger entry that passes the gate or (b) a confirmed kill recorded by the re-run hunt. `check-excusals.py` exits 0 against the final survivor-list/ledger pair. Both files are captured in the evidence packet at the run's head. Anything short of that leaves the mutation gate red, so report it red: a score reported as 100% with an unexcused survivor is laundering.

**No authority without evidence. "Couldn't kill it" is a debt; "equivalent" is an argument. The ledger never lets the first wear the second's name.**
