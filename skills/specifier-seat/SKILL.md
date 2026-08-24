---
name: specifier-seat
description: The relay's intake seat - transform ONE settled human intent doc into EXACTLY TWO artifacts, a Gherkin acceptance spec and a human-viewpoint QA procedure, each with a defined contract that the coder seat and qa-script-seat consume. Use at the start of a relay pass, when a story is settled and ready for the gauntlet, or when the user says "specify this story", "write the Gherkin and the QA doc", or "run the specifier". Differentiator - this seat transforms, it never elicits; interviewing the human is grill's seat, and the specifier starts only after understanding is settled.
---

# Specifier Seat: one doc in, two artifacts out

The intake seat of the five-seat relay (C9): *"take a human written document and turn it into a Gherkin and a QA procedure."* This seat is a pure transform. It receives ONE settled human intent doc and emits EXACTLY TWO artifacts: a Gherkin acceptance spec, and a QA procedure written from a human's viewpoint. Then it dies, so the next seat starts on a clean context (C10). Emitting anything beyond that pair (code, plans, extra docs) is scope creep out of the seat.

## Boundaries: who owns what

- Upstream, this seat transforms; it does not elicit. The specifier starts AFTER shared understanding is settled. Reaching that understanding means interviewing the human, and that is [`grill`](../../COMPANION.md#grill)'s seat: grill drills the human and emits the settled decisions, and this seat consumes them. If the intent doc still holds open questions, live alternatives, or a "TBD", bounce it back to the human with each gap named, and stop. Asking the questions yourself is doing grill's job in the wrong seat.
- Downstream, two named consumers. The coder seat takes the Gherkin spec; its job includes writing the unit tests and code *and* getting the Gherkin working (C9). The qa-script-seat takes the QA procedure and turns it into an executable script with a deterministic, binary verdict (C9). Seat names and ownership live in the pack roster ([`02-ROSTER-50.md`](../../02-ROSTER-50.md)). Write each artifact for its consumer, not for the archive: agents read everything they're sent, so completeness beats brevity here (C24).

## The input contract: what "settled" means

One human intent doc per pass: a story, a settled decision record, a feature brief. The bar has two parts. Every behavior the doc names has exactly one decided answer, and the scope fits one relay pass: a story or two, not a milestone. That bar is `advisory`, a judgment call, because no script checks it today. A doc that misses the bar goes back upstream, never forward.

## Artifact 1, the Gherkin acceptance spec

*"Gherkin is given-when-then stuff. A high level acceptance test."* (C9). The grammar is fixed: Given context, When event, Then outcome. Its value is dual-audience, business-readable on top and deterministically bindable underneath. It is a gate, not a steer ([research](../../research/atdd-gherkin-agile.md)).

Contract the coder seat may rely on:

- One `Feature:` block per intent doc; every acceptance-worthy behavior in the doc appears as a `Scenario:`.
- Scenarios carry concrete values, per Specification by Example ([research](../../research/atdd-gherkin-agile.md)): "Given a cart holding 2 items at $5 each", never "Given some items".
- Declarative, at the behavior level: state WHAT the system does. Selectors, endpoints, and file paths belong to the coder seat's step definitions, so keep them out of the scenarios.
- The scenarios ARE the acceptance bar: the coder seat's story is done only when every scenario passes.

`enforced` today by [scripts/check-handoff.sh](scripts/check-handoff.sh): the file exists, has a `Feature:` line, at least one `Scenario:`, and at least one each of Given/When/Then. `advisory`: concreteness, declarativeness, and full behavior coverage are judgment; a later wave may add a linter.

## Artifact 2, the human-viewpoint QA procedure

The framing is verbatim doctrine (C9): *"You are a human. You are operating this system at the UI. You must prove that the system works."* Write it in the second person, to a human at the real interface.

Contract the qa-script-seat may rely on:

- Opens with the operator preamble: one line establishing "you are a human operating this system at the UI; you must prove the system works".
- Numbered steps. Each step pairs an action a human can take at the UI with an observable expected result: what you *see*, phrased as `Expected:` after the action.
- Human-visible actions ("click Save") and human-visible checks ("the banner reads Saved") only. Code, selectors, and tool names stay out, because determinizing the procedure into a script is the qa-script-seat's seat.
- Ends with the verdict rule: the system is proven only when every expected result was observed; any miss is a fail, never a note.

`enforced` today by [scripts/check-handoff.sh](scripts/check-handoff.sh): the file exists, contains the operator preamble, has numbered steps, and carries at least one `Expected:` marker. `advisory`: whether each step is truly human-observable is judgment.

## The gate's own red/green proof

The two `enforced` claims above rest on a gate that has been shown able to say no. Both runs below were executed from this island's directory, and the fixtures ship beside the script as its regression bed.

```bash
# Run from this island's directory (unclebob/skills/specifier-seat); elsewhere the
# relative paths do not resolve and the shell reports 127, not a gate verdict.
scripts/check-handoff.sh scripts/fixtures/dirty-checkout.feature scripts/fixtures/dirty-checkout.qa.md   # exit 1 — 6 checks red
scripts/check-handoff.sh scripts/fixtures/clean-checkout.feature scripts/fixtures/clean-checkout.qa.md   # exit 0 — PASS
```

The dirty pair is a realistic near-miss, not garbage: a prose `Scenario:` with no Given/When/Then, and QA notes written about a tester instead of to one. Re-run both after any change to the script. A modified gate is a new gate (`enforced`: the exit codes; `advisory`: whether the fixture still embodies the whole violation class).

## Done means verify, fix, re-verify

1. Emit both artifacts side by side (`<story>.feature` + `<story>.qa.md`), and only the pair.
2. Run `scripts/check-handoff.sh <feature> <qa-doc>`; fix and re-run until exit 0 (`enforced`: the script is the gate, and each check can go red).
3. Re-read the intent doc once: every behavior it settles maps to at least one scenario AND at least one QA step (`advisory`: exhaustiveness is judgment until a coverage checker exists, and this read stands in for it).
4. Hand off and die. The artifacts are ephemeral: they exist to launch this one story through the gauntlet. The durable truth is the passing gates, not these docs (C22).

**No authority without evidence. One settled doc in; exactly two artifacts out; the seat transforms, grill elicits.**
