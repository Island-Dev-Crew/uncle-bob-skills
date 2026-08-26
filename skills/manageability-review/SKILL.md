---
name: manageability-review
description: The human-judgment acceptance criterion for agent-written code once generation is free - a reviewer who cannot restate the change's control flow in a fixed number of sentences, from a single reading, bounces it, and the failure is a finding about the code rather than about the reviewer. Reach for it when generated diffs land faster than anyone can follow them, when deciding what a human's read of code has to produce before it counts as a review, or when someone says "it passes every gate but nobody understands it", "restate the control flow", "is this even reviewable", "intellectual manageability". Differentiator - this island owns the restatement test and nothing else; complexity expressed as a number belongs to the CRAP gate, interface-first reading economics to the interface budget, and the verdict ceremony to the Forge.
---

# Manageability Review: if you cannot say what it does, it does not land

Most of this pack spends its effort getting the human out of the code: *"I'm going to work very hard to get it into a situation where I don't have to look at the code at all"* (C1). Where a human still looks, the economics of generation have changed what the look is *for*. When code was expensive, a large diff was itself evidence of work. When code is nearly free, volume is evidence of nothing. The one property a human's read can still accept on is whether a mind can hold the thing. Correctness did not stop mattering; it moved to the gates. Volume is what stopped being evidence.

That property has a name older than any tool in this repo: **intellectual manageability**, Dijkstra's term from The Humble Programmer (EWD340, 1972 Turing lecture), where he named it the limiting resource ([`seventies-canon.md`](../../research/seventies-canon.md)). Bob lands on the same ground in the conversation's last movement: *"the fundamentals are the way of organizing that complexity into a form that can be conceived not just by humans, but by our models as well. Since our models are modeled after humans"* (C28). All quotes reach this page through the [concept ledger](../../docs/01-CONCEPT-LEDGER.md), never from memory.

The ledger requires two honesty notes, and this island keeps them rather than smoothing them over. First, the *"most complicated thing that humans have ever attempted"* line Bob attributes to Dijkstra (C28) is `unverified` as a verbatim Dijkstra quote; EWD340's "intellectual manageability" is the sourced ground. Second, applying that criterion to agent-generated code is the research brief's synthesis and this island's, not a claim Dijkstra made about anything.

## The test

One reviewer, one pass, then the change is closed and answered from memory.

1. **Fix N before reading.** N is the sentence budget for the restatement. Choosing it after the read is choosing it to fit, which is the first and easiest way to make this test measure nothing.
2. **Read the change once.** The whole merge unit: the diff plus the code it lands in, at whatever depth you would normally read it. Not the change's own description of itself (fake mode 4). Then close it.
3. **Restate it from memory**, in at most N sentences, in control-flow terms.
4. **Reopen and check the restatement against the code.** This is the only re-reading the test allows, and it happens after the sentences are written down.
5. **Verdict.** Restatement produced within N and correct → accept on this axis. Not producible without reopening, over budget, or contradicted by the code → **bounce**.

## What counts as a restatement

Four things, or it is not one: **entry** (what is called, with what), **order** (what runs in what sequence), **branches** (each condition that can be taken), **exits** (every way it can end: return, raise, timeout, silent fall-through).

```text
upload(file):
    for attempt in 1..3:
        r = put(file)
        if r.ok:          return r
        if r.status==413: raise TooLarge
        if attempt < 3:   sleep(backoff(attempt))
    raise Exhausted
```

- **Not a restatement.** *"It adds retry with backoff to the uploader."* That is the change's *purpose*. Purpose-restatement is the easiest sentence in the room to write, which is exactly why it is the default cheat. It does not say when retrying stops, and the reviewer who wrote it cannot tell you whether a 413 is retried.
- **A restatement, N=3.** *"`upload` calls `put` once per attempt, up to three attempts. It returns the response on the first `ok`, and on status 413 it raises `TooLarge` immediately with no further attempt. Otherwise it sleeps a backoff computed from the attempt number and retries; after the third failure it raises `Exhausted`."*

**And a sentence has a size.** The unit is one a person would say aloud in a single breath; the three above run 10, 20 and 19 words. Three sentences chained with *and … which … after which …* carry unbounded control flow and satisfy N=3 verbatim, so the chain evades the budget rather than meeting it. A sentence that will not survive being said aloud is more than one sentence, and counts as more than one. That bound is a human judgment like everything else here, and `unverified` as a calibrated limit. It is stated so the count has a unit, not because a breath was measured.

Now wrap that same behavior in an event emitter, a retry decorator, and a policy object across three files. The per-function numbers come out lower, function by function, because dispersing branch logic across small pieces is exactly how a per-function count is reduced. The restatement does not survive the dispersal. **That gap is the gap this island exists in.** It is why the number and the sentence are two different checks, and why neither is evidence for the other.

## The direction rule

A failed restatement is a finding about **the code**. Not about the reviewer's seniority, not about their familiarity with the codebase, not a prompt to "read it again and you'll get it." Inverting that direction is how a codebase becomes unreviewable one accepted diff at a time: each reviewer, told the failure was theirs, quietly stops reporting it.

