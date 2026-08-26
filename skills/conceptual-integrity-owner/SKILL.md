---
name: conceptual-integrity-owner
description: Names the one human mind that owns a system's design and holds that no merged design change is legitimate without that owner's recorded sign-off - the strategic seat agents do not fill, because they are strong tactically and weak strategically. Reach for it when a design decision is about to land unowned, when the answer to "who decided this" is a committee or an agent poll, or on "who owns this design", "conceptual integrity", "do we need an architect anymore", "add another agent to figure out the structure". Differentiator - this island owns WHO holds the design and what their sign-off covers; the head-bound verdict ceremony belongs to the Forge, the human reading surface to acceptance-surface-review, and essential-versus-accidental routing to no-silver-bullet-triage.
---

# Conceptual Integrity Owner: one mind holds the design

**Conceptual integrity comes from one mind.** Not from a committee, not from headcount, not from the average of several good opinions. This pack's canon brief names *The Mythical Man-Month* (1975) as the source of the three ideas used here: conceptual integrity, Brooks's law, and the surgical team. It records conceptual integrity as *"one mind owning the design"* and as *"precisely the strategic role Bob says humans must keep"* ([`seventies-canon.md`](../../research/seventies-canon.md)). This page is written from that brief and from the concept ledger, and **no line on it is a verbatim Brooks quote.** Ranking conceptual integrity against the other considerations in system design would go past what the brief carries, so this page does not rank it.

The agent era does not retire that seat. It leaves the seat as the main thing a human still does. The source splits the labour bluntly: *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* (C25). And the one step Bob reports trying to automate, and failing at, is the design step itself. After interrogating the agents about the structure, *"I would design a module structure… and give them an implementation plan"* (C12). He calls the attempt a live failure: *"I'm working now to see if I can automate that and I'm having not a lot of luck"* (C12).

So this island encodes a **seat**, not a process: who holds the design, and what their sign-off covers. Conversation quotes reach this page only through the [concept ledger](../../docs/01-CONCEPT-LEDGER.md); phrases quoted from the canon brief are cited to it where they appear.

