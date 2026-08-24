---
name: thrash-watch
description: Live recognition of agent thrash - the struggle Uncle Bob says novices fail to see - read from a running agent's behavior (break-one-fix-another chains, circling, the outright give-up), plus the ordered intervention ladder that clears it. Reach for it while supervising a working agent that seems stuck, or when the user says "the agent keeps breaking things", "it's going in circles", "is this agent thrashing", or "it just apologized and changed two lines again". It reports by default - the destructive rungs of its ladder need an explicit repair ask. Differentiator - it watches the agent's behavior only; debugging the code is diagnose's seat, and the respawn rung executes via trajectory-hygiene.
---

# Thrash Watch: see the struggle

When Bob's agents failed in December, their behavior was the data, and he could read it: *"the important part was the next step where I watched them thrash. I could see the agent struggle and I recognized the struggle since I have been through that struggle… the novice would come in and not recognize the struggle"* ([C27](../../01-CONCEPT-LEDGER.md)). Recognition is the skill this island encodes. The root cause is almost always mess: *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). The threshold differs from a human's, but it exists (C2). A codebase a human still tolerates can already be spinning its agents.

## Report or repair - route before you watch

The first read is not of the agent, it is of **what the user asked for**. The signatures below cost nothing to run; rungs 2-4 destroy work. The mode is fixed by the ask, never by how alarming the finding turns out to be.

- **REPORT is the default.** Any diagnosis-shaped invocation - "is this agent thrashing", "why does it keep breaking things", "audit this session" - runs the watch and stops at the verdict. Name the signature by number, the files it keeps circling, and the last green ref. **That verdict is the deliverable.** The ladder is *quoted*, not climbed: say which rung would clear the signature and exactly what that rung would revert. The fix-until-green loop is not entered.
- **REPAIR is asked for, never inferred.** "Clean it up", "get the gates green", "fix it and re-run" unlocks the ladder below. A diagnostic ask plus a frightening finding is still a diagnostic ask - the alarm raises urgency, not authority. Rung 1 is the one exception either way: halting output destroys nothing, so a REPORT-mode watcher may stop a live agent and then report.

Two rules bind REPAIR however it was reached. Both **advisory** - no hook inspects an invocation's shape or a dirty path's owner today.

- **Name what you would revert before touching anything.** Print the paths, the last green ref, and the diff-stat that would be discarded, then wait for the human's go-ahead. An unnamed revert is an unreviewable one, and the supervisor is the one accountable for it.
- **A revert never discards work the human wrote.** Scope it to the supervised agent's own churn - the paths that agent touched this session - and leave the rest of the working tree alone. Uncommitted human edits are not thrash. Where the two overlap inside one file, quote that file to the human and revert nothing until they say which half goes.

## The lane

This island watches **agent behavior only**. The stream it reads is turns, diffs, test results, tone. When a signature fires, the question is *what is the agent doing*, never *what is wrong with the code*:

