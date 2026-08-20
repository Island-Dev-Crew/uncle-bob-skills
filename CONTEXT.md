# CONTEXT — the Uncle Bob pack substrate

The shared file the islands read and write to coordinate. This pack is a standalone archipelago: twenty islands mined from one conversation between Robert C. Martin and Matt Pocock about directing AI coding agents, each a self-contained skill, all obeying the two laws below.

## The two laws

**1. No authority without evidence.** A claim is not done until a captured piece of evidence — from a check that could have failed — proves it. State enforced-vs-advisory explicitly; never imply it. Mark unverified work `unverified`; never launder it into `verified`.

Applied to this pack's own construction, that law has a sharp edge: **a gate is not trusted until it has been watched failing.** Every one of the twelve gate scripts here ships a red/green fixture pair, and each was executed in both directions before its island was allowed to claim it. The island that states this rule, [`known-dirty-fixture`](skills/known-dirty-fixture/SKILL.md), earned its own claim the same way.

**2. Values transfer; disciplines don't; thresholds move.** The source's own sharpest formulation, from Robert C. Martin: *"it's probably a mistake to impose a human discipline on an agent. It is not a mistake to impose human values on the agent, but there may be thresholds that we need to change"* (concept C17 in [01-CONCEPT-LEDGER.md](01-CONCEPT-LEDGER.md)).

Its enforcement corollary, also his: *"You can't tell an agent to be clean. You have to measure the cleanliness that they produce and have them correct failures."* Prose rules decay in the middle of a context; a tool in a fix-until-green loop does not. **Every quality rule in this pack names its measuring tool or is marked `advisory`.**

## Grounding

Every claim about the conversation cites a numbered concept `C1`–`C28` in [01-CONCEPT-LEDGER.md](01-CONCEPT-LEDGER.md), and every ledger concept carries a quote verified against the transcript in [source/](source/). An island may not quote the conversation from memory; it cites the ledger, which cites the transcript. Claims that go beyond the conversation cite a brief in [research/](research/), where anything unsourced is flagged `UNVERIFIED` rather than smoothed over.

Auto-caption garbles are corrected once, in the ledger, and never re-introduced: the C.R.A.P. metric is **Savoia & Evans, 2007**; "Dex Hardy" is **Dex Horthy**; "John Aster" is **John Ousterhout**.

## How the islands compose

- **doctrine** — `boredom-dividend` is the generative move the pack is built on (revive practices shelved only because they bored humans); `threshold-port` ports any human practice to an agent; `values-not-disciplines` discipline runs through every island's enforced-vs-advisory section.
- **the relay** — `seat-relay` stages a story through five specialist seats; `specifier-seat` is its intake and `qa-script-seat` its exit; each seat is born, works, and dies with its context.
- **the gates** — `crap-gate` (complexity × coverage), `mutant-hunt` (diff-scoped mutation) with `mutant-excusal-ledger` (the honest 100%), `dependency-fence` (layering direction), each proven red before trusted by `known-dirty-fixture`.
- **context economy** — `steering-audit` sorts rules into prompt-worthy or gate-worthy; `priority-zone` budgets the head of the context; `trajectory-hygiene` decides when to continue and when to kill and respawn.
- **structure** — `arch-lens` renders the repo's own drill-down viewer; `structure-interrogation` asks the agents what they actually built and corrects it.
- **planning** — `story-cadence` argues small batches over plan-maxing; `spec-mulch` deletes the spec on merge; `essence-pointer` specifies by exemplar rather than by download.
- **the human** — `thrash-watch` recognises agent struggle; `margin-ledger` keeps the productivity margin honest; `human-subagent` runs a junior under the same gates the agents run; `strategy-shelf` is the old-books curriculum behind the strategic seat.

## Boundaries

This pack was built under the IDC Forge methodology and deliberately refuses concerns the Forge already owns. Those refusals are recorded in [COMPANION.md](COMPANION.md) — twenty-one named boundaries, each saying what the pack does *not* do and who does. They are boundary statements, not dependencies: everything here runs from a fresh clone with `python3` and `bash` and nothing else.

## Verification

```bash
python3 scripts/validate-island.py skills/*/
```

Twelve mechanical checks per island. The validator itself is proven the pack's way: red on `scripts/fixtures/bad-island`, green on `good-island`.

Roll Tide · Island Development Crew · Huntsville, AL
