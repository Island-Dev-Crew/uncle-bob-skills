# Uncle Bob Skills

**Twenty agent skills for directing AI coding agents, mined from one conversation and built so that every rule either names its measuring tool or admits it is advice.**

In 2026 Robert C. Martin ("Uncle Bob") sat down with Matt Pocock and described how he now builds software: he has stopped reading the code his agents write, and instead built a cage of deterministic gates around them. The reasoning is specific, mechanical, and mostly checkable — which is what makes it forgeable into skills rather than quotes.

This pack is that conversation turned into twenty working islands, each grounded in a numbered concept from the transcript, each with a stated boundary, and twelve of them shipping an executable gate that has been watched failing before it was trusted.

## The two laws

**No authority without evidence.** Nothing claims done without a captured result from a check that could have failed.

**Values transfer; disciplines don't; thresholds move.** Keep the value (tested, small, covered, clean), drop the human ritual, retune the number by experiment. Martin's corollary is the pack's whole architecture: you cannot tell an agent to be clean — you measure the cleanliness it produces and make it correct the failures.

## Install

Copy any island into your agent's skills folder:

```bash
cp -R skills/crap-gate ~/.claude/skills/
```

The islands are plain `SKILL.md` files with an `agents/openai.yaml` sidecar, so they load in Claude Code, Codex, Pi, and Hermes alike. There is no runtime, no package, and no install step — the gate scripts need only `python3` and `bash`.

## The twenty islands

**Doctrine** — [`boredom-dividend`](skills/boredom-dividend/SKILL.md) mines practices shelved only because they bored humans and revives them as agent gates · [`threshold-port`](skills/threshold-port/SKILL.md) ports a human practice to an agent without its ritual · [`margin-ledger`](skills/margin-ledger/SKILL.md) keeps gates from slowing agents below human speed

**The relay** — [`seat-relay`](skills/seat-relay/SKILL.md) stages one story through five specialist seats, each born, working, and dying with its context · [`specifier-seat`](skills/specifier-seat/SKILL.md) turns intent into a Gherkin spec and a human-viewpoint QA procedure · [`qa-script-seat`](skills/qa-script-seat/SKILL.md) turns that procedure into an executable verdict

**The gates** — [`crap-gate`](skills/crap-gate/SKILL.md) per-function complexity × coverage · [`mutant-hunt`](skills/mutant-hunt/SKILL.md) diff-scoped mutation testing · [`mutant-excusal-ledger`](skills/mutant-excusal-ledger/SKILL.md) the honest 100%, since equivalence is undecidable · [`dependency-fence`](skills/dependency-fence/SKILL.md) declared layering direction with three sanctioned repairs · [`known-dirty-fixture`](skills/known-dirty-fixture/SKILL.md) no gate is trusted until it has failed

**Context economy** — [`steering-audit`](skills/steering-audit/SKILL.md) sorts every prompt rule into prompt-worthy or gate-worthy · [`priority-zone`](skills/priority-zone/SKILL.md) budgets the head of the context where attention actually lands · [`trajectory-hygiene`](skills/trajectory-hygiene/SKILL.md) decides when to continue a context and when to kill it

**Structure** — [`arch-lens`](skills/arch-lens/SKILL.md) has the agents build the repo its own drill-down viewer · [`structure-interrogation`](skills/structure-interrogation/SKILL.md) asks the agents what they actually built, then corrects it

**Planning** — [`story-cadence`](skills/story-cadence/SKILL.md) small batches over plan-maxing, because heavy upfront specs replay waterfall · [`spec-mulch`](skills/spec-mulch/SKILL.md) the spec dies on merge; the result and its gates are the specification · [`essence-pointer`](skills/essence-pointer/SKILL.md) don't download the tool, study it and build your own

**The human** — [`thrash-watch`](skills/thrash-watch/SKILL.md) recognises agent struggle the way an experienced engineer recognises their own, and ranks the interventions: stop, clean, repartition, respawn

*(The education islands — `human-subagent`, which trains a junior by running them under the gates the agents run, and `strategy-shelf`, the old-books curriculum behind the strategic seat — are specified in the roster for a later wave and are not in this release.)*

## Verify it yourself

Nothing here asks to be believed:

```bash
python3 scripts/validate-island.py skills/*/
```

Twelve mechanical checks per island, 240 in total. The validator is proven the same way everything else is — it goes red on `scripts/fixtures/bad-island` and green on `good-island`. Every gate script ships its own dirty and clean fixture, and [04-WAVE1-GAUNTLET.md](04-WAVE1-GAUNTLET.md) records what a blind critic caught in each island before it shipped, including three gates that separated their own fixtures but could still be bypassed until they were fixed.

## How it was built

Each island was authored by one agent, then judged by a **blind critic** that never saw the build brief — only the island's contract and a falsifiable evaluation spec. Thirteen passed first time, six after one fix round, one took three. The critics caught laundered evidence, invented provenance, dead links, and gate bypasses; the record of every finding is in the gauntlet report.

## Reading the evidence

| file | what it is |
|---|---|
| [CONTEXT.md](CONTEXT.md) | the pack's substrate — the two laws, grounding rules, how the islands compose |
| [01-CONCEPT-LEDGER.md](01-CONCEPT-LEDGER.md) | 28 concepts (C1–C28) from the conversation, each with a transcript-verified quote |
| [00-EXTRACTION.md](00-EXTRACTION.md) | the two-channel video analysis — what was said, what was shown, what checked out |
| [02-ROSTER-50.md](02-ROSTER-50.md) | the full 50-island roster; islands 21–50 are not yet built |
| [03-FORGE50-AUDIT.md](03-FORGE50-AUDIT.md) | the overlap audit that set every island's boundary |
| [04-WAVE1-GAUNTLET.md](04-WAVE1-GAUNTLET.md) | build and gauntlet record — verdicts, defects, and what remains advisory |
| [COMPANION.md](COMPANION.md) | 21 concerns this pack deliberately does not own, and who does |
| [research/](research/) | seven primary-sourced briefs; unsourced claims flagged `UNVERIFIED` |
| [source/](source/) | the transcript, the timestamped captions, and the frames worth keeping |

## Honest state

v1.0 ships Wave 1: twenty islands, mechanically clean, gauntleted, with twelve proven gates. Most in-island rules are `advisory` and say so — these are first-version islands, and the pack would rather admit that than dress advice up as enforcement. Islands 21–50 are specified in the roster and not yet built.

## Credit

The thinking is Robert C. Martin's, from a conversation with Matt Pocock ([video](https://www.youtube.com/live/zcLPGC-tvgk)). His own tools are public and worth reading before this pack — [swarm-forge](https://github.com/unclebob/swarm-forge), [crap4java](https://github.com/unclebob/crap4java), [crap4go](https://github.com/unclebob/crap4go), [crap4clj](https://github.com/unclebob/crap4clj) — and in his own words, the right move is not to download them but to point your agents at them and build your own. This pack is that instruction taken literally.

Built with the IDC Forge methodology. Boundaries in [COMPANION.md](COMPANION.md).

**No authority without evidence.**

Roll Tide · Island Development Crew · Huntsville, AL
