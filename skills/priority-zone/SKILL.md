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

## Report or repair — read which one was asked

The two trigger shapes end in different places, so settle which one arrived before running anything. *"Why does my agent ignore its rules"* and *"audit my CLAUDE.md"* are diagnosis: run `zone-lint.py` once, report Z1-Z4 with the flagged line numbers and what the U-curve costs the directives sitting there, and stop. **The verdict is the deliverable** — the fix-until-green loop below is not entered and no file is edited. *"Trim my system prompt"* is a request for the repair, and only then does the loop apply.

`zone-lint.py` is **read-only** in both modes: it reads the prompt file, prints Z1-Z4, exits. It rewrites nothing, and nothing on this island authorises an agent to rewrite a human's standing prompt until the exit code turns green. Every fix move below is a **proposed diff** — quoted with its line numbers, applied by the human, then re-verified by re-running the gate. The standing prompt is the human's own steering surface; an agent editing it in a loop removes the thing they asked to have inspected, and a green exit proves only that the file got smaller.

## Run the gate — verify, fix, re-verify

```bash
python3 <this-island>/scripts/zone-lint.py CLAUDE.md
python3 <this-island>/scripts/zone-lint.py AGENTS.md --max-lines 80 --max-tokens 1200 --head-lines 30
```

Exit 0 iff all four checks pass: Z1 file exists and is non-empty, Z2 line budget, Z3 approximate-token budget (ceil(chars/4), stated as an approximation), Z4 no hard directive past the head window (fenced code blocks skipped; an *unmatched* opening fence is refused rather than honoured — its tail is scanned as prose under a printed warning, so a truncated fence cannot hide a directive). On any red: trim, front-load, or relocate, then re-run. On a repair invocation, loop until exit 0 — the human applying each diff, the agent re-running the gate. Either the gate consents, or the prompt is not done.

Fix moves, in order of preference: cut (the line was sediment), front-load (it really is one of the 3-10), point (move detail behind a reference and keep one pointer line — relocation, not deletion: the rule still binds from where it now lives), gate (route it to `steering-audit` for prompt-vs-gate classification). How to word what survives (pointers, the two loads, pruning) is the neighboring island's craft, linked below.

## Boundaries

- **Document-level levers stay with [`writing-for-agents`](../../COMPANION.md#writing-for-agents).** Context pointers, the two loads, information hierarchy, pruning, failure modes. That island owns *how to write* what remains in the head. This island owns the *position and budget evidence and its enforcement*: how much may stand at the head, and where hard directives may sit.
- **Rule classification is [`steering-audit`](../steering-audit/SKILL.md)'s seat.** It decides which rules are generative, so they stay in the prompt, and which are checkable, so they move to a deterministic gate. This island measures size and position. It never classifies a rule's content.

## Enforced vs advisory

- `enforced` (mechanical, exists today): Z1-Z4 in [`scripts/zone-lint.py`](scripts/zone-lint.py). A non-empty file, the line budget, the approximate-token budget, and the head-window placement lint all fail closed with a non-zero exit.
- `enforced` as a recomputable red/green proof ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s ritual; run from this island dir). The shipped pair is one prompt twice: sediment pushed its binding rules below the fold. The clean half does not delete the operational rules it drops out of the head — it relocates them behind a pointer to `docs/checklists.md` and says so in the file (*"Relocated, not dropped; still required"*). That is the *point* move as shipped evidence: green here is a prompt that got re-ordered, not one that got shorter by losing rules. The third fixture is that same prompt with a truncated fence — the shape where an unclosed opening fence would otherwise swallow the file's tail and silence the directives in it.

```bash
python3 scripts/zone-lint.py scripts/fixtures/dirty-claude.md --max-lines 16 --max-tokens 200 --head-lines 12  # RED: exit 1 (Z2 23 lines, Z3 ~288 tokens, Z4 MUST/ALWAYS at lines 21-22)
python3 scripts/zone-lint.py scripts/fixtures/clean-claude.md --max-lines 16 --max-tokens 200 --head-lines 12  # GREEN: exit 0 (Z1-Z4 all OK)
python3 scripts/zone-lint.py scripts/fixtures/unclosed-fence-claude.md --max-lines 16 --max-tokens 200 --head-lines 12  # RED: exit 1 (Z4 still sees MUST/ALWAYS at lines 15-16 behind an unclosed fence, and warns about it)
```

- `advisory`: the default numbers (100 lines / 1500 tokens / 40-line head window); which 3-10 constraints deserve the head slots; lowercase or paraphrased directives, which the UPPERCASE regex deliberately does not chase (a deterministic proxy, not a semantic judge); and wiring the script into a hook or CI. Until a hook runs it, running it at all is on you.

**Ctrl-C.** A Ctrl-C (SIGINT) arriving mid-run is not a verdict. The seal maps `KeyboardInterrupt` to exit `2` — this island's non-verdict code — never to `0` or `1`, so an interrupted run cannot read as a pass or a finding. Pack policy: [CONTEXT.md — Interrupts are not verdicts](../../CONTEXT.md). A signal the interpreter never sees (`SIGKILL`, `SIGTERM`) is reported by the shell as `137`/`143` and is outside this table too.

## Done when

- [ ] The invocation was read as audit or repair — an audit ended at the reported verdict, with no file rewritten to chase exit 0.
- [ ] `zone-lint.py` exits 0 on the standing prompt at the budget you chose.
- [ ] The head window reads as identity + task frame + at most 10 generation-shaping constraints.
- [ ] Every directive the lint flagged was cut, front-loaded, pointed, or handed to `steering-audit` — none merely reworded in place to dodge the regex.

**The head is a budget, not a landfill: what must shape generation stands first, and everything checkable becomes a gate (C3).**
