---
name: no-silver-bullet-triage
description: Routes each work item by Brooks's 1986 split - accidental complexity, the difficulty our tools impose, goes to agents at full speed, while essential complexity, the difficulty of the thing itself, gets a recorded human decision before any agent touches it. Reach for it when handing a backlog to agents, when an agent has just decided something nobody chose, or on "can the agent take this one", "essential vs accidental complexity", "what has to stay human", "no silver bullet". Differentiator - this island owns the classification and the routing only, so whether the thing should exist at all, who owns the design, and what a human reads afterwards are three neighbouring seats, each named below.
---

# No Silver Bullet Triage: hand over the mechanism, keep the meaning

Brooks split software difficulty in two in 1986. **Accidental** complexity is what our representations and tools impose — the difficulty of *expressing* the thing. **Essential** complexity is the difficulty of the thing itself. His bound follows from the split: no single technique yields an order of magnitude within a decade, because a large part of the difficulty was never the tool's to remove ([`seventies-canon.md`](../../research/seventies-canon.md)).

That bound is not a prediction that nothing improves. It is a prediction about **where** improvement stops — and it lands exactly on the seam this pack was built around. The conversation names the same seam in different vocabulary: *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* (C25, quoted via [the ledger](../../01-CONCEPT-LEDGER.md); every conversation quotation on this page reaches it that way, never from memory).

This island owns one job: **classify each item essential or accidental, and route it accordingly.** Nothing else.

## Why the router matters more now, not less

Agents are a large win on the accidental side. The conversation's own **observed** margin for the full gated pipeline is *"a factor of two or three or four"* (C5) — the figure Bob reports in the interview, not a captured run — and it was bought squarely on the code-writing side of the seam — *"They are fast with code. I am slow with code. So I'm going to let them have the code and I'm going to deal with the stuff around that to make sure it's all okay"* (C1).

Now do the arithmetic that follows. If the accidental half compresses several-fold and the essential half does not move, the **share** of remaining work that is essential rises. That is arithmetic given the premise, not a measurement — but the premise has direct support inside the conversation, from someone actively trying to falsify it: Bob's attempt to automate the module-design step is *"having not a lot of luck"* (C12), and his read on the manual organizing pass is *"We may never escape that manual organizing step at the end"* (C20). Both attempts at automating the strategic step are his own, and both are still open.

So the better the agents get, the more of what is left is the part that decides what the system **means** — and the more expensive it is to have no router. C28 is the same law at a different rung: *"the fundamentals are the way of organizing that complexity into a form that can be conceived not just by humans, but by our models as well"* (C28, whose companion line — *"software is the most complicated thing that humans have ever attempted"* — the ledger flags as attributed by Bob to Dijkstra and `unverified` as a verbatim Dijkstra quote).