So the bounce carries a deliverable, and it is the strongest artifact this island produces: **the sentence that could not be written.** Not "too complex" but *"I could not say what happens when the 413 arrives on the third attempt."* That names a seam. The repairs it usually asks for are ordinary: name the thing so the sentence writes itself, collapse an indirection, pull a scattered branch into one place, split the *module* along the seam the missing sentence found. None of them are this island's to enforce. Durable capture of that sentence, enumerated at an exact SHA, provenance-marked, given a collision-free id, is [`finding-register`](../../COMPANION.md#finding-register)'s seat. This island says only what the finding must contain and that it lands against the code.

## How the test gets faked

1. **Re-reading mid-sentence.** Then the test measures transcription, not comprehension. One pass, then closed.
2. **Restating purpose instead of control flow.** The four elements above are the guard; a restatement missing the exits is not short, it is absent.
3. **Floating N.** Fixed before, never after.
4. **Restating the change's own narration.** Agent-written code tends to arrive with agent-written prose: a PR body, a commit message, a docstring, a comment, or a descriptive test name, each of them already narrating entry, order, branches and exits. Read one and the sentences are handed to you before you reason at all. That is fake mode 1 arriving not by hostile input but by the ordinary output of the generators in this pack's scope, on exactly the change class this island was built for. Test names are the sharpest case, because they are the one narration artifact sitting *inside* the read this island permits. `test_413_raises_TooLarge_without_retry` hands over a branch and an exit before the reviewer reasons, and it ships in the diff; this pack elevates that channel on purpose, since [`tests-as-spec`](../tests-as-spec/SKILL.md) opens on C16's *"They read tests to understand what the system does"*. So the line runs through the test rather than around it. The restatement may come from the implementation and from the test *assertions*, which are code, and never from test *names* or their docstrings, which are prose. That generators ordinarily emit such narration is this island's read of them and `advisory`; no ledger entry speaks to what a generator emits by default, and nobody here has surveyed one. The rest of the narration is closed with the code, so the read the restatement comes from is the diff and the implementation, never the change's account of itself. Partial, and stated as partial: a reviewer who read the PR body an hour earlier cannot unread it, and nothing here detects that. What is closeable is the deliberate consult during the pass.
5. **Chaining the budget.** Meeting N by growing the sentences instead of adding them; see the breath bound above. A count whose unit floats is the same cheat as a floating N, moved one level down.
6. **Splitting to pass.** Six diffs each restatable in three sentences, where nobody can restate the six together. The unit is the change **as it will land**, not the convenient slice. This mitigation is partial and stated as partial: nothing here detects a decomposition chosen to defeat the budget.
7. **The author restating their own change.** They are reciting, not reading, and can restate anything. Who may review is [`cross-family-review`](../../COMPANION.md#cross-family-review)'s law, invoked here and never re-defined.
8. **The familiar reader reciting the module.** Fake mode 7's mechanism, reached by someone who is not the author, so the ceremony's authorship rule does not catch it. A reviewer who has read the surrounding module before can produce a passing restatement out of memory of the module rather than out of comprehension of this change. That is the false-accept twin of the direction rule's false-bounce. Partial, and stated as partial: nothing here detects it, and the only mitigation is that the restatement must name the branches and exits *this diff* introduces or moves, not the ones the module already had.

## N, and how to move it

**N = 3 sentences for a single story-sized change is a starting number, `unverified`.** It is calibrated against nothing, and it is stated as a start so nobody mistakes it for a measurement. Move it the pack's way: run the review, capture the outcomes, let the evidence pick the value. Never let an agent vote it up, because *"you can't trust any debate you have with an agent"* (C18). Porting a threshold from the human regime to an agent one is [`threshold-port`](../threshold-port/SKILL.md)'s discipline, and moving N is that move.

Values transfer; thresholds move (C17). The value here, accept only what a mind can hold, is the one that transfers. N is the part that was always going to need retuning.

## Why this is not sentimentality about humans

The mess that defeats the reviewer degrades the fleet too: *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). C17 points the same way. Bob set a threshold deliberately *higher* for agents than he would accept from a human, and talks about raising it further still; the actual numbers are [`crap-gate`](../crap-gate/SKILL.md)'s content and are not restated here. That puts the agent's tolerance above the human's, which makes a human's failed restatement an *early* signal of the thrash to come rather than a late one. That inference is this island's, drawn from C17's direction and marked `advisory`; nobody here has measured the two thresholds against each other.

The reading side of the same coin is C16, where agents *"pay attention to the structure. It can allow them to not read the code beneath them, which is both a danger and an advantage… as long as the code is consistent, you're okay"*. Unrestatable code is code whose structure has stopped predicting its behavior. That is precisely the condition under which skipping the implementation becomes the danger instead of the advantage.

## Where it applies, and what it costs