> Read every "no" and "never" below as a rule this island *states*, not as a check it *runs*. **This island ships no script, and nothing in the rule below is machine-checked.** See [Enforced vs advisory](#enforced-vs-advisory).

## The seat

- **One named human, per system.** A person's name, not a role title, not a rota, not "the platform team", not "whoever reviews it". If the answer to *who owns this design* takes more than one name, the system has no owner yet — it has a queue.
- **The owner holds meaning, not throughput.** What the system is for, what its parts are, where the boundaries fall, which words the codebase uses for its load-bearing ideas, and which proposals blur those ideas. Delivery speed, staffing and scheduling sit in somebody else's seat, and somebody else can hold them without splitting the design.
- **Declared before it is needed.** An owner appointed during the argument is an arbitrator, not an owner. The seat is named at the point the system gets a name.
- **Handover is an event.** An owner can change; the design cannot change owners silently. A handover is dated, records what the incoming owner now holds, and is signed by both. Alternating owners week to week is not one mind. It is a committee with a slower clock.
- **One system, one owner. One owner may hold several systems.** The rule bounds minds per design, not designs per mind.

## What counts as a design change

The sign-off rule is only usable if "design change" is enumerable. A change is a **design** change when it alters the shape of the system rather than its behaviour. That is the reversion test from [`strategic-ledger`](../strategic-ledger/SKILL.md), unchanged: revert it, and observable behaviour is identical.

| Change | Why it is the owner's |
|---|---|
| a module created, deleted, merged, or split | the partition is the design |
| a dependency added or inverted across a boundary | direction is meaning; the fence only enforces the direction already chosen |
| a public interface or contract changed | what callers may assume |
| a load-bearing name changed | the vocabulary the whole codebase reasons in |
| the error model changed | what the system promises when it fails |
| a data shape that outlives the process: schema, wire format, stored file | the hardest thing to take back |
| a decision implemented a second time, in a second place | one meaning, two spellings: the drift [`leak-scan`](../leak-scan/SKILL.md) detects |
| a framework or runtime dependency adopted | it imports somebody else's design into yours |

Everything not on that list ships without the owner, once you have adapted the list to this system (**Done when**, item 2). That half of the rule carries as much weight as the other half. An owner asked to sign every merge becomes a bottleneck, then a rubber stamp, then nothing.

## The sign-off record

A recorded sign-off, one per design change, containing at minimum:

| field | must contain |
|---|---|
| `owner` | the human's name |
| `decision` | what the shape now is, in the owner's own words, one paragraph |
| `rejected` | at least one alternative shape considered and refused, with the reason |
| `scope` | the modules or boundaries the decision governs |
| `date` | when it was taken |

The `rejected` field is the load-bearing one. A decision with no refused alternative is a description of what the agents happened to build, arriving after the fact and dressed as a choice.

**Where a sign-off must also bind to an exact head and void when that head moves, that is the ceremony's rule, not this island's.** Who may review, what a verdict binds, and when it voids belong to [`cross-family-review`](../../COMPANION.md#cross-family-review). Invoke it. Do not restate the verdict format, the void-on-move rule, or the author-never-reviews law here. The two artifacts are different animals. A verdict says *this diff at this SHA passed review*; a sign-off says *this is what the system now means, and I chose it*. A design record outlives the story that occasioned it: plan documents mulch on merge ([`spec-mulch`](../spec-mulch/SKILL.md)), and the trace of who decided does not.

## Adding agents is not holding the design

The seat empties quietly in three ways, and all three feel like progress:

1. **Consensus laundering.** Three agents were asked and agreed, so the question is settled. It is not: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18). The owner should poll them, then treat the answer as a hypothesis to argue with, never as the decision. Agents polled inside one family are at best one opinion asked several times, and that reading is this pack's position, not something the ledger settles. Across families, C18's distrust still bites, because what it doubts is the debate, not the roster. Where a cross-family verdict *does* bind, it binds under the ceremony's rule and the ceremony's conditions ([`cross-family-review`](../../COMPANION.md#cross-family-review)): a review verdict on a diff, never a substitute for the sign-off above.
2. **Headcount substitution.** The design is unowned, so a design agent gets added, then two more. Adding agents to a late project adds coordination surface rather than progress: Brooks's law, generalized to fleets ([`seventies-canon.md`](../../research/seventies-canon.md)). It adds no integrity, because integrity is a property of how many minds hold the design rather than of how many hands execute it. That last inference is this pack's reading of the brief's one-mind formulation, not a line in it. The fleet-sizing arithmetic behind the coordination half is [`mythical-agent-month`](../mythical-agent-month/SKILL.md)'s seat (Wave 3, alongside this island). This island states only the consequence: **agent count never substitutes for the owner.**
3. **Delegating the strategic half.** The tactical work gets delegated, correctly, and the strategic work rides along with it because nobody separated the two. Separating them is a routing question, and it belongs to the sibling [`no-silver-bullet-triage`](../no-silver-bullet-triage/SKILL.md): essential complexity (deciding what the system means) against accidental complexity (everything else). This island does not route work. It names who signs once the routing says a decision is essential.

## The surgical team as the org chart

Brooks's surgical team is the shape this seat lives inside: **one surgeon cuts; everyone else multiplies that one mind's output** rather than adding minds to the design. The brief calls it "the human-plus-agents org chart, fifty years early" ([`seventies-canon.md`](../../research/seventies-canon.md)): one owner holding the design, many fast tactical hands executing it, and support that exists to keep the surgeon cutting. The brief names the team without listing its roles, so mapping role onto agent seat one by one would run past this pack's evidence. The shape is what ports.

What the shape buys in the agent era is what it bought Brooks. Output scales with the hands to the extent the work partitions, and pricing the coordination surface that bounds that is [`mythical-agent-month`](../mythical-agent-month/SKILL.md)'s job, not this one's. The design does not degrade as hands are added, because the number of minds holding it stayed at one. Every relay seat in [`seat-relay`](../seat-relay/SKILL.md) is a force multiplier under this definition: born, working, dying, never owning.

## Where this island sits

- **The verdict ceremony** (who may review, what a verdict binds, when it voids) is [`cross-family-review`](../../COMPANION.md#cross-family-review)'s. Invoked here, never redefined.
- **What surface a human reads** (the acceptance spec, the QA procedure, and when a code path enters the reading) is [`acceptance-surface-review`](../acceptance-surface-review/SKILL.md)'s. This island says who signs; that island says what they read before signing.
- **Routing work by essential against accidental complexity** is [`no-silver-bullet-triage`](../no-silver-bullet-triage/SKILL.md)'s. It decides which items need a human decision; this island names the human. **The two records do not stack.** Most essential items there change behaviour and take that island's decision record alone. Where an essential item *is* a design change, the two coincide and one sign-off does both jobs: its `owner`, `decision` and `rejected` fields already carry what that island's fields 2 to 4 ask for, and the *at minimum* in the schema above leaves room for its fields 1 and 5 — the question as it could have been answered otherwise, and what would reverse the call. Write one, not two. That island's page states the same rule.
- **Eliciting the decision from the human** is [`grill`](../../COMPANION.md#grill)'s seat: it owns the interview and emits settled decisions as ADRs. This island runs no interview. Where grill ran one, its ADR carries the five fields above and *is* the sign-off. Write one, not two.
- **How much effort goes into shape at all** is [`strategic-ledger`](../strategic-ledger/SKILL.md)'s: it books the tactical/strategic split (C25) in minutes. This island says who decides the shape those minutes buy.
- **The instruments the owner rules on** are the structure islands'. [`structure-interrogation`](../structure-interrogation/SKILL.md) extracts what the agents think they built (C12), [`arch-lens`](../arch-lens/SKILL.md) renders it, [`dependency-fence`](../dependency-fence/SKILL.md) holds a chosen direction. This island defines none of them; the owner reads all three.
- **Wiring an approval requirement into the repository** (branch protection, code owners, a pre-merge hook) is [`agent-guardrails`](../../COMPANION.md#agent-guardrails)'s plumbing seat. This island supplies only what such a rule would have to require.

## Done when

- [ ] The system names one human owner, recorded where a newcomer finds it without asking.
- [ ] The design-change list above is adapted to this system and written down, so both halves of the rule are checkable by a person.
- [ ] Every merged design change on that list carries a sign-off record with a non-empty `rejected` field.
- [ ] Any agent poll that informed a decision is recorded as input, not as the decision (C18).
- [ ] The last owner handover, if any, is dated and signed by both humans.

## Enforced vs advisory

- `advisory`: **every rule on this page.** No script ships with this island, deliberately. A sign-off is a human judgment about what a system means. A script could check the record's *form* (the fields present, a name where a name belongs, a date before the first commit) and no further, and that check would consent to a pasted line as readily as to a decision. A red/green pair could be built for that form check, and it would prove exactly that much. The violation this island actually cares about — a sign-off nobody decided — leaves no textual signature to catch, so the pair would be necessary and nowhere near sufficient ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)). Shipping no gate is the honest option here; shipping a thin one would be laundering under the pack's first law ([`CONTEXT.md`](../../CONTEXT.md)).
- `advisory`: the doctrinal call that the seat must be **human**. Two pieces of source evidence hold it up, and neither is a proof. First, the tactical/strategic split as the two speakers settled it: agents *"really good at tactical, really bad at strategic"* (C25). Second, the design step named as the one automation attempt going badly (C12). Both come from one conversation, about one practitioner's practice, in one period of tooling. Treat the call as this pack's position, revisable the way any threshold is revisable ([`threshold-port`](../threshold-port/SKILL.md)).
- `enforced`: only this file's own shape. The pack validator (`../../scripts/validate-island.py`) checks it mechanically, exit-code gated. It says nothing whatever about whether your design has an owner.
- If you want mechanical teeth, the honest form is a repository rule requiring a named human's approval on the paths where design lives, wired through [`agent-guardrails`](../../COMPANION.md#agent-guardrails). Even then, what is enforced is that a name approved — never that a mind decided.

**No authority without evidence, and no design without an owner: one named human holds what the system means, signs every change to it, and no number of agents inherits that seat.**
