---
name: structure-interrogation
description: Extract the agent's own model of the structure it actually built - what the modules are, how each interrelates with the others, how they talk - then correct that model against the structure you intended. Reach for it after agents have built or grown a codebase and nobody has checked what shape it really took, or when the user says "interrogate the structure", "ask the agents what they built", or "what are the modules here, really". Differentiator - arch-survey mines change-history for refactor candidates; this island interrogates the agent's mental model, and the re-partition design stays human-held.
---

# Structure Interrogation: ask the agents what they built

Agents grow structure faster than anyone inspects it. This island asks them what they built. You interrogate the agents instead of reading the code, so what comes back is the agent's own model of the structure. The gap between that model and the structure you intended is the finding. The island ends where Bob ends: a human designs the new module structure and hands it back as an implementation plan. The ground (C12): *"I'd interrogate the agents. What's the structure here? How does this module interrelate with that module?… and then I would get scared to death because the answers were horribly frightening. And then I would design a module structure… and give them an implementation plan."*

## Where this sits — the boundaries

- [`arch-survey`](../../COMPANION.md#arch-survey) owns the change-history scan. It mines churn hot-spots for refactor candidates and ranks them. This island never reads history at all. It extracts the agent's own model of the structure, then corrects that model.
- [`arch-lens`](../arch-lens/SKILL.md) is the viewer instrument, the drill-down structure diagram. The lens shows what the code *is*; the interrogation shows what the agent *thinks* it is. Where you have both, cross-check one against the other, and put any mismatch on the gap list below.
- Fencing the corrected partition mechanically (a direction-spec agents cannot violate) is [`dependency-fence`](../dependency-fence/SKILL.md)'s seat. This island stops at the handed-back plan.

## 1. Interrogate

Ask the agents that built the codebase, or that work it now, each in its own session. Write every question and every answer down verbatim in a dated record, `ops/interrogations/YYYY-MM-DD-structure.md`. Those answers are the evidence the rest of the island runs on. The battery, straight from the concern:

- What are the modules of this system? Name them.
- How does this module interrelate with that module?
- How do they talk — what actually crosses each boundary (calls, types, events, shared state)?
- Which module owns this concept? What breaks elsewhere if that module's interface changes?

Push each answer down to specifics: named files, named call sites. Keep pushing until it survives or breaks. An answer that reassures you at every turn usually means the interrogation was shallow, not that the structure is clean. A second agent with fresh context, interrogated alongside the builders, is a cheap cross-check. Where the builder and the fresh reader describe the same boundary differently, that disagreement goes on the gap list. Both moves are advisory; your judgment ends the probing.

## 2. Expect to be scared — the gap is the finding

Read the answers as evidence, not as reassurance. Fear is the expected output of a working interrogation: *"the answers were horribly frightening"* (C12). A frightening answer means the instrument worked, so the session moves to design rather than despair. Now write the gap list. Each entry pairs the agent's claim, quoted from the record, with what you intended or with what the code demonstrably does. An empty gap list is a valid result. Report it plainly and stop, rather than manufacturing gaps to justify a re-partition.

## 3. The human designs the re-partition — the manual step is the point

Re-partitioning is strategic work, and agents are *"really good at tactical, really bad at strategic"* (C25). It is the general's decision, not the sergeant's. So the human designs the new module structure: which modules exist, what each one owns, how the dependencies flow. Then convert that decision into the form agents execute well. Break it into an ordered implementation plan of small tactical steps (C12, *"give them an implementation plan"*) and hand it back to the agents.

Honest status: this step is human-held today by evidence, not by preference. Bob's own attempts to automate it are failing (*"I'm working now to see if I can automate that and I'm having not a lot of luck,"* C12). If an agent drafts a candidate partition, record the seats as they were: design = agent, review = human, per the named-seats rule in [`CONTEXT.md`](../../CONTEXT.md). A plan whose design seat is an agent is a reviewed draft, and its record says so.

## Done — and the reverify loop

The interrogation doubles as the acceptance check. Done when:

1. The interrogation record exists: dated, verbatim Q&A, one file per session.
2. The gap list exists, every entry quoting the agent's claim from the record.
3. The re-partition plan exists, names its design seat, and has been handed back as ordered implementation steps.
4. Reverify: after the agents implement the plan, run the same battery on a fresh-context agent. The loop closes when the fresh answers describe the intended partition. Until they do, the re-partition stays `unverified`. The loop: interrogate → design → implement → re-interrogate.

## Evidence discipline

Every rule above is `advisory` at v0. No hook or script blocks any step, the record and the gap list are captured by hand, and reading them is your judgment. One `enforced` check exists today: the pack validator (`scripts/validate-island.py`), and it gates this island's own structure. Nothing yet checks an interrogation mechanically. A later wave could make step 4 partly enforced by diffing the agent's claimed dependency edges against a computed import graph. Until that script exists and has gone red on a known-bad fixture, the reverify verdict is advisory and says so.

**The agent describes the structure; the human designs it. Interrogate, expect fear, hand back the plan.**