A human restating every change re-imposes the exact slowness the architecture removed, and the margin is the accounting unit (C5). So this test is applied where code is already in front of a human, at the `critical` tier of [`acceptance-surface-review`](../acceptance-surface-review/SKILL.md), and otherwise as a sampled spot check on generated work (C1). Whether the review time still fits inside the productivity margin is [`margin-ledger`](../margin-ledger/SKILL.md)'s accounting, not a number this island sets.

Named holes, because a limit left unstated is a claim by omission: this test rules on **comprehensibility only**. A perfectly restatable change can be wrong, and correctness lives with the gates and the acceptance surface. It rules on **one reader at one moment**, so a bounce is one reader's finding, not a proof of unmanageability. The accept direction leaks too, and fake mode 8 names how. And it is a **judgment, not a measurement**: two reviewers may split, and this island offers no tiebreak.

## Boundaries

- **Complexity as a number is not mine.** Cyclomatic count, the CRAP score, the thresholds and the formula all belong to [`crap-gate`](../crap-gate/SKILL.md), and this island neither restates the arithmetic nor sets a ceiling. It is the **human-judgment complement**: the number catches what a machine can count, the sentence catches what it cannot. Run both; neither one is the other's evidence.
- **Interface-first reading economics are not mine.** What an agent should load, what an implementation read costs in tokens, and the load ledger belong to [`interface-budget`](../interface-budget/SKILL.md). Here the reading is a fixed single pass by a person and the currency is sentences.
- **The review ceremony is not mine.** Who may review, what a verdict binds, and when it voids on a moved head belong to [`cross-family-review`](../../COMPANION.md#cross-family-review). This island supplies one criterion the reviewer applies; it never defines the verdict format or the seat rules.
- **What lands in front of the human is not mine.** [`acceptance-surface-review`](../acceptance-surface-review/SKILL.md) decides whether code is on the surface at all and how criticality widens it. This island only says what the reading must produce once it happens. That island's Done-means carries a restatement rule of its own, and the two are not duplicates: its test runs on Gherkin *scenarios* and bounces upstream to [`specifier-seat`](../specifier-seat/SKILL.md), whereas the control-flow restatement over code, bouncing as a finding against the code, is this island's.
- **Review posture is not mine.** Hunting defects without attachment, and refusing a bare "looks good", is [`egoless-fleet`](../egoless-fleet/SKILL.md)'s seat. The only posture question owned here is where a failed restatement's finding lands.

## Enforced vs advisory

- `advisory`, and this covers **every review rule on this island.** The test is a human restating control flow from memory. The discipline lives in one person's head between two readings, and this island ships no script to police it. Under this pack's second law as [`values-not-disciplines`](../values-not-disciplines/SKILL.md) states it, a rule that names no measuring tool is advisory by definition. That is the honest label here, rather than a thin gate wrapped around judgment: an unbacked sentence is laundering under the pack's first law ([`CONTEXT.md`](../../CONTEXT.md)).
- `advisory`, and separately `unverified`: the value of N, per the section above.
- `enforced`, and no review rule here is. Two pack tools *touch* this island and both can go red on it. `validate-island.py` gates this file's own shape; `verify-proofs.py` extracts the command below, re-runs it from this island's directory, and compares the annotated exit code. Neither is a rule about your review. The validator earned its red/green the pack's way on the pack-root fixtures — `scripts/fixtures/bad-island` (6 of 12 checks red, exit 1) and `scripts/fixtures/good-island` (12/12, exit 0) — by the ritual recorded in [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md). Run from this island's directory:

```bash
python3 ../../scripts/validate-island.py ../manageability-review   # exit 0
```

The second tool is run as `python3 ../../scripts/verify-proofs.py ../manageability-review` and reports `1 documented commands, 1 with an exit annotation, 0 unannotated, 0 mismatched` at exit 0. It is deliberately **not** written into the block above. `verify-proofs.py` extracts the commands from every `bash` fence and re-runs them, so a block documenting its own verifier makes the tool spawn itself without bound. That was measured here, not assumed: the self-referential block was tried on a throwaway fixture and had to be killed at a 20-second cap.

Both checks say only that the file is well-formed and that its one documented command still reproduces. Neither says anything whatsoever about whether your review obeyed the doctrine. Recompute them rather than trusting this line.

## Done when

- [ ] N was written down before the change was opened.
- [ ] The change was read once and closed before the restatement was written.
- [ ] The restatement names entry, order, branches, and exits — not purpose — and each sentence is one you could say aloud in a breath.
- [ ] The sentences came from the diff and the code: no PR body, no commit message, no control-flow-narrating comment or docstring, and no test *name* or test docstring was consulted during the pass. Test *assertions* are code and stay in bounds.
- [ ] It was checked against the code, and either matched or the mismatch was recorded.
- [ ] On a bounce, the sentence that could not be written travelled back with the change, and the finding was filed against the code — durably, in `finding-register`, when it has to outlive this review.
- [ ] The restater was not the change's author (per the ceremony's law, not this island's), and the restatement named the branches and exits this diff itself introduces or moves.

**No authority without evidence. Generation is free and volume proves nothing — if no one can say, in N sentences, what the change does, the change is the finding.**
