---
name: seat-relay
description: Stage one story through the serial five-seat specialist relay - specifier, coder, cleaner, hardener, QA - one fresh-context agent per seat, each handing a typed artifact to the next. Use inside spec-pipeline's implement stage when a story warrants gated quality, or on "run the seat relay", "five-seat relay", "stage this story through the seats". Differentiator - serial role specialization with born-do-die contexts; gauntlet-loop fans out parallel builders against one falsifiable bar, this island hands one baton down five seats in order.
---

# Seat Relay: one baton, five specialist seats

Uncle Bob's staged relay for a single story: specifier → coder → cleaner → hardener → QA, each seat a fresh-context specialist agent (C9). A seat is born, does exactly its task, hands a **typed artifact** — the baton — to the next seat, and dies: *"agents are born, do the task, and die so that the next one comes in with a clean context"* (C10). Focus is the point: *"when you focus the agents down to a single task, you're keeping the context window under control"* (C10). The baton, never the dead seat's memory, is the story's state between seats. Ledger ground: [../../01-CONCEPT-LEDGER.md](../../01-CONCEPT-LEDGER.md).

## Where this island sits

State these boundaries before staging anything; each names the neighbor that owns the adjacent concern.

- **Inside [`spec-pipeline`](../../COMPANION.md#spec-pipeline) Stage 3 (implement).** The relay is an execution discipline for one story inside the implement stage — spec-pipeline owns the spec → tickets → implement chain, and the relay stays a discipline within its third stage, never a parallel spec-to-ship pipeline of its own. The specifier seat consumes a ticket or intent doc the pipeline already produced.
- **Serial, where [`gauntlet-loop`](../../COMPANION.md#gauntlet-loop) is parallel.** Gauntlet-loop owns fanning out PARALLEL builders against one falsifiable bar; this island owns SERIAL role specialization — one baton handed down five different mandates. Many attempts at one bar → gauntlet-loop (also user-invoked — no agent can fire it by description; the human runs it, or read its SKILL.md at the link); staged specialist passes → here.
- **Seat mandates come from [`delegated-authority-prompt`](../../COMPANION.md#delegated-authority-prompt).** Each seat runs unattended, so compose its mandate as a front-loaded authority prompt with explicit stop conditions. That island is user-invoked — no agent can fire it by description; read its SKILL.md directly at the link and apply the pattern, or have the human run it.
- **Per-seat model picks route through [`model-routing`](../../COMPANION.md#model-routing)** — the cheapest model above each seat's cognitive floor (a cleaner grinding CRAP reports needs less than a specifier translating human intent).
- **Seat isolation reuses [`worktree-fleet`](../../COMPANION.md#worktree-fleet) mechanics where files are mutated in parallel.** Seats are serial within one story; when several stories are in flight and more than one coder mutates the same repo, give each its own worktree. That island is also user-invoked — read it directly; its evidence boundary (worktree artifacts are inadmissible as gate evidence until re-derived from a fresh clone) applies to batons produced in worktrees.

## The five seats and their batons

| # | Seat | Reads | Baton it delivers | Exit gate |
|---|---|---|---|---|
| 1 | Specifier | intent doc (the human-written story) | Gherkin acceptance tests + a QA procedure written from a human operator's point of view (C9) | Gherkin parses; QA procedure exercises the story through the UI |
| 2 | Coder | Gherkin + QA procedure | code + unit tests + passing Gherkin (C9) | full test suite green, Gherkin included |
| 3 | Cleaner | code + tests | cleaned code + CRAP report (C9, C6) | every touched function at or below the CRAP ceiling — 6 for agents, per C17 |
| 4 | Hardener | cleaned code + tests | mutation log + kill-tests (C9, C7) | zero unexcused surviving mutants on the story diff; excusals recorded in an equivalence ledger ([research](../../research/mutation-testing.md)) |
| 5 | QA | QA procedure + built system | executable QA script + deterministic verdict (C9) | the script runs the system end to end and exits green |

Each exit gate loops on its named tool where one exists (C4): the seat *"must change the code until this tool says that it's okay"* — that tool's exit code decides, never the seat's self-report. Seat 1's gate is split: the Gherkin-parses clause is mechanical (a Gherkin parser's dry-run exit code); the QA-procedure-exercises-the-UI clause is advisory — a judgment on prose the mandate composer makes, cashed out mechanically only when seat 5 executes the procedure as a script.

## Running the relay

1. **Compose the mandate** for the next seat: its input baton, its exit gate, its stop conditions (the delegated-authority-prompt pattern, read at the link above).
2. **Spawn a fresh agent** for the seat — new context, mandate + baton only. Pick its model via model-routing.
3. **Run to the gate.** The seat loops against its deterministic tool until green, or a stop condition trips.
4. **Collect the baton, kill the seat.** Write the artifact into the story's workspace under a per-seat name (`01-gherkin/`, `02-code/`, `03-crap-report/`, `04-mutation-log/`, `05-qa-verdict/` or the project's equivalent). The seat's context is then dead.
5. **A red gate downstream returns the baton upstream to a fresh agent in the owning seat.** The failure report travels with the baton; the dead context is never resuscitated (C10). Example: a surviving mutant the hardener cannot honestly kill is a coder-seat defect — respawn seat 2 with the mutation log attached.
6. **Repeat 1–5 until seat 5's verdict is green,** then hand the story back to spec-pipeline's implement checkpoint.

## The economics

The relay deliberately trades speed for quality inside a bounded margin (C5): a single agent one-shots a story in ~5 minutes at questionable quality; the full relay takes ~1 hour; a human takes ~half a day — *"factor of four, factor of five improvement… and very high quality"* (C5). The accounting unit is the margin, never the wall clock: *"as long as you can keep the margin of productivity higher than a human, you're still ahead of the game"* (C5). When gates stack until the relay runs slower than the human, cut gates until the margin returns; the margin, not gate count, is what the relay defends.

## Enforced vs advisory (v0, stated honestly)

- **Enforced today:** this island's own structure — [`validate-island.py`](../../scripts/validate-island.py) gates frontmatter, sidecar, ledger citations, and line budget with a real exit code. Inside a target project, a seat's exit gate is enforced exactly where the named tool runs and blocks: the Gherkin parser's dry-run exit code, the test runner's exit code, the CRAP tool's report, the mutation tester's survivor count. Enforcement lives in that tool's exit code (C4), never in this prose.
- **Advisory at v0:** everything about staging — spawning fresh seats, killing contexts, baton naming, the upstream-return rule, the margin accounting. This island ships no relay-runner script yet (an orchestrator is neither under ~100 lines nor deterministic); a later wave adds one and promotes these rules. Until then the operator stages the seats, and any claim that "the relay ran" without the five batons on disk stays `unverified` ([repo law](../../CONTEXT.md)).

## Done conditions

The relay is complete for a story when every check below passes; a red at any point loops verify → fix (a fresh agent in the owning seat) → re-verify:

- [ ] five batons exist on disk, one per seat, in relay order
- [ ] each baton carries its gate's captured output (test run, CRAP report, mutation log, QA exit code) — evidence from a check that could have failed
- [ ] seat 5's QA verdict is green and rerunnable
- [ ] every upstream return is logged with which seat was respawned and why

**No authority without evidence. The baton is the story's state; the seat that made it is already dead.**
