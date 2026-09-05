---
name: coupling-budget
description: Treats every cross-module edge a change adds to the edge sets it is handed as spend against a declared budget - each added edge carries a written reason or the gate goes red, and the count itself is capped so prose cannot buy unlimited coupling. Reach for it when reviewing an agent diff that reaches into a module it never touched before, before fanning parallel agents across module lanes, or on trigger phrases like 'coupling budget', 'the agent added a new dependency', 'why does this import cross modules', 'how much coupling did that change add'. Differentiator - this island owns the budget on coupling a change ADDS; declared layering direction belongs to the sibling dependency-fence, computed instability and abstractness to stability-order, and cohesion sizing to component-cohesion.
---

# Coupling Budget: every new edge is spent, not free

Constantine's pair, coupling and cohesion, was canonised in Stevens, Myers & Constantine, *Structured Design*, **IBM Systems Journal 13(2), 1974, pp. 115–139**, from work he had been developing since the mid-60s ([`seventies-canon.md`](../../research/seventies-canon.md)). It gave designers a vocabulary for a thing they could otherwise only feel. Fifty years on, the thing being judged is an agent's diff, and the vocabulary still fits. But a vocabulary is not a gate. This island turns the coupling half into an account with a balance.

Bob's version of the same idea, at module scale: *"Anything that is well partitioned with well-disciplined interfaces… is something a human can grasp because we compartmentalize in our minds. Well, so do the models"*. And the failure mode: *"If you load up a module with every bit of stuff under the of under the sun [sic], the poor agent is going to wonder, 'What the heck am I doing in here?'"* (C15, via [the ledger](../../docs/01-CONCEPT-LEDGER.md); the `[sic]` is carried from its caption-garble marker rather than smoothed away). Coupling un-partitions a system one import at a time, and each import looks locally reasonable. That is exactly the shape of damage a fast worker does invisibly: agents *"are as subject as humans are to messy code"* and eventually *"just start to spin"* (C2).

## The agent-era stake: parallelism is bought with low coupling

Bob runs coders concurrently: *"you could have three coders running at the same time. And my little laptop can support a lot more than three"* (C10). Concurrency at that scale rests on one writer per module, and one writer per module is safe only while modules do not reach into each other. The reading that low coupling is what makes parallel agents on separate files safe belongs to [`seventies-canon.md`](../../research/seventies-canon.md)'s analysis of the 1974 canon; the 1974 paper does not make that claim. The paper supplies the taxonomy, the brief draws the agent-era consequence. Either way the accounting runs one direction only: **every cross-module edge an agent adds narrows the next fan-out.** Track the spend while it is one edge, or meet it later as a merge conflict.

## What the gate counts

The unit is the **delta**, not the graph:

```
added   = current cross-module edges - baseline cross-module edges
removed = baseline cross-module edges - current cross-module edges
```

Three rules over that delta:

1. **OVER-BUDGET**: `count(added)` above the declared budget. A justified edge is still spend; prose is not currency.
2. **UNJUSTIFIED**: an added edge with no justification entry.
3. **THIN-REASON**: a justification carrying fewer **visible characters** than `--min-reason` (default 20). Visible means NFC-normalised codepoints, minus the three zero-width Unicode category groups (control/format C, combining marks M, separators Z), minus a named set of blank glyphs that fall outside those groups: the Hangul fillers, the Braille blank, the Khmer inherent vowels, the Mongolian vowel separator. So twenty zero-width joiners are worth nothing, twenty Braille blanks are worth nothing, and the count the report prints is the count the verdict used. That set is a named list, not a rendering test; a blank codepoint outside it still counts 1, and the fixture below draws that line.

**Removals are reported as credit and never spent.** Net-zero accounting would let a change pay for a hard new coupling by deleting a trivial one somewhere unrelated, so the report prints the credit and the budget ignores it. That is a decision made here, stated rather than hidden.

## The input contract

One JSON file, structural throughout. The checker parses objects and arrays and holds no regex, so there is no pattern in it to fool with an idiom swap:

