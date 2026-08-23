---
name: human-subagent
description: Curriculum design for Uncle Bob's education inversion - a junior joining an agent-heavy team is run AS an agent, given the same task briefs and held to the same deterministic gates, spending months deliberately unproductive, until they can be trusted to direct agents of their own. Reach for it when onboarding a junior or a career-changer into an agent fleet, when planning what a new hire actually does for their first six months, or on "how do juniors learn anything now", "what do we do with new grads", "how should I train someone to run agents", "is there still an entry-level path". Differentiator - it designs the drill and its scoring only; the reading list is strategy-shelf, live struggle-spotting is thrash-watch, and the machinery that delivers lessons and remembers them belongs to the Forge.
---

# Human Subagent: run the junior as an agent

The most provocative claim in the conversation is an inversion of who imitates whom. Agents took the tactical seat — *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* (C25, quoted through [the ledger](../../01-CONCEPT-LEDGER.md)). That seat was the entry-level job. It was also the on-ramp almost everyone used: you spent years being the sergeant, and somewhere in there you learned to be the general. Take the sergeant's work away and the on-ramp does not become shorter — it disappears, unless someone builds a replacement on purpose.

Bob's replacement is to hand the junior the agent's job description. At a company, *"the lead engineer… should look at you as an agent and he should give you the same kind of tasks that the agents have and subject you to the same kind of deterministic tools… you should spend several months in that state being horribly unproductive but learning a hell of a lot. And by the time you've gone through that gauntlet, maybe you can be trusted to run an agent of your own"* (C26). Matt Pocock names why the arithmetic now works at all: agents compress strategic feedback loops that used to take nine months, so a bad structural decision becomes visible fast enough to learn from (C26).

