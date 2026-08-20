---
name: structure-interrogation
description: Extract the agent's own model of the structure it actually built - what the modules are, how each interrelates with the others, how they talk - then correct that model against the structure you intended. Reach for it after agents have built or grown a codebase and nobody has checked what shape it really took, or when the user says "interrogate the structure", "ask the agents what they built", or "what are the modules here, really". Differentiator - arch-survey mines change-history for refactor candidates; this island interrogates the agent's mental model, and the re-partition design stays human-held.
---

# Structure Interrogation: ask the agents what they built

Agents grow structure faster than anyone inspects it. This island extracts the **agent's own model** of that structure — by interrogation, not by reading the code — treats the gap between that model and your intent as the finding, and ends with a **human-designed re-partition** handed back as an implementation plan. The ground (C12): *"I'd interrogate the agents. What's the structure here? How does this module interrelate with that module?… and then I would get scared to death because the answers were horribly frightening. And then I would design a module structure… and give them an implementation plan."*

## Where this sits — the boundaries

- [`arch-survey`](../../COMPANION.md#arch-survey) owns the change-history scan: it mines churn hot-spots for refactor candidates and ranks them. This island never touches history; it extracts the **agent's own model** of the structure and corrects it.
- [`arch-lens`](../arch-lens/SKILL.md) is the viewer instrument — the drill-down structure diagram. The lens shows what the code *is*; the interrogation reveals what the agent *thinks* it is. When both exist, cross-check one against the other; a mismatch belongs on the gap list below.
- Mechanically fencing the corrected partition (a direction-spec agents cannot violate) is [`dependency-fence`](../dependency-fence/SKILL.md)'s seat; this island ends at the handed-back plan.

## 1. Interrogate

Ask the agents that built or now work the codebase, in their own sessions. Capture every question and answer **verbatim** into a dated record — `ops/interrogations/YYYY-MM-DD-structure.md` — because the answers are the evidence the rest of the island runs on. The battery, straight from the concern:

- What are the modules of this system? Name them.
- How does this module interrelate with that module?
- How do they talk — what actually crosses each boundary (calls, types, events, shared state)?
- Which module owns this concept? What breaks elsewhere if that module's interface changes?

Push each answer to specifics — named files, named call sites — until it either survives or breaks; a uniformly reassuring answer usually signals a shallow interrogation rather than a clean structure. Interrogating a second, fresh-context agent alongside the builders is a cheap cross-check: where builder and fresh reader disagree about the same boundary, the disagreement itself goes on the gap list. Both moves are advisory — your judgment ends the probing.

## 2. Expect to be scared — the gap is the finding

Read the answers as evidence, not reassurance. Fear is the expected output of a working interrogation — *"the answers were horribly frightening"* (C12) — so a scary answer means the instrument worked, and the session moves to design, not despair. Write the **gap list**: each entry pairs the agent's claim (quoted from the record) with what you intended or what the code demonstrably does. An empty gap list is a valid result; report it plainly and stop, rather than manufacturing gaps to justify a re-partition.

## 3. The human designs the re-partition — the manual step is the point

Re-partitioning is strategic work, and agents are *"really good at tactical, really bad at strategic"* (C25) — the general's decision, not the sergeant's. So the **human** designs the new module structure: which modules exist, what each owns, how the dependencies flow. Then convert that strategic decision into the form agents execute well: an ordered implementation plan of small tactical steps (C12 — *"give them an implementation plan"*), handed back to the agents.

Honest status: this step is **human-held today** by evidence, not preference — Bob's own automation attempts are failing (*"I'm working now to see if I can automate that and I'm having not a lot of luck,"* C12). If an agent drafts a candidate partition, record the seats as they were: design = agent, review = human — per the named-seats rule in [`CONTEXT.md`](../../CONTEXT.md). A plan whose design seat is an agent is a reviewed draft, and its record says so.

## Done — and the reverify loop

The interrogation doubles as the acceptance check. Done when:

1. The interrogation record exists: dated, verbatim Q&A, one file per session.
2. The gap list exists, every entry quoting the agent's claim from the record.
3. The re-partition plan exists, names its design seat, and has been handed back as ordered implementation steps.
4. **Reverify:** after the agents implement the plan, run the same battery on a fresh-context agent. The loop closes when the fresh answers describe the intended partition; until then the re-partition stays `unverified`. Loop: interrogate → design → implement → re-interrogate.

## Evidence discipline

Every rule above is **advisory** at v0: no hook or script blocks any step, the record and gap list are captured by hand, and reading them is your judgment. The only **enforced** check that exists today is the pack validator (`unclebob/scripts/validate-island.py`) gating this island's own structure — nothing yet mechanically checks an interrogation. A later wave can make step 4 partially enforced by diffing the agent's claimed dependency edges against a computed import graph; until that script exists and has gone red on a known-bad fixture, the reverify verdict is advisory and says so.

**The agent describes the structure; the human designs it — interrogate, expect fear, hand back the plan.**
