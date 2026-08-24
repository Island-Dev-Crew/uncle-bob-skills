---
name: threshold-port
description: Port a human engineering practice into an agent lane and recalibrate its numeric gate parameters (complexity caps, coverage floors, CRAP cutoffs) by controlled experiment. Use when adopting a human discipline for agents or picking a gate level, e.g. "should agents do strict TDD", "what CRAP threshold for agent code", "is our coverage floor right for the agent lane", or when a threshold was set by vibe or by polling the agents. Differentiator - this island owns the value/ritual/threshold split for numbers; markdown files and the measure-edit-keep loop belong to skill-tune.
---

# Threshold Port: keep the value, drop the ritual, move the number

Bob's sharpest line in the conversation draws the whole map: *"it's probably a mistake to impose a human discipline on an agent. It is not a mistake to impose human values on the agent, but there may be thresholds that we need to change"* (C17, [ledger](../../01-CONCEPT-LEDGER.md)). This island turns that line into a repeatable port. TDD, a coverage floor, a complexity cap: each one crosses to the agent lane in three moves, and the number at the end moves only on evidence.

## Scope: numbers, not markdown

This island targets numeric gate parameters. Complexity caps, coverage floors, CRAP cutoffs, mutation budgets are what gets ported here, never markdown files. Tuning a skill, a CLAUDE.md, or any prose context file is [`skill-tune`](../../COMPANION.md#skill-tune)'s lane entirely.

The experimental engine this island leans on is skill-tune's too. The measure-edit-keep-iff-score-moved loop belongs there and is referenced here, never re-derived. Run that loop with the gate level as the one edited variable and lane outcomes as the score. This island supplies the rest: what to keep, what to drop, and what counts as a win for a *number*.

## Move 1: keep the value

Name what the practice actually protects, as a property a tool can measure: tested, covered, small, clean. Values transfer intact (C17). If the value resists measurement, the port is not ready for move 3. Carry it as advisory prose and say so, until a measurable proxy exists.

## Move 2: drop the ritual

The ritual is the human-wired procedure around the value, the part shaped by human working memory, boredom, and habit. Classify a rule as ritual when it constrains the order or rhythm of the work rather than a measurable property of the result.

The canonical case (C17) is strict TDD line-interleave, which Bob explicitly does not impose: *"I don't think it makes any sense to make an agent write a single line of a test and then write a single line of the production code."* Agents naturally *"write a function and then write the test for that function"*, and *"They always fall back on doing that… So I figure that's probably okay."* The value crosses whole: every path covered by a test. The red-green rhythm stays home.

## Move 3: retune the threshold by controlled experiment

Human-calibrated numbers carry human assumptions, so the ported level starts as a hypothesis. Bob's own path is the template (C17): *"for a human I would keep crap numbers below four… but for the agents I've set this at six and… maybe I'll push it to eight."* Here is skill-tune's loop, run on a number:

1. Baseline at the current level. Record real lane outcomes: defect escapes, thrash incidents (change-one-break-another loops), gate-failure rate, productivity margin.
2. Change one level: one variable, one step. Go 4→6, then 6→8; a 4→8 jump makes the delta unattributable.
3. Run real work at the new level, long enough to collect the same outcomes.
4. Keep iff no worse: outcomes held or improved. Otherwise revert and log why, so the next porter does not retry it.

## The hard rule: evidence decides, agents propose

Agent opinions enter the experiment only as hypotheses in step 2. Bob polls his agents on threshold levels and treats the answers as color, never as a decision: *"you can't trust any debate you have with an agent"* (C18). A level that traces to an agent vote instead of a measured step is authority without evidence, wearing a port as a disguise.

## The rationale is a tunable too

Bob justifies the looser agent level by *"a huge short-term memory and a perfectly accurate short-term memory"* (C17). That is his hypothesis, not established research, and [`research/crap-metric.md`](../../research/crap-metric.md) flags it unverified. Treat the rationale exactly like the number. If agents thrash at 8, the hypothesis lost, however good the story. Outcomes outrank rationales in both directions.

## The port record

One row per ported practice, kept beside the gate config it calibrates:

```
practice    value kept (measurable)      ritual dropped           level path        evidence per step
TDD         all paths test-covered       line-interleave rhythm   n/a (no number)   C17 precedent + lane baseline id
CRAP gate   small + fully tested fns     manual per-fn review     4→6 (kept)        outcome rows per step, run ids
```

The `evidence per step` cell names the recorded outcome comparison for each level change. Where no comparison exists, it reads `unverified — inherited human level, not yet tested`. Formula, regimes, and per-language tooling for the CRAP example live in [`research/crap-metric.md`](../../research/crap-metric.md); the values-not-disciplines source line is traced in [`research/martin-canon.md`](../../research/martin-canon.md).

## Done when

- the value is stated as a measurable property and the destination gate measures it;
- every dropped rule is classified ritual via the order-or-rhythm test;
- every level in force is the latest step of a one-variable experiment with recorded outcomes, or is explicitly marked `unverified — inherited human level, not yet tested`;
- no level traces to an agent poll;
- the port record shows all of the above.

Verify → fix → re-verify: walk the record row by row against these five conditions, repair the first miss, then walk again from the top until a full pass.

## Enforced vs advisory

- **Enforced (today)** — this island's own shape: `python3 scripts/validate-island.py skills/threshold-port`, run from the pack root, exits 0. In a destination repo, a ported threshold is enforced only where its tool blocks on breach with a non-zero exit (crap4py already does; see [`research/crap-metric.md`](../../research/crap-metric.md)). Until that wiring exists, the level is advisory and the port record must say so.
- **Advisory (v0)** — the three-move classification, the one-step-at-a-time discipline, the no-agent-vote rule, and the port record format. No script here checks them yet. A later wave can add a port-record linter; until then this is honest guidance, and calling it enforced would be laundering.

**No authority without evidence. Values transfer; rituals stay home; the number moves one measured step at a time.**
