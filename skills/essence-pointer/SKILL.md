---
name: essence-pointer
description: Specify a tool by exemplar - a live working reference (unclebob/swarm-forge, crap4java/crap4go/crap4clj) serves as the whole spec for a customized local equivalent, with parity proven against the exemplar's own test suite where one exists. Use when adopting one of Uncle Bob's harness or gate tools, porting a checker to your own stack, or the user says "build us our own crap tool", "point the agents at that repo and make one for us", or "study it, don't vendor it". Differentiator - the exemplar stays upstream as spec, never as dependency; trust of the built copy is a separate red-fixture acceptance, not this island's claim.
---

# Essence Pointer: the exemplar is the spec

Bob's rule for his own gate tools (the crap tool, the mutation tester, the agent harness): *"don't download those. I wrote them for me… point your agents at them, have… the agents look at them, and then build one for you… a far better way of specifying the essence of something and then customizing it to your particular need"* (C23, quoted via [the ledger](../../01-CONCEPT-LEDGER.md)). A vendored tool carries its author's circumstances — his languages, his layout, his thresholds — into your repo as a frozen dependency. A studied one leaves only its **essence**: the invariant behavior, re-grown in your stack, under your thresholds, as code your own gates can hold to account. The research brief names the pattern Specification by Example inverted — the working example IS the whole spec ([atdd-gherkin-agile](../../research/atdd-gherkin-agile.md)).

## Live exemplars to point at

| Exemplar | What it demonstrates | Ground |
|---|---|---|
| `github.com/unclebob/swarm-forge` | the tmux multi-agent harness | [martin-canon](../../research/martin-canon.md) |
| `github.com/unclebob/crap4java` · `crap4go` · `crap4clj` | per-function CRAP gates over real coverage artifacts | actively updated Aug 2026, verified via GitHub API — [crap-metric](../../research/crap-metric.md) |
| this repo's own islands | skill shape and the evidence discipline | the tree you are standing in |

Any working tool you respect qualifies; these are the ones Bob explicitly points people at (C23).

## The move

1. **Pin the exemplar.** Record URL + full commit SHA of exactly what the agents studied, next to where the generated tool will live. The essence claim must be reproducible against exact bytes. `advisory` — no checker exists yet; a later wave can add one.
2. **Point the agents at it.** They read the README, the core source, and above all its tests — agents *"read tests to understand what the system does"* (C16). Have them write down the split: **essence** (the invariant behavior — what it measures, what it gates, what its inputs and exit codes mean) versus **circumstance** (the author's language, file layout, and threshold numbers). `advisory` — the split is judgment; writing it down gives a reviewer something concrete to disagree with.
3. **Build the local equivalent**, customized to your stack and your thresholds — customization is half of C23's point, and thresholds are yours to set, not the exemplar's to dictate (C17: values transfer, thresholds move). The exemplar stays upstream as reference only; your dependency tree gains the equivalent you built.
4. **Prove parity against the exemplar's own test suite where one exists.** Port or adapt the exemplar's tests to run against your equivalent, then run them. `enforced` when the exemplar ships a runnable suite — the suite's exit code is the mechanical gate, and the captured run is the parity evidence. `advisory` when it ships none — compare behavior on shared sample inputs, name exactly what you compared, and mark parity `unverified`; per [the law](../../CONTEXT.md), unverified never launders into verified.
5. **Loop until green.** Parity red → fix the equivalent (or your reading of the essence) → re-run. Done is the suite green, or an honest `unverified` with the gap named.

### Worked split (essence vs. circumstance)

Porting `crap4go`: the essence is the formula `comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)` joined per-function to a coverage artifact, with a non-zero exit on threshold breach ([crap-metric](../../research/crap-metric.md)). The circumstance is Go's `-coverprofile` format and Bob's own threshold number — both are yours to replace. How to *use* a CRAP gate afterward is a neighboring island's concern; this island only gets the tool born.

## Done when

- [ ] Exemplar pinned: URL + full SHA recorded beside the generated tool.
- [ ] The essence/circumstance split is written down.
- [ ] Local equivalent runs end-to-end on this repo's real inputs.
- [ ] Parity evidence captured: exemplar-suite run green (`enforced`, exit code), or explicitly `unverified` with what-was-compared named.
- [ ] The red acceptance handoff (below) is booked before the tool guards anything.

## Boundaries — who owns what

- **Parity is not trust.** Green parity proves your copy matches the exemplar; it proves nothing about whether the tool will catch anything. The generated tool is not trusted until it fails red on a known-bad input — that acceptance step is [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s seat, and this island's output is that island's input.
- **Adopting, not building?** When a third-party skill is coming in wholesale as prose your agent will obey, that is an intake audit, not an essence port: third-party skill adoption audits stay with [`skill-supply-chain-review`](../../COMPANION.md#skill-supply-chain-review).

**No authority without evidence. The exemplar is the spec; the copy proves itself — first against the exemplar's own tests, then red against a dirty fixture.**
