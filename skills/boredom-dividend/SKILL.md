---
name: boredom-dividend
description: The mining method behind the whole pack - systematically revive practices that were shelved only because they bored humans, not because they were wrong, and turn each one into an agent-run gate. Reach for it when hunting for new quality gates, when an old practice (a metric, an exhaustive check, an overnight analysis) feels worth a second look, or when someone says "what gates should we add", "revive that old practice", or "we stopped doing that because it was too tedious". Differentiator - this island owns the mining move only (shelf inventory, wrong-vs-tedious triage, agent-feasibility pass); each revived practice ships as its own gate island, and the plumbing every gate plugs into lives on the Forge islands it names.
---

# Boredom Dividend: mine the shelf

Practices die two deaths, and only one of them is a verdict. Some were **wrong** — the premise failed, the target was bad. Some were **right but tedious** — the labor cost killed them while the verdicts stayed good. Bob's selection rule for reviving the second kind is one sentence: *"these guys are fast and they don't care how boring the work is and they will do what I tell them to do"* (C8). Tedium priced a practice out for humans; agents reprice it to near zero. That repricing is the dividend, and this island is the method for collecting it: inventory the shelf, triage each practice, feasibility-check the survivors, revive them as gates.

## The proof cases

Both of the pack's founding gates came off this exact shelf (C8):

- **CRAP** (C6) — shelved ~2000 on labor cost alone: *"it took me forever to go through every one of those functions… although it was interesting, I kind of set it aside."* Revived as an agent loop: *"why don't you run crap over everything you've just done and it would run crap and then it would clean up the code."* Full metric ground: [`crap-metric.md`](../../research/crap-metric.md); the revived gate lives at [`crap-gate`](../crap-gate/SKILL.md).
- **Mutation testing** (C7) — right since the 1970s, impractical at ~2000 scale (an overnight run), now: *"Maybe it took it 30 minutes instead of an overnight run and then it would plug all the holes."* The cost curve inverted along exactly the axis that shelved it — incremental caches and diff-scoped mutants ([`mutation-testing.md`](../../research/mutation-testing.md)); the revived gate lives at [`mutant-hunt`](../mutant-hunt/SKILL.md).

The pattern generalizes past one person's shelf: the roster names exhaustive dependency checks as the next specimen ([`02-ROSTER-50.md`](../../02-ROSTER-50.md), island 20), and the literature's shelf — techniques that never left the papers because running them by hand was absurd — is far larger.

## The mining method

### 1. Inventory the shelf

Enumerate practices that were abandoned — yours, the team's, the literature's:

- your own set-asides ("interesting, but I stopped")
- team lore ("we used to do X before every release")
- checklist items everyone skips, audits that quietly stopped running
- published techniques that stayed academic because the run cost was hours of human attention

Done when the inventory is a list, not a vibe: each entry names the practice, roughly when it was shelved, and who shelved it.

### 2. Triage: was it wrong, or was it tedious?

Bin every entry by **why it died**:

- **wrong** — the premise failed, it optimized a bad target, or evidence retired it. Stays shelved: reviving a wrong practice buys a fast gate on a bad target.
- **tedious** — the verdicts were good; hand-scoring, overnight runs, or mind-numbing repetition killed it. Candidate.
- **unverified** — nobody remembers why. Record that honestly and park it; guessing a bin launders ignorance into a verdict.

### 3. Feasibility pass

A tedious-but-right candidate revives only if an agent can run it **in a loop with a deterministic verdict**. Three letters, each pass/fail:

- **(a) mechanical execution** — a tool runs the practice end to end, with live human judgment fully outside the loop.
- **(b) binary verdict** — an exit code, a threshold breach, a killed/survived count. A prose impression cannot anchor the fix-until-green loop (C4's shape, owned by the gate islands).
- **(c) margin-safe cost** — fast enough to run per task or per story. The mutation case shows this letter is what usually flips: overnight → 30 minutes was the whole revival (C7). A candidate too slow today goes back on the shelf with a note naming the cost, because cost curves keep moving.

Record the three letters per candidate. A fail on any letter re-shelves the candidate *with the failing letter written down*, so the next mining pass starts from the record instead of re-litigating.

### 4. Revive as a gate — content into existing plumbing

A revived practice becomes **gate content only** — formula, threshold, input contract, verdict semantics — shipped as its own island and plugged into plumbing this pack never rebuilds:

- hook and pre-commit plumbing (where the check actually executes) belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails)
- gate infrastructure — loopback routing, the ledger, band caps — belongs to [`archipelago`](../../COMPANION.md#archipelago)
- the captured verdict (stdout + exit code) enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format as one rung of the packet's ladder, never a second evidence format

And before it guards anything, every revived gate **must pass [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) acceptance**: red on a known-bad fixture, green on a known-good one, both kept beside the gate. A revived practice that has never failed is nostalgia wearing a uniform. When the revival ports a human threshold, retuning the number is [`threshold-port`](../threshold-port/SKILL.md)'s seat — experiment, never agent vote.

## Enforced vs advisory

- `enforced` — the acceptance bar every revived gate must clear before guard duty: `known-dirty-fixture`'s `prove-gate.sh` exits non-zero unless red-on-bad AND green-on-good both hold ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)).
- `enforced` — this island's own shape: the pack validator (`../../scripts/validate-island.py`) checks it mechanically, exit-code gated.
- `advisory` — the mining itself: the inventory's completeness, the wrong-vs-tedious binning, and the three feasibility letters are judgment calls with no mechanical check today. A later wave can script part of the pass (verify a candidate tool exists and exits non-zero on a seeded violation); v0 states these honestly as advisory rather than laundering them into enforced.

## Done when

- [ ] Shelf inventory enumerated — every entry names practice, era, and who shelved it
- [ ] Every entry binned wrong / tedious / unverified, with the death-reason recorded
- [ ] Every tedious candidate carries a written (a)(b)(c) feasibility verdict
- [ ] Each revival shipped as gate content wired to the three named plumbing islands, and `prove-gate.sh` exited 0 on its fixture pair before it guards anything

Verify-fix-reverify: a candidate failing a letter re-shelves with the letter recorded; a gate failing acceptance is fixed and re-proven; the whole mining pass re-runs whenever the shelf grows.

**Shelved-for-wrong stays shelved; shelved-for-boring becomes a gate — the agent doesn't feel the boredom (C8).**
