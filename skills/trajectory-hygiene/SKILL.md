---
name: trajectory-hygiene
description: Mid-session context stewardship - the kill-vs-continue call on a running context window, because a context has momentum and contamination never washes out. Reach for it mid-task when a session drifts or fixates on a dead idea, the topic pivots, or utilization creeps past the smart zone - "this session feels poisoned", "should I kill this context or keep going", "the agent keeps going back to that". Differentiator - owns only the mid-session lane; the context ending ritual is handoff's seat and doc-level economy is writing-for-agents' seat.
---

# Trajectory Hygiene: kill or continue

A context window has momentum. Steer an agent one way early and "everything that follows in that same session… will continue following that trajectory. And the only way to clear the trajectory is to clear the context window" ([C11](../../01-CONCEPT-LEDGER.md)). Uncle Bob's contamination parable makes the second half concrete: a coffee conversation polluted by a passer-by's soap-opera chatter — "from that point on all the coffee references have to do with the soap opera… The model doesn't know. It can't differentiate." (C11). Contamination never washes out; correcting a poisoned session in-session adds more tokens inside the poison. The only reset is a fresh context.

This island encodes the standing mid-session decision: **continue** while the trajectory serves the task; **kill-and-respawn** when it stops.

## The lane

This island owns the **mid-session lane only** — the kill-vs-continue call while a context is running.

- The context **ending** — the compaction template and the wake protocol a fresh agent runs — is [`handoff`](../../COMPANION.md#handoff)'s seat. Handoff is user-invoked (`disable-model-invocation`), so no agent can fire it; when this island's verdict is *kill*, tell the human to run `handoff` for the exit ritual.
- **Doc-level economy** — what belongs in an agent doc, pointers, pruning, the two loads — is [`writing-for-agents`](../../COMPANION.md#writing-for-agents)'s seat. This island governs the live window, not the documents loaded into it.

## Continue: a healthy trajectory

Continue while all of these hold (advisory — judged, not measured):

- Output still tracks the task the session was steered onto; corrections land and stick.
- The window holds one task, not an accumulation of finished ones — "when you focus the agents down to a single task, you're keeping the context window under control" (C10).
- Utilization sits inside the smart zone (kill trigger 3 below).

## Kill: the three triggers

Kill-and-respawn when any one fires. All three are **advisory** at v0 — no hook measures utilization or detects contamination today, so this is judged, stated, and logged, never auto-blocked; a later wave can add a utilization probe script. The one **enforced** check in this island's lane is the pack validator gating this file's own structure (`unclebob/scripts/validate-island.py`, exit code).

1. **Contamination.** An off-topic injection, a wrong turn, or a bad early steer now colors output — the soap-opera coffee (C11). Signature: the agent keeps returning to the dead idea after correction. Each correction spends tokens inside the poisoned window; respawn instead.
2. **Topic pivot.** The next task differs from the trajectory this window was steered onto. Between focused tasks the lifecycle is born-do-die: "agents are born, do the task, and die so that the next one comes in with a clean context" (C10). Finish, persist, kill, respawn — a fresh context per task beats re-aiming a warm one.
3. **Past the smart zone.** Recall degrades past roughly 40% context utilization — Dex Horthy's smart-zone/dumb-zone line, named in the ledger under (C3) and grounded in [`lost-in-the-middle`](../../research/lost-in-the-middle.md) (U-shaped attention, NoLiMa, context-rot). The ~40% figure is a practitioner threshold, advisory by nature: the point to start planning an exit, not a cliff.

## Cost honesty

Respawning is not free: "startup times are high… 10, 15 seconds to even start up… then it's got to figure out its whole context all over again" (C10). The trade is a flat startup cost against every future token generated on a poisoned trajectory. When a trigger genuinely fires, respawn wins; when none fires, the startup cost is pure waste — that is why the triggers, not habit, decide.

## The respawn ledger: what survives, what dies

- **Survives** (anything on disk): files, commits, test results, artifacts, evidence packets, the handoff file, the repo tree itself.
- **Dies** (anything only in the window): the conversation, in-flight reasoning, unwritten conclusions — and the contamination, which is the point.

Before killing, move every survivor across the line: write unwritten conclusions to a file, commit or stash working code, capture evidence. The full exit ritual lives with `handoff` (user-invoked — the human runs it).

## The checkpoint loop

Run at every natural pause — a task completes, a gate goes green, a new task arrives:

1. **Check** the three triggers against the live session.
2. **Decide** — continue or kill; name the trigger when killing.
3. **On kill** — persist survivors to disk, tell the human to run `handoff`, respawn.
4. **Re-verify** — the fresh context orients from the tree (files, commits, the handoff), never from memory of the dead session; a fresh agent quoting the old session is reading a stale summary — send it back to the tree.

Done when: the check ran at the pause, the decision is named with its trigger, and (on kill) every survivor is on disk before the window closes. If re-verify finds a survivor missing, the kill was premature: recover it from the dead session while it is still open, or re-derive it in the fresh one — then re-verify.

**No authority without evidence. Contamination never washes out — kill the context, keep the survivors, respawn fresh.**