- **Debugging the code is [`diagnose`](../../COMPANION.md#diagnose)'s seat.** When an intervention exposes a real defect, hand it there and borrow its first rule by reference: build the observation loop first, a red-capable feedback loop before any theory. This island never carries a bug past the handoff.
- **Durable findings enter [`finding-register`](../../COMPANION.md#finding-register), never a second register here.** A module that reliably induces thrash, a mess hotspot confirmed across two sessions — register each as a `U-` entry with a recomputable command. The next supervisor then inherits the map instead of rediscovering the swamp.
- **The respawn decision executes via [`trajectory-hygiene`](../trajectory-hygiene/SKILL.md).** This island decides *that* rung 4 is needed; trajectory-hygiene owns the kill mechanics, the survivor ledger, and the pointer to the human-run `handoff` ritual.

## The signatures

The watch list: what struggle looks like live. All five are **advisory**, judged from the transcript and diff stream by the supervising seat. No hook parses a running session today.

1. **Break-one-fix-another chains.** Every fix breaks a neighbor, and the agent oscillates between two failing states. This is C2's spin in its purest form.
2. **Circling.** The same files opened, edited, reverted, re-edited across turns: motion without displacement. Grep the recent diffs. The same paths keep appearing and the net change keeps approaching zero.
3. **Shrinking diffs, growing apologies.** Each attempt touches less code and spends more tokens explaining. Effort migrates from the change to the excuse, and collapsing confidence reads as verbosity.
4. **Inadvertent-breakage cascades.** Tests go red in areas the task never named, and the blast radius widens turn over turn instead of narrowing.
5. **The give-up.** The agent says it outright: *"One agent one time said, 'I just can't deal with this anymore.'"* (C2). Terminal, so skip classification and go straight to the ladder.

One healthy look-alike to rule out before intervening: a genuinely hard task produces slow, *converging* progress. Its failing states differ each turn and its red set shrinks. Thrash repeats; work converges.

## The intervention ladder

Four rungs, **in order**. Take the lowest rung that clears the signature, re-observe, and escalate one rung on recurrence. Skipping straight to respawn wastes rungs 2–3, the two that fix the *cause*. Respawning onto the same mess re-buys the same thrash with a fresh context (C2).

1. **Stop the agent.** Halt output before more tokens land on the failing path. A context window has momentum: *"everything that follows in that same session… will continue following that trajectory"* (C11). Every further turn deepens the groove.
2. **Clean the mess.** REPAIR only, and scoped to the supervised agent's own churn, named before it is touched (see *Report or repair*). Mess is the root cause (C2): revert the churn to the last green state, delete half-finished edits, get the gates green again. Often the clean alone un-sticks the agent. Resume and re-observe before escalating.
3. **Repartition the module.** When the *same* module induces thrash after a clean, the module sits past the agent's mess threshold (C2). Split it, discipline its interfaces, then re-issue the task against the new shape. If the repartition surfaces a defect rather than a tangle, that is `diagnose`'s handoff.
4. **Respawn with fresh context.** The trajectory itself is poisoned, and *"the only way to clear the trajectory is to clear the context window"* (C11). Execute via `trajectory-hygiene`: persist survivors, kill, respawn onto the cleaned, repartitioned code.

## The watch loop

1. **Observe** the live stream: turns, diffs, test results.
2. **Classify.** Name the signature by number, or name "converging" and keep watching.
3. **Intervene** at the lowest sufficient rung; say which rung and why. In REPORT mode this step is written, not executed: name the rung, name what it would revert, and hand the decision to the human.
4. **Re-verify.** After the rung, watch for progress resumed: diffs substantive again, corrections stick, the red set shrinking. Same signature refires → escalate one rung. New signature → classify again.

**Done when:** in REPORT mode, the signature, the circling paths, the last green ref, and the rung that would clear them are on the record and nothing in the tree moved. In REPAIR mode, the agent is converging again (or rung 4 executed and the fresh context is on task), the signature and rung are named on the record, and any durable finding is registered in `finding-register`. A supervisor who cannot name the signature has not finished watching, and that unnamed struggle is exactly the novice's failure (C27). The recognition instinct itself is trainable: Bob's cure for the novice is the older canon where these lessons were first learned — DeMarco, Yourdon, the Pragmatic Programmer (C27).

## Evidence discipline

- **Enforced** (mechanical check exists today): this island's own structure, gated by the pack validator `scripts/validate-island.py` and its exit code.
- **Advisory** (judged, stated, never auto-blocked): every signature and every rung above, plus the report/repair routing, the name-before-revert rule, and the churn-ownership scope on rung 2. This is a v0 island and says so honestly. No script measures churn-per-turn, revert counts, or apology density yet. A later wave can add a deterministic churn probe; until it exists these rules stay labeled advisory rather than laundered into enforced.

**No authority without evidence. The struggle is visible before the failure is. Name the signature, take the lowest rung that clears it.**