```json
{
  "note": "optional, ignored by the checker",
  "budget": 2,
  "modules": ["web", "billing", "domain", "legacy"],
  "baseline": [["web", "domain"], ["web", "legacy"]],
  "current": [["web", "domain"], ["web", "billing"], ["billing", "domain"]],
  "justifications": [
    {"edge": ["web", "billing"], "reason": "read only status api"}
  ]
}
```

- **`budget` has no default.** Missing and unoverridden, it exits 2: the number of new couplings you will accept is a decision, and silence is not one.
- **Every endpoint must be declared in `modules`.** An undeclared endpoint exits 2, so a renamed or newly-invented module is a spec error rather than an edge that quietly vanishes from the delta.
- **Module names join through one key function**: Unicode NFC, then strip. Two declared names differing only by letter case are **refused** (exit 2), never silently joined; NFD input from macOS joins with its NFC twin.
- **Cross-module edges are deduped module pairs**, so a hundred imports along one pair count once. `["a","a"]` is an intra-module edge, excluded from coupling; its raw occurrence count is printed in the header, on both sides, `baseline` and `current`, rather than dropped in silence.
- **A `current` with no cross-module edges exits 2**, whether it is empty or full of self-edges. A coupling-free extraction is a failed extraction far more often than a coupling-free repo, and an empty gate must not pass. The tripwire tests the *cross* set, not the raw array. The roll-up bug that most plausibly breaks an extraction maps every path onto one module, and that arrives as a non-empty list of self-edges, not as `[]`.

Extracting `current` is your stack's job (`go list -deps`, `jdeps`, dependency-cruiser rolled up to package level, an import scan); `baseline` is the same command run at the merge base. Record the command in the repo so any seat reproduces both sides identically.

## Running it

```bash
python3 scripts/coupling-budget.py change.json --budget 2 --min-reason 20
```

Exit **0** within budget with every added edge justified at or above the reason floor, **1** violations, **2** usage error, unreadable or non-UTF-8 file, malformed spec, or internal failure. (`-h/--help` prints usage and exits 0 without judging.) The three exit codes stay distinct on purpose: 0 and 1 are the verdicts, 2 is the refusal to reach one, and a broken spec must never read as consent. It runs as the tool at the end of C4's loop — *"you must you must [sic] change the code until this tool says that it's okay."*

**The enforcement point is the invocation, not the file.** The spec's `budget` field sits in the agent's write lane, so an agent that adds six edges can also write `"budget": 99` and green itself. That is [`budget-inflation.json`](scripts/fixtures/budget-inflation.json), a captured exit-0 run below. Pin the number in CI with `--budget N`. The flag always wins over the spec (`budget_of`), so the field becomes a declaration the agent may *propose*, and the pinned flag is the one that judges. The same spec at `--budget 2` exits **1**.

**When it goes red the levers are budget-shaped**: don't add the edge; reach the same capability through a seam that already exists; or raise the budget, deliberately, in its own commit, as a human act, never as an agent's escape hatch. That last lever is a human act because a human moves the pinned flag, not because prose asked nicely. Which *structural* edit implements the third option (inverting a dependency, inserting an interface, splitting a module in half) is [`dependency-fence`](../dependency-fence/SKILL.md)'s three-repair menu (C14), not this island's.

## The number is not the metric

`--budget` and the 20-character `--min-reason` floor are starting points, not findings. Thresholds are precisely the part of a human practice that moves when the worker changes (C17), so tune both the way this pack tunes any gate parameter: run at each candidate level, capture the outcomes, keep the level the evidence picks. That loop is [`threshold-port`](../threshold-port/SKILL.md)'s. An agent's opinion about the right budget is a hypothesis: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18).

## Boundaries

