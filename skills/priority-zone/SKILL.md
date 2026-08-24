---
name: priority-zone
description: The head-of-context budget for the standing prompt - the primacy/recency U-curve (Liu et al., TACL 2024), instruction-density decay (IFScale), and Horthy's smart zone, encoded as a hard size gate plus a placement lint that keeps must-follow rules where attention actually lands. Reach for it when a CLAUDE.md or AGENTS.md keeps growing, when agents obey rules only sometimes, or on "trim my system prompt", "why does my agent ignore its rules", "context budget for CLAUDE.md". Differentiator - this island owns the position and budget evidence and its enforcement; how many directives at once is instruction-density-cap's seat, the wording levers live in writing-for-agents, and prompt-vs-gate rule sorting is steering-audit's seat.
---

# Priority Zone: the head-of-context budget

Attention over a context window is not flat. The head is the priority zone: what stands there shapes generation. What sinks to the middle is obeyed *"in the Pirates of the Caribbean sense. They're more like guidelines"* (C3). The standing prompt is whatever loads at the head of every turn: the CLAUDE.md, the AGENTS.md, or the system prompt. This island turns that position evidence into two mechanical checks on that prompt: a hard size budget, and a placement lint that keeps hard directives in the head window.

## The evidence

All four grounds carry citations in [`research/lost-in-the-middle.md`](../../research/lost-in-the-middle.md). The numbers below are that file's, kept there so they cannot drift:

- **The U-curve.** Liu et al. (TACL 2024) showed accuracy traces a U as relevant material moves through a long context: highest at the very beginning (primacy) and end (recency), degraded in the middle. Beginning and end tokens draw more attention *regardless of relevance*. An instruction buried mid-context competes for attention it structurally does not get.
- **Instruction density.** IFScale: with hundreds of simultaneous directives even frontier models degrade, to ~68% at 500. Earlier instructions are favored (primacy again), and errors shift toward *omission*: the rule is not broken, it is silently skipped. Reasoning models hold to roughly 100-250 instructions, a graded decay rather than a cliff. Density is cited here only as a second reason the head budget is tight. Counting the directives and gating on the count moved out to [`instruction-density-cap`](../instruction-density-cap/SKILL.md).
- **The smart zone.** Dex Horthy's framing (verified attribution; the transcript mishears the name): recall degrades past ~40% context utilization, so ship the work inside the smart zone. Every token the standing prompt spends is smart-zone territory burned before the work begins.
- **Bob's form.** (C3): *"the stuff at the very beginning and the stuff at the very end have more prominence than the stuff in the middle… the 50th and the 80th sentence in there, they're gone."* His architecture: *"trim that initial prompt down to its absolute minimum so that you can get as much of it as possible into its priority… and then do deterministic tools after the fact."*

## The budget: what earns the head

The first N tokens carry exactly three things (the split in [`research/lost-in-the-middle.md`](../../research/lost-in-the-middle.md)):

1. **Identity.** Who the agent is in this repo, one or two lines.
2. **Task frame.** What kind of work arrives here, and what done means.
3. **The 3-10 constraints that must shape generation.** Style direction, architecture intent, the choices a post-hoc gate cannot recover because they steer *how the code is written*, not whether it passes.

Everything else is either a pointer to on-demand material or a deterministic gate that runs after generation. Checks compose without limit. Standing instructions compete and dilute, so when the budget is tight, a rule leaves the prompt before a constraint does.

Default numbers: 100 lines and ~1500 approximate tokens for the standing prompt, with a hard-directive head window of 40 lines. Those defaults are `advisory`. Tune them per repo and per model class, since IFScale says weaker models hold fewer simultaneous directives. The gate at whatever numbers you choose is mechanical.

## The placement lint

Positive target: hard directives live in the head window, where primacy lands on them. The lint flags any UPPERCASE directive token (MUST, ALWAYS, NEVER, CRITICAL, REQUIRED, IMPORTANT, SHALL) that appears past that window. Each flag is a rule the author treated as binding, parked where the U-curve starves it. A flag has three exits: front-load it into the head, spending one of the 3-10 slots; demote it to pointed-at reference; or hand it to [`steering-audit`](../steering-audit/SKILL.md) to become a deterministic gate.

## Run the gate — verify, fix, re-verify

```bash
python3 <this-island>/scripts/zone-lint.py CLAUDE.md
python3 <this-island>/scripts/zone-lint.py AGENTS.md --max-lines 80 --max-tokens 1200 --head-lines 30
```

Exit 0 iff all four checks pass: Z1 file exists and is non-empty, Z2 line budget, Z3 approximate-token budget (ceil(chars/4), stated as an approximation), Z4 no hard directive past the head window (fenced code blocks skipped). On any red: trim, front-load, or relocate, then re-run. Loop until exit 0. Either the gate consents, or the prompt is not done.

Fix moves, in order of preference: cut (the line was sediment), front-load (it really is one of the 3-10), point (move detail behind a reference and keep one pointer line), gate (route it to `steering-audit` for prompt-vs-gate classification). How to word what survives (pointers, the two loads, pruning) is the neighboring island's craft, linked below.

## Boundaries

- **Document-level levers stay with [`writing-for-agents`](../../COMPANION.md#writing-for-agents).** Context pointers, the two loads, information hierarchy, pruning, failure modes. That island owns *how to write* what remains in the head. This island owns the *position and budget evidence and its enforcement*: how much may stand at the head, and where hard directives may sit.
- **Rule classification is [`steering-audit`](../steering-audit/SKILL.md)'s seat.** It decides which rules are generative, so they stay in the prompt, and which are checkable, so they move to a deterministic gate. This island measures size and position. It never classifies a rule's content.

## Enforced vs advisory

- `enforced` (mechanical, exists today): Z1-Z4 in [`scripts/zone-lint.py`](scripts/zone-lint.py). A non-empty file, the line budget, the approximate-token budget, and the head-window placement lint all fail closed with a non-zero exit.
- `enforced` as a recomputable red/green proof ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s ritual; run from this island dir). The shipped pair is one prompt twice: sediment pushed its binding rules below the fold.

```bash
python3 scripts/zone-lint.py scripts/fixtures/dirty-claude.md --max-lines 16 --max-tokens 200 --head-lines 12  # RED: exit 1 (Z2 23 lines, Z3 ~288 tokens, Z4 MUST/ALWAYS at lines 21-22)
python3 scripts/zone-lint.py scripts/fixtures/clean-claude.md --max-lines 16 --max-tokens 200 --head-lines 12  # GREEN: exit 0 (Z1-Z4 all OK)
```

- `advisory`: the default numbers (100 lines / 1500 tokens / 40-line head window); which 3-10 constraints deserve the head slots; lowercase or paraphrased directives, which the UPPERCASE regex deliberately does not chase (a deterministic proxy, not a semantic judge); and wiring the script into a hook or CI. Until a hook runs it, running it at all is on you.

## Done when

- [ ] `zone-lint.py` exits 0 on the standing prompt at the budget you chose.
- [ ] The head window reads as identity + task frame + at most 10 generation-shaping constraints.
- [ ] Every directive the lint flagged was cut, front-loaded, pointed, or handed to `steering-audit` — none merely reworded in place to dodge the regex.

**The head is a budget, not a landfill: what must shape generation stands first, and everything checkable becomes a gate (C3).**