> **Naming.** The word inside that quote is Bob's and is preserved as he said it. This pack does not adopt it: `gauntlet` is reserved for the Forge's [`gauntlet-loop`](../../COMPANION.md#gauntlet-loop), which means builder sub-agents fanned out against one falsifiable bar, shadowed by blind critics. That is agents producing artifacts. This is a person being drilled. Two different things, and one word for both would launder the difference. Here the practice is **the drill**, and the months are **the rotation**.

## The ladder beneath it

The drill is the last rung, not the first. Bob's prerequisite is blunt — *"you should be writing code for a year… so that you know what the agents are dealing with"* — and beneath that a descent-then-climb: *"binary all the way through assembly language, some basic code like C, some higher level code like Python… and finally be able to strategically run an agent under supervision"* (C26). The argument for the low rungs is not nostalgia but calibration: *"if all you're doing is writing Java all day long, you live in a fantasy world"* (C26). This island's reading of why the low rungs matter — not a claim C26 makes: a director who has never seen a pointer, a register, or a cache line has *fewer* independent ways to separate an agent's plausible answer from a correct one. The gates still refuse on their own authority, and that refusal needs no knowledge of registers; but everything the gates do not cover arrives as prose that sounds right, and reading that is where the calibration gets spent.

Read the ladder as **entry criteria**, not as a syllabus this island delivers. The rungs are Bob's (C26); the right-hand column is this island's reading of what each one buys, not a claim he made:

| Rung | What it buys the future director |
|---|---|
| A year of writing code | Knowing what the agents are dealing with (C26) |
| Binary, assembly | Calibration — the machine stops being magic |
| A low-level language (C) | Cost intuition: allocation, lifetime, failure |
| A high-level language (Python) | Fluency in the layer the agents actually write |
| The drill | Struggle under gates, supervised (C26) |
| Directing agents | The strategic seat (C25) |

Where the rungs are already climbed, start at the drill. Where they are not, say so out loud rather than running a drill that measures the wrong gap.

## Designing the drill

Six rules. They are what makes it a drill and not just a hard first quarter.

1. **Same brief, same shape.** The trainee receives the mandate an agent would receive, in the same format — objective and definition of done, context pack, decision rights, stop conditions, evidence contract. That format is [`delegated-authority-prompt`](../../COMPANION.md#delegated-authority-prompt)'s; do not invent a gentler one for the human, because the brief's gaps are half of what there is to learn.
2. **Same gates, unrelaxed, and say which lane you ran.** The trainee finishes when the tool consents, not when a human says it looks fine — a gate is a loop nobody exits until the checker says okay (C4). Run the *same* gate stack the trainee will later direct ([`crap-gate`](../crap-gate/SKILL.md), [`mutant-hunt`](../mutant-hunt/SKILL.md), [`dependency-fence`](../dependency-fence/SKILL.md)). One honest tension: C17 makes a threshold a property of the executor, not of the value — the agent lane sits looser than the human lane for reasons that are about the agent's memory, not the trainee's comfort. Pick one lane, name it in the brief, and never retune it mid-rotation; a moving number teaches nothing.
3. **No rescue channel.** No hint-dropping over the shoulder, no pair-programming the trainee out of the hole, no reviewer quietly fixing the diff. Every one of those is kindness that removes the struggle, and the struggle is the entire curriculum.
4. **Fresh brief per task, not a rolling epic.** One task, one brief, one verdict — the born-do-die shape the agents run on (C10) — so failure lands on a task boundary where it can be examined instead of smearing across a quarter.
5. **The rotation is time-boxed and disclosed.** Bob's own words for the period are *"horribly unproductive"* (C26). Tell the trainee that before it starts, put an end date on it, and write both into the brief. Undisclosed, months of low output stop being a curriculum and become a performance problem — the trainee's, unfairly.
6. **Book it outside the margin ledger.** [`margin-ledger`](../margin-ledger/SKILL.md) exists to cut any gate that drags throughput below a human baseline (C5). A trainee under gates is *designed* to sit below that line. Log the rotation as training cost, explicitly, or the ledger will read a curriculum as a failing gate and correctly recommend cutting it.

## Scoring — two boards, and only one of them is a number

**Board 1 — the gate tally (bookkeeping over enforced tools).** Per task, record: which gate refused, how many fix-until-green cycles before it consented, and whether the trainee could state *why* it refused from the tool's output alone. The gates themselves are enforced by their own islands; this tally is not a gate and grants nothing. Its only job is to show the shape of the trainee's cycles over weeks — a falling cycle count on unchanged difficulty is progress; a flat one is a signal to look at the brief before blaming the trainee.

**Board 2 — the recognition board (the graduation criterion).** Four behaviours, each scored `observed` or `not yet`, each stamped with the date and the task it was observed on:

- **R1** — Names a thrash signature in a running agent *before* being told, using the vocabulary of [`thrash-watch`](../thrash-watch/SKILL.md).
- **R2** — Explains a refusal from the gate's own output, without a human translating it.
- **R3** — Chooses stop-and-repartition over one-more-fix at least once, and defends the choice afterward.
- **R4** — Re-derives a claimed verdict instead of accepting it — the first law, exercised on a colleague's assertion.

Two anti-laundering rules on this board. `not yet` never softens into "observed weakly"; and a behaviour is observed on a task, never in a conversation about a task. Graduation is `observed` on all four — which is to say the trainee has stopped being someone the gates catch and started being someone who reads the gates.

## Why manufactured struggle is the point

The drill is not hazing and it is not a filter. It exists to produce one specific capability, and it is the capability a novice cannot fake. Bob knew his agents were failing in December because he had been there himself: *"the important part was the next step where I watched them thrash. I could see the agent struggle and I recognized the struggle since I have been through that struggle… the novice would come in and not recognize the struggle"* (C27). Recognition is pattern-matching against your own scar tissue. C27 evidences that the novice arrives without it; that no lecture installs it and no document transfers it — this one included — is this island's bet, not his claim, and it is the bet the whole drill is staked on. If the tactical work that used to generate the scars is now done by agents, the scars have to be manufactured deliberately, under supervision, on tasks small enough that the wreckage is legible.

This is also why the strategic seat cannot simply be assigned. Agents shrink accidental complexity; deciding what the system *means* stays human ([seventies-canon](../../research/seventies-canon.md), on Brooks's "No Silver Bullet"). The drill is how someone earns the right to that decision, and its exit criterion is Bob's, unchanged: trusted to run an agent of their own (C26).

## Generalising past code

The drill transfers to any craft that has all three of these. Missing one, you have an ordinary apprenticeship — a good thing, but not this thing, and the scoring above will not fit it.

1. **A brief small enough to hand over whole** — the unit of work fits in one mandate with a definition of done.
2. **A tool that can refuse** — a check that says no on its own authority, so the loop closes without a human verdict (C4). Copy-edit linters, lab protocol validators, and CAD rule checks qualify outright: software says no, and the verdict does not depend on who ran it. A contract-review checklist is executed by a person, so it qualifies only when every hard-fail item is objectively decidable by any reader — the moment one item needs taste, you have "the senior thinks it's good" in a table, which is rule 3's rescue channel wearing a checklist, and it does not qualify.
3. **An expert who can already read the struggle** — someone who has been through it, per C27, and can score board 2 honestly.

## Enforced vs advisory

- `advisory` — **everything this island prescribes.** The six drill rules, both scoreboards, the graduation criterion, and the ladder's entry criteria are judgment work executed by a lead engineer. This island ships **no script**, deliberately: there is no honest mechanical check for "did this person learn to recognise struggle", and wrapping a thin gate around that judgment would be exactly the laundering the first law forbids. Anyone who tells you otherwise is selling a certificate.
- `enforced` — the gates the trainee runs against are enforced by their own islands, with their own thresholds and their own red/green fixtures ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)). The drill borrows that enforcement; it adds none.
- `enforced` — this file's own shape, gated mechanically by the pack validator, which is the only claim on this page a machine checks.

```bash
python3 ../../scripts/validate-island.py ../human-subagent   # exit 0
```

Run from this island's directory. It says this island is well-formed. It says nothing whatever about whether your drill works.

## Boundaries — who owns what

- **Lesson delivery is a Forge concern.** Session state, lesson artifacts, learning records, the feedback loop that puts material in front of a person and remembers what they already did — all of it is owned by the Forge's `teach` island, which is a stateful teaching workspace and is user-invoked (a person runs it; read it in the Forge repo). It is *not* one of the twenty-two boundaries [COMPANION.md](../../COMPANION.md) records, so there is no entry here to link you to — but the concern is still not this island's. This island designs the drill and its scoring and hands delivery there.
- **The reading list is the sibling island.** Which old books, and which two-to-four load-bearing ideas each one carries for an agent-director, is [`strategy-shelf`](../strategy-shelf/SKILL.md)'s concern — C27's cure for the novice. This island says the trainee needs the shelf; it never enumerates it.
- **Recognising thrash live is [`thrash-watch`](../thrash-watch/SKILL.md).** That island owns the signatures and the intervention ladder. Board 2's R1 *tests* for that vocabulary; it does not redefine it.
- **The ladder argument itself** — why the rung below is worth climbing, and the standing rung-below weekend for an incumbent director, is [`abstraction-ladder`](../abstraction-ladder/SKILL.md)'s seat (C26, C28). This island reads the same C26 rungs one direction only: as one-time **entry criteria** for a trainee, scored on the way up.
- **Not a `gauntlet`.** Restated because it matters: [`gauntlet-loop`](../../COMPANION.md#gauntlet-loop) is agents fanned out against one bar with blind critics. This island is one human, one brief at a time, under the same tools. Never reuse the word for the drill.
- **Whether to hire and train at all** is [`job-to-be-done`](../../COMPANION.md#job-to-be-done)'s one-shot triage; this island starts after that answer is yes.

## Done when

- [ ] The trainee's ladder position is stated, and any unclimbed rung is named rather than assumed.
- [ ] The brief uses the agents' mandate format, and the gate lane is named in it.
- [ ] The rotation has a disclosed end date and is booked as training cost outside the margin ledger.
- [ ] Board 1 has a per-task row; Board 2 has four rows, each `observed` with a task and a date, or `not yet`.
- [ ] Graduation was declared on four `observed` marks — never on a report of progress.

**Nobody is handed the general's seat. The sergeant's work is gone, so the struggle has to be built on purpose — and recognising it is the one thing a novice cannot fake.**