- **Parallel-agent isolation mechanics** (worktrees, per-agent checkouts, who writes where on disk) belong to [`worktree-fleet`](../../COMPANION.md#worktree-fleet), and so does the evidence rule that **worktree artifacts are inadmissible as gate evidence until re-derived from a fresh clone**. This island argues *why* low coupling makes one-writer-per-module possible, and prices the additions. It never lays out a filesystem, and a green run produced inside a worktree obeys that island's re-derivation rule before it counts.
- **Declared layering direction**, which module *may* depend on which, is the sibling [`dependency-fence`](../dependency-fence/SKILL.md). Direction is a rule you write; this is a quantity you spend. A change can point perfectly inward and still add six new inward edges.
- **Instability, abstractness, and the distance from the main sequence** are [`stability-order`](../stability-order/SKILL.md)'s computed numbers over the whole graph. This island prints no `I`, `A` or `D`, only the delta and who spent it.
- **The cohesion half of the 1974 pair** (REP/CCP/CRP, and sizing a component to a context window) is [`component-cohesion`](../component-cohesion/SKILL.md)'s.
- **Where the checker executes** (pre-commit, PostToolUse, a CI step) belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails); this island installs no hook. Gate infrastructure — loopback, ledger, band caps — belongs to [`archipelago`](../../COMPANION.md#archipelago). The captured report becomes one rung in [`evidence-packet`](../../COMPANION.md#evidence-packet) format, never a second format.

## Enforced vs advisory

- `enforced`: the three verdicts over the delta. [`scripts/coupling-budget.py`](scripts/coupling-budget.py) computes added and removed edges from the declared sets, and exits 1 on OVER-BUDGET, UNJUSTIFIED or THIN-REASON. It exits 2 fail-closed on a missing budget with no `--budget` override, a non-integer or negative budget, a `NaN`/`Infinity` JSON constant, an undeclared endpoint, case-ambiguous module names, an unknown top-level key, a duplicate or malformed justification, a `current` carrying no cross-module edges (empty, or all self-edges), an unreadable or non-UTF-8 file. A UTF-8 BOM and CRLF line endings parse normally. This island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: everything feeding it. Whether a module boundary is drawn where it should be, the extraction command, the budget number, the reason floor, and above all **whether a reason is any good**. The checker measures that a reason exists and carries at least a floor's worth of visible characters. It cannot read it: a reason of twenty real letters saying nothing clears the floor exactly as one saying something does. A human still does.

**Red/green proof** — the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual, recomputable from this island's directory:

```bash
python3 scripts/coupling-budget.py scripts/fixtures/dirty-change.json   # exit 1
python3 scripts/coupling-budget.py scripts/fixtures/clean-change.json   # exit 0
python3 scripts/coupling-budget.py scripts/fixtures/invisible-reason-refused.json   # exit 1
python3 scripts/coupling-budget.py scripts/fixtures/blank-glyph-reason-refused.json   # exit 1
python3 scripts/coupling-budget.py scripts/fixtures/collapsed-rollup.json   # exit 2
python3 scripts/coupling-budget.py scripts/fixtures/over-budget-only.json   # exit 1 — OVER-BUDGET is the only violation
python3 scripts/coupling-budget.py scripts/fixtures/over-budget-only.json --budget 2   # exit 0 — the same file, one budget higher
python3 scripts/coupling-budget.py scripts/fixtures/unjustified-only.json   # exit 1 — UNJUSTIFIED is the only violation
bash ../known-dirty-fixture/scripts/prove-gate.sh scripts/fixtures/dirty-change.json scripts/fixtures/clean-change.json -- python3 scripts/coupling-budget.py   # exit 0, ACCEPTED
```

The dirty run exits **1** on a well-formed spec, raising all three verdict kinds at once: `OVER-BUDGET added 3, budget 1`, `THIN-REASON billing to platform (reason 3 visible chars, minimum 20)`, `UNJUSTIFIED web to platform (no justification entry)`. It fails on the check, not on the parse.

The clean run exits **0** carrying the boundary cases, so the pair proves discrimination rather than blanket acceptance. Added is exactly at budget (2 of 2). One reason is exactly at the floor, 20 visible characters. A removal is reported as credit, a duplicate edge entry is deduped, an intra-module edge is excluded and counted in the header, and a stale justification is noted without convicting. Nudge either boundary and it goes red: `--budget 1` on the clean fixture exits 1, `--min-reason 21` exits 1.

The third fixture is the invisible-reason close. Twenty zero-width joiners and twenty combining accents each survive whitespace collapse at length 20 and once bought a green at the default floor. Counted as visible characters both now read **0** and go red, while an ordinary NFD-accented reason in the same run still passes on its base letters.

The fourth carries that close past the category filter, where two blank glyphs used to walk through. Twenty U+2800 BRAILLE PATTERN BLANK (category So) and twenty U+3164 HANGUL FILLER (category Lo) draw no ink but sit outside C, M and Z, so each once counted 20 and bought a green; the named `BLANKS` set now takes them out and both read **0**. The same fixture pins the top-up case: a real nineteen-character reason padded with one Braille blank reads 19, not 20, so it goes red at the floor, while a genuine 32-character reason in the same run passes. The set is a list of codepoints rather than a rendering test, so a blank codepoint nobody has named still counts 1. That residue is the boundary this fixture draws. It stays bounded: such an edge is still spend against OVER-BUDGET, and the floor never judged a reason's quality in the first place.

The fifth is the failed-extraction close. A roll-up bug collapsed every path onto `web`, so `current` arrives **non-empty** carrying four self-edges and zero cross-module edges, and the baseline's three edges would have read as pure credit: `added 0, budget 0` and a green. It now exits **2**, because the tripwire measures the cross set the gate actually judges rather than the raw array. Deleting any fixture returns the gate to `unverified`.

**Each verdict is load-bearing on its own.** The dirty run raises all three verdicts at once, and the pack verifier compares exit codes, not reason text, so the `OVER-BUDGET` line could be deleted from the script and that run would still exit 1 on its neighbours: the gate would have lost the verdict it is named for and every pack tool would stay green. The two `-only` fixtures close that. [`over-budget-only.json`](scripts/fixtures/over-budget-only.json) adds two well-justified edges against a budget of one, so `OVER-BUDGET added 2, budget 1` is its only violation, and the same file at `--budget 2` exits 0: the code moves with the count and with nothing else. [`unjustified-only.json`](scripts/fixtures/unjustified-only.json) adds two edges inside a budget of two, one with a reason above the floor and one with no entry, so `UNJUSTIFIED billing to domain` is its only violation. Replace either emission in the script with `pass` and its fixture goes green, which `verify-proofs.py` reports as a mismatch; that was watched rather than inferred, and anyone with the same edit can watch it again. THIN-REASON needs no third fixture: the invisible-reason and blank-glyph runs above already add within budget with every edge justified, so THIN-REASON is the only violation either raises, and removing its emission turns both green.

**Three blind spots, captured rather than described.** All three are exit-0 runs the gate consents to and should not be read as "no coupling was added":

```bash
python3 scripts/coupling-budget.py scripts/fixtures/baseline-laundering.json     # exit 0
python3 scripts/coupling-budget.py scripts/fixtures/deepening-blind-spot.json    # exit 0
python3 scripts/coupling-budget.py scripts/fixtures/budget-inflation.json        # exit 0
```

The first: the gate reads one file and cannot know the `baseline` is yesterday's truth. An agent that writes the edge it is about to add into `baseline` shows a delta of zero and passes at budget 0. The mitigation is procedural: regenerate `baseline` from the merge base with the recorded command, outside the agent's write lane. The second: cross-module edges are deduped module pairs, so forty new call sites along an existing `web`/`billing` edge are not representable as a delta and cost nothing. A deepened coupling is invisible here. That is the input contract's price, and reaching for it is the whole-graph islands' job, not this one's. The third: the spec's `budget` field is agent-writable, so six new edges under `"budget": 99` pass. Its mitigation is mechanical rather than procedural, and it is the pinned `--budget` above (`--budget 2` on that same file exits 1).

## Done means

- [ ] `baseline` and `current` come from the same recorded extraction command, run at the merge base and at HEAD
- [ ] The budget is a declared number with a person's name on the decision to move it, and the number CI judges against is pinned with `--budget`, outside the agent's write lane
- [ ] Every added edge has a reason a reviewer read, not merely one the checker measured
- [ ] The captured exit-0 run is in the evidence packet; a green asserted without it stays `unverified`
- [ ] The three blind-spot runs are understood as blind spots, not as clearance

**Coupling is spent, not discovered.** Every new edge either names its reason and fits the budget, or the change goes back: *"you must you must [sic] change the code until this tool says that it's okay"* (C4).
