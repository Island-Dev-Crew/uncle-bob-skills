---
name: story-cadence
description: The comparative planning doctrine for the agent era - heavy upfront specification is the 1970s waterfall temptation replayed, and it decays mid-run for the same reason it always did, so where change is near-free, small batches with feedback beat plan-perfection. Reach for it when sizing how much plan to write before agents run, when someone proposes a spec-first pipeline or 2025-26 spec-driven-development tooling, or says "write the full plan first", "spec everything before the agents start", "how much should we plan upfront". Differentiator - doctrine only, the argument and its economics; ticket machinery, decision maps, and mid-run divergence detection live on neighboring islands.
---

# Story Cadence: small batches beat gorgeous plans

The doctrine, in one move: the urge to fully specify before agents run is *"a very old temptation… in the 70s. It led us to the waterfall process"* (C19, quoted via [the ledger](../../01-CONCEPT-LEDGER.md)) — and with agents it fails the same way it failed then, only faster. The answer is not a better plan; it is a shorter one, on a **cadence**: a story or two, look, sort out, next stories (C20). The economics that settles it is the cost-of-change collapse (C21). Everything below is that comparison made usable; all direct quotes are pulled through the ledger, never from memory.

## Why plans decay mid-run

The planner cannot foresee what execution reveals. Bob, from inside the failure the week of the conversation: *"you make all these plans and then as the agents are running, you realize that they can't follow that plan because you didn't think of everything… they're running half-cocked off on some nonsense that you have to stop, back up, rewrite the plan"* (C19). And the seduction that keeps the temptation alive: *"The agents love to write plans… the plans will be gorgeous and beautiful… And then they fall apart at the end"* (C19). Decay is structural, not a skill issue — waterfall broke on it in the 70s with human executors, and agents merely compress the interval between gorgeous and half-cocked.

## The cadence

Bob's replacement, verbatim: *"Let's just let them do a story or two, and then we'll look at the architecture at the end, and maybe I'll have to manually get involved… and then a few more stories and so on"* (C20). As a loop:

1. **Batch** — plan only a story or two ahead; that is the execution horizon before the next human look.
2. **Look** — inspect the architecture the batch actually produced. This is the verify step.
3. **Sort out** — manually reorganize where the look found drift. This is the fix step, and Bob concedes it may be permanent: *"We may never escape that manual organizing step at the end. Although I'm trying to figure out a way to do it"* (C20).
4. **Next stories** — re-plan from the repo as it now is, not from the original plan. The next batch's look is the re-verify.

A plan that survives contact intact is the exception, so the cadence treats re-planning as the normal cost of each cycle, not as failure.

## The economics: the $1 house

*"the cost of change has plummeted to as close to zero as I think we're ever going to get it… why would you do this upfront planning because that's expensive. Why wouldn't you just fiddle fiddle fiddle fiddle until it looks right?"* (C21). Waterfall's whole premise was Boehm's curve — late change costing up to ~100x — which made front-loading rational; XP's premise was that flattening the curve makes small batches rational ([atdd-gherkin-agile](../../research/atdd-gherkin-agile.md)). Agents flatten it further, toward the $1 house: nobody pays an architect for a perfect one-shot plan when every change costs a dollar. **Where change is near-free, fiddle-with-feedback beats plan-perfection.** Upfront depth stays rational only where change is still genuinely expensive — irreversible data migrations, published API contracts, security boundaries — and the doctrine asks that any such exception be named as one, out loud, before the big plan gets written.

## The SDD echo, 2025-26

*"There's this movement towards spec-driven development… my impression there is that that's probably not going to work"* (C19). The research brief grounds the echo: the 2025 SDD tool wave (GitHub Spec Kit, AWS Kiro, OpenSpec) arose against vibe-coding drift, and reviewers already report the waterfall failure shape — plan artifacts piling up (a Scott Logic review's "sea of markdown documents", secondary-sourced in the brief, `unverified` as a verbatim quote) and tooling that cannot detect implementation/spec divergence, so specs silently drift from the code (Kiro) ([atdd-gherkin-agile](../../research/atdd-gherkin-agile.md)). A spec pipeline is not condemned by this doctrine — a spec that launches one small batch through gates is agile; a spec that tries to pre-decide the whole run is waterfall wearing 2026 tooling.

## Right-sized plan: done when

A planning conversation has landed inside this doctrine when every box checks:

- [ ] Execution horizon before the next human look is a story or two, stated as a number.
- [ ] The architecture look and manual sort-out are scheduled at the end of the batch, not "when we have time" (C20).
- [ ] Re-planning after each batch is budgeted as normal cost, not logged as plan failure.
- [ ] Any deep-upfront exception names the concrete high-cost change justifying it (C21).
- [ ] The plan document is treated as ephemeral scaffolding — its lifecycle (delete on merge) belongs to [`spec-mulch`](../spec-mulch/SKILL.md), not here.

## Enforced vs advisory

Every rule in this island is **advisory**: this is doctrine, and no mechanical checker of batch size, plan decay, or change-cost exists on this island today — v0 ships no script by design (doctrine only, per the roster line). The only **enforced** check touching this island is the pack validator (`unclebob/scripts/validate-island.py`) gating this file's own shape, which says nothing about whether your planning obeys the doctrine. The paths to making it mechanical are already seated elsewhere: see the boundaries below.

## Boundaries — who owns what

- **Ticket and tracer machinery** — turning stories into specs, tickets, and implementation passes is [`spec-pipeline`](../../COMPANION.md#spec-pipeline)'s seat; this island only argues how *short* each pass should be.
- **Multi-session decision maps** — charting a foggy effort too big for one session is [`wayfinder`](../../COMPANION.md#wayfinder)'s seat; this island governs the batch size inside a lane, not the map of lanes.
- **Mid-run divergence detection** — mechanically catching a plan decaying against observed repo state is `plan-decay-detector`'s seat (Wave 3, forthcoming); until it lands, decay-spotting is human judgment.
- **Measuring the actual change-cost** — testing the $1 premise against your repo's real numbers is `change-cost-probe`'s seat (Wave 3, forthcoming); until it lands, the collapse is an argument, not a measurement.
- **Ephemeral spec lifecycle** — the spec-dies-on-merge rule is [`spec-mulch`](../spec-mulch/SKILL.md)'s concern (C22); this island stops at cadence.

**No authority without evidence. Plan a story or two, look, sort out, go again — the gorgeous plan is the temptation, the cadence is the discipline.**