*(The reading that agents shrink the accidental half specifically is the research brief's 2026 assessment, not a 1986 claim — Brooks wrote nothing about agents ([`seventies-canon.md`](../../research/seventies-canon.md)).)*

## The classification

Two questions, asked of the item and not of the person doing it.

| ask | if yes | why the test works |
|---|---|---|
| **The perfect-tool test.** If your language, framework, build system and runtime were replaced by ideal ones tomorrow, does this item vanish? | `accidental` | tool-imposed difficulty is the only kind a better tool can delete |
| **The outside-the-code test.** Does answering this require something no reading of the repo can supply — a domain rule, a promise made to someone, a choice between two defensible answers? | `essential` | meaning is not derivable from mechanism, so no amount of code-reading produces it |

The tie-breaker, when both tests fire weakly: **accidental work has a right answer the repo already implies; essential work has a chosen answer that someone must be able to be wrong about.** If nobody could be wrong, it was not a decision.

Worked examples, deliberately including the uncomfortable ones:

- Serialization glue, build config, retry plumbing, test scaffolding, a rename pass, mechanically inverting a dependency — `accidental`. Each exists because a tool requires it, not because the problem does.
- What *settled* means for an order; whether a partial refund reopens a dispute window; which of two services is allowed to know a customer's identity; what the system does when the two sources of truth disagree — `essential`. No tool improvement deletes those questions; they are the product.
- **How** a seam is cut is mechanism. **That** there is a seam between billing and identity, and what each side may know, is meaning. The same refactor can be both, which is the next section.

## Mixed items are split, not tagged

Most misroutes are not misjudgements — they are mixed items handed over whole. A ticket reading `add a retry to the payment call` (this island's example, not a transcript line) is accidental mechanics wrapped around an essential question: is this call idempotent, and is a double charge acceptable? Ship it whole and the agent answers the essential half silently, in code, and correctly-looking.

So: **a mixed item becomes two items — the decision, then the mechanism** — never one item with a fractional tag. This is the same split-don't-fraction rule [`strategic-ledger`](../strategic-ledger/SKILL.md) applies to its rows, borrowed here for a different axis and for the same reason: a fractional tag is unfalsifiable, and the routing's whole value is that each item can be argued with.

An agent's own classification of an item is a hypothesis, never authority: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18). Ask for it; a human decides the tag.

## Where each kind goes

**`accidental` → agents, at full speed, and no human writes it by hand — except where the fleet is barred from the action, or the prompt costs more than the keystroke.** Record which of the two it was, with the reason: that exception list is exactly where the C5 margin leaks back out, so it should stay short enough to read. This is the whole point of the gate stack — the CRAP ceiling, the mutation pass, the dependency fence exist so accidental work can be handed over and still land clean. A human who takes it back to write or hand-walk spends the margin the gates just earned, and lands back in *"it's interesting because it's fast, but it's frustrating because it makes me slow"* (C1). The goal remains *"I don't have to look at the code at all"* (C1). How much of the resulting diff a human still reads is set by **blast radius, not by this tag** — that ladder is [`acceptance-surface-review`](../acceptance-surface-review/SKILL.md)'s, and on its `critical` tier a named code path is read even when the work was purely accidental.

**`essential` → a written human decision, dated before the agent starts.** Five fields, kept short because it is also read by a human, and humans do not read what agents write (C24):

1. **The question**, phrased so it could have been answered differently.
2. **The options** — at least two, each defensible by someone reasonable.
3. **The choice, and the name of the human who made it.** A role is not a name; an agent is not a human.
4. **Why the alternatives lose** — the part no repo read supplies.
5. **What would reverse it** — an observation that, if seen, makes this the wrong call.

Field 5 is the falsifiability hook and the one most often skipped. A decision nothing could overturn is a preference with a date on it. Field 3 is the one that makes the record worth keeping when the choice turns out badly a year later — *"The rules you throw away are the ones you're going to pick up off the floor in a year and dust off and remember why you need them"* (C28).

The record then becomes agent input: agents read everything they are sent (C24), so the coder seat starts from the decision instead of improvising one.

## The three failure modes

- **Essential work routed to an agent.** The agent answers, confidently and plausibly, and the system acquires a meaning nobody chose. This is the expensive one precisely because it looks like progress — there is no red gate, no failing test, just a commit that decided something.
- **Accidental work routed to a human.** Hand-writing boilerplate, arguing file layout, tuning a retry by hand. Feels like diligence, is the C1 loss, and spends the productivity margin C5 makes the accounting unit — the margin whose floor is human speed, at which *"you've lost the game"* (C5).
- **A mixed item routed whole.** The dominant one in practice, and the reason the split rule above exists.

## Where this island sits

- **Whether the thing should be built or automated at all** is [`job-to-be-done`](../../COMPANION.md#job-to-be-done)'s seat — the one-shot pre-build triage. This router opens *after* that verdict and only sorts work already sanctioned; it never argues an item out of existence.
- **Who owns the design, and whose signature counts,** is [`conceptual-integrity-owner`](../conceptual-integrity-owner/SKILL.md)'s — Brooks's one-mind-owns-the-design rule and its sign-off protocol ([`seventies-canon.md`](../../research/seventies-canon.md)). This island decides *which* items need a human decision; that island names the human. The two records do not stack: its sign-off covers **design** changes (shape changes, which by its reversion test leave observable behaviour identical), while most essential items here change behaviour — a refund-window rule takes a decision record and no sign-off. Where an essential item *is* a design change the two coincide, and one record serves: its sign-off, whose `owner`, `decision` and `rejected` fields already carry what fields 2 to 4 above ask for. Write one, not two.
- **How the decision is extracted from a human** is [`grill`](../../COMPANION.md#grill)'s seat — it owns eliciting decisions from a human, and emits the settled ones as ADRs. This island names *which* items require a decision before agents may proceed; it runs no interview. Where grill ran the interview, its ADR *is* the record: the five fields above are what that ADR must carry for an essential item, not a second document. Write one, not two.
- **What a human reads once the agents have written the code** is [`acceptance-surface-review`](../acceptance-surface-review/SKILL.md)'s. Decide before, read after: this island governs the before.
- **Not the same axis as [`strategic-ledger`](../strategic-ledger/SKILL.md).** That ledger splits behaviour from shape and prices minutes per cycle; this router splits meaning from mechanism and decides who may answer an item. They cross: a dependency-inversion pass is `strategic` there and `accidental` here, while a one-line pricing-rule change is `tactical` there and `essential` here. Two orthogonal tags, not two names for one split.

## Enforced vs advisory

**Every rule on this island is `advisory`, and it ships no script by design.** Classification is judgment: no tool reads intent, and the item that most needs catching — an essential question nested inside an accidental ticket — is exactly the one a parser cannot see. The evidence for that limit is in the source rather than in a shrug: the two automation attempts recorded in C12 and C20 are Bob's own, and neither has landed.

A checker *could* verify the **form** of a decision record — five fields present, a name in field 3, a date before the first commit — and that would be honest form-checking. This island does not ship one, because a green form check next to an unchecked routing invites the reading that the routing was verified. Under the pack's first law ([`CONTEXT.md`](../../CONTEXT.md)) that reading would be laundering, so the sentence stays narrow: nothing here is enforced.

The only **enforced** check touching this island is the pack validator (`../../scripts/validate-island.py`), which gates this file's own shape — frontmatter, ledger citation, body size — and says nothing whatsoever about whether your routing is right. The imperatives above are doctrine, not checks.

## Done when

- [ ] Every item in the batch carries exactly one tag, `essential` or `accidental`, set by a human.
- [ ] Mixed items were split into a decision item and a mechanism item, not tagged fractionally.
- [ ] Every `accidental` item went to an agent, or carries a recorded reason it could not; how much of any diff anyone reads was set by blast radius, not by this tag.
- [ ] Every `essential` item has a decision record carrying all five fields, dated before its agent ran.
- [ ] Field 5 on each record names something that could actually be observed, not a restatement of the choice.
- [ ] Any tag an agent proposed was re-decided by a named human before routing (C18).

**No authority without evidence, and no meaning without a name — agents take the difficulty our tools imposed, a human takes the difficulty that decides what the system is.**
