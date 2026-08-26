# Uncle Bob Skills

**Fifty agent skills for directing AI coding agents, mined from one conversation and built so that every rule either names its measuring tool or admits it is advice.**

In 2026 Robert C. Martin ("Uncle Bob") sat down with Matt Pocock and described how he now builds software: he has stopped reading the code his agents write, and instead built a cage of deterministic gates around them. The reasoning is specific, mechanical, and mostly checkable — which is what makes it forgeable into skills rather than quotes.

This pack is that conversation turned into fifty working islands, each grounded in a numbered concept from the transcript, each with a stated boundary, and every one that ships an executable gate has been watched failing before it was trusted.

## The two laws

**No authority without evidence.** Nothing claims done without a captured result from a check that could have failed.

**Values transfer; disciplines don't; thresholds move.** Keep the value (tested, small, covered, clean), drop the human ritual, retune the number by experiment. Martin's corollary is the pack's whole architecture: you cannot tell an agent to be clean — you measure the cleanliness it produces and make it correct the failures.

## Install

**The supported topology is the whole pack.** Clone it and point your agent's skills folder at `skills/`:

```bash
git clone https://github.com/Island-Dev-Crew/uncle-bob-skills.git
ln -s "$PWD/uncle-bob-skills/skills" ~/.claude/skills/uncle-bob
```

The islands are plain `SKILL.md` files with an `agents/openai.yaml` sidecar, so they load in Claude Code, Codex, Pi, and Hermes alike. There is no runtime, no package, and no install step — the gate scripts need only `python3` and `bash`.

Copying one island out on its own is not supported, and the reason is mechanical rather than stylistic: **all fifty link outside their own directory** — 64 distinct outside-island targets across the pack, and 42 islands cite the pack validator or `prove-gate.sh` as the evidence for their only `enforced` claim. (Both numbers re-derivable from the committed tree; an earlier figure here, 442, could not be reproduced by any counting method and is retired rather than defended.) Lift one island out and those links resolve to nothing: the two laws in [CONTEXT.md](CONTEXT.md), the ledger concept its every quote rests on, the boundary in [COMPANION.md](COMPANION.md) that says what it refuses, its sibling islands, and the validator that proves it. What survives is the prose; what is severed is the evidence graph the prose points at — which is the one thing this pack asks to be judged on. A single-island copy is a reading copy, not a working one.

## The founding layer (v1.0)

**Doctrine** — [`boredom-dividend`](skills/boredom-dividend/SKILL.md) mines practices shelved only because they bored humans and revives them as agent gates · [`threshold-port`](skills/threshold-port/SKILL.md) ports a human practice to an agent without its ritual · [`margin-ledger`](skills/margin-ledger/SKILL.md) keeps gates from slowing agents below human speed

**The relay** — [`seat-relay`](skills/seat-relay/SKILL.md) stages one story through five specialist seats, each born, working, and dying with its context · [`specifier-seat`](skills/specifier-seat/SKILL.md) turns intent into a Gherkin spec and a human-viewpoint QA procedure · [`qa-script-seat`](skills/qa-script-seat/SKILL.md) turns that procedure into an executable verdict

**The gates** — [`crap-gate`](skills/crap-gate/SKILL.md) per-function complexity × coverage · [`mutant-hunt`](skills/mutant-hunt/SKILL.md) diff-scoped mutation testing · [`mutant-excusal-ledger`](skills/mutant-excusal-ledger/SKILL.md) the honest 100%, since equivalence is undecidable · [`dependency-fence`](skills/dependency-fence/SKILL.md) declared layering direction with three sanctioned repairs · [`known-dirty-fixture`](skills/known-dirty-fixture/SKILL.md) no gate is trusted until it has failed

**Context economy** — [`steering-audit`](skills/steering-audit/SKILL.md) sorts every prompt rule into prompt-worthy or gate-worthy · [`priority-zone`](skills/priority-zone/SKILL.md) budgets the head of the context where attention actually lands · [`trajectory-hygiene`](skills/trajectory-hygiene/SKILL.md) decides when to continue a context and when to kill it

**Structure** — [`arch-lens`](skills/arch-lens/SKILL.md) has the agents build the repo its own drill-down viewer · [`structure-interrogation`](skills/structure-interrogation/SKILL.md) asks the agents what they actually built, then corrects it

**Planning** — [`story-cadence`](skills/story-cadence/SKILL.md) small batches over plan-maxing, because heavy upfront specs replay waterfall · [`spec-mulch`](skills/spec-mulch/SKILL.md) the spec dies on merge; the result and its gates are the specification · [`essence-pointer`](skills/essence-pointer/SKILL.md) don't download the tool, study it and build your own

**The human** — [`thrash-watch`](skills/thrash-watch/SKILL.md) recognises agent struggle the way an experienced engineer recognises their own, and ranks the interventions: stop, clean, repartition, respawn

## The canon layer (v1.1)

Fifteen more islands, where the conversation's claims meet the books behind them.

**Structure measured, not argued** — [`stability-order`](skills/stability-order/SKILL.md) instability, abstractness and distance from the main sequence as checks · [`component-cohesion`](skills/component-cohesion/SKILL.md) the REP/CCP/CRP triangle, sized so a component is also a context-window unit · [`interface-budget`](skills/interface-budget/SKILL.md) deep modules priced in tokens: work from the interface before loading the body · [`leak-scan`](skills/leak-scan/SKILL.md) one design decision expressed twice is a fact paid for twice

**Comments and errors as design** — [`comment-as-spec`](skills/comment-as-spec/SKILL.md) the interface comment is the spec a model acts from, and it must not leak the implementation · [`define-errors-out`](skills/define-errors-out/SKILL.md) redesign the API so the error case stops existing rather than handling it again

**Drift caught early** — [`boyscout-ratchet`](skills/boyscout-ratchet/SKILL.md) every touched file leaves measurably no worse, so a legacy repo can adopt a gate it cannot pass today · [`tornado-detector`](skills/tornado-detector/SKILL.md) files-touched-per-feature climbing is a design decision smearing across the codebase · [`strategic-ledger`](skills/strategic-ledger/SKILL.md) holds the tactical/strategic split near its band, with structural evidence

**The acceptance surface** — [`gherkin-gate`](skills/gherkin-gate/SKILL.md) scenarios red before, green after, living outside the prompt where nothing decays · [`tests-as-spec`](skills/tests-as-spec/SKILL.md) the suite written for the reader who never met the author · [`acceptance-surface-review`](skills/acceptance-surface-review/SKILL.md) what a human still reads, and how blast radius widens it

**Patrolling the pack's own metrics** — [`coverage-gaming-audit`](skills/coverage-gaming-audit/SKILL.md) coverage measures execution, not assertion · [`gate-toolchain`](skills/gate-toolchain/SKILL.md) the tool per language, incremental mode required inside the loop · [`values-not-disciplines`](skills/values-not-disciplines/SKILL.md) every quality rule names its measuring tool or is marked advisory

## The strategy layer (v1.2)

The last fifteen, and the ones the conversation ends on: who holds a design when agents write the code, and how anyone learns to hold one.

**Who decides** — [`conceptual-integrity-owner`](skills/conceptual-integrity-owner/SKILL.md) one named human owns the design; headcount never substitutes · [`no-silver-bullet-triage`](skills/no-silver-bullet-triage/SKILL.md) agents get the accidental complexity, humans keep the essential · [`manageability-review`](skills/manageability-review/SKILL.md) accept only code a human can still restate

**Fleet economics** — [`mythical-agent-month`](skills/mythical-agent-month/SKILL.md) adding agents adds coordination surface, not progress · [`do-it-twice`](skills/do-it-twice/SKILL.md) walk one thin slice end to end before any fan-out · [`change-cost-probe`](skills/change-cost-probe/SKILL.md) measure what a change actually costs instead of asserting it

**Structure by secrets** — [`parnas-partition`](skills/parnas-partition/SKILL.md) every module names the decision it hides or the split is refused · [`coupling-budget`](skills/coupling-budget/SKILL.md) every cross-module edge a change adds spends from a budget

**Keeping ourselves honest** — [`measurement-humility`](skills/measurement-humility/SKILL.md) every enforced metric names what it might corrupt and when it is re-examined · [`egoless-fleet`](skills/egoless-fleet/SKILL.md) a review that found nothing and looked for nothing is not a review · [`instruction-density-cap`](skills/instruction-density-cap/SKILL.md) a prompt carrying more directives than the model tracks · [`plan-decay-detector`](skills/plan-decay-detector/SKILL.md) halt when the plan's assumptions stop matching the tree

**The education layer** — [`human-subagent`](skills/human-subagent/SKILL.md) train a junior by running them as an agent, under the same gates · [`strategy-shelf`](skills/strategy-shelf/SKILL.md) the old-books curriculum behind the strategic seat · [`abstraction-ladder`](skills/abstraction-ladder/SKILL.md) why fundamentals survive every rung, and the test to apply before discarding one

## Verify it yourself

Nothing here asks to be believed:

```bash
python3 scripts/validate-island.py skills/*/     # 600 checks across 50 islands
python3 scripts/verify-proofs.py                 # re-runs every command an island states an exit code for
python3 scripts/lane-check.py                    # every shipped script stays in its lane
```

Twelve mechanical checks per island. The validator is proven the same way everything else is — it goes red on `scripts/fixtures/bad-island` and green on `good-island`. Every gate script ships its own dirty and clean fixture.

The second tool re-runs **every command an island states an exit code for**, and says out loud what it did not run rather than passing over it. Its summary line counts each class at the head you run it on: proofs run, `PENDING` (a runnable line with no code documented for it), `TEMPLATE` (a `<placeholder>` argument), `SKIPPED` (a leading token off its allowlist), `REFUSED`. Pass `--strict` to make any PENDING a failure. The classification itself is proven the pack's way, against a fixture carrying all five shapes in one block:

```bash
python3 scripts/verify-proofs.py scripts/fixtures/proof-grammar-island            # exit 0 — 2 proofs run
python3 scripts/verify-proofs.py --strict scripts/fixtures/proof-grammar-island   # exit 4 — 1 PENDING
python3 scripts/verify-proofs.py scripts/fixtures/hostile-proof-island            # exit 1 — REFUSED
python3 scripts/verify-proofs.py scripts/fixtures/good-island                     # exit 3 — nothing ran
python3 scripts/verify-proofs.py scripts/fixtures/unsafe-export-island            # exit 1 — a poisoned PATH export is refused, never replayed
python3 scripts/closed-stream-check.py scripts/fixtures/verdict-flip-island       # exit 1 — a gate whose documented 1 flips to a clean 0 on a dead pipe is a LEAK
```

Exit 3 is the one that matters: a verifier that executed nothing has verified nothing, and reporting that as a pass is the same failure as a gate that scans zero files.

[04-WAVE1-GAUNTLET.md](04-WAVE1-GAUNTLET.md), [05-WAVE2-GAUNTLET.md](05-WAVE2-GAUNTLET.md) and [06-WAVE3-GAUNTLET.md](06-WAVE3-GAUNTLET.md) record what blind critics caught before each wave shipped — including gates that separated their own fixtures perfectly and were still walked past, which is why the critics were eventually told to forge inputs rather than re-run the author's.

## How it was built

Each island was authored by one agent, then judged by a **blind critic** that never saw the build brief — only the island's contract and a falsifiable evaluation spec. Thirteen passed first time, six after one fix round, one took three. The critics caught laundered evidence, invented provenance, dead links, and gate bypasses; the record of every finding is in the gauntlet report.

## Reading the evidence

| file | what it is |
|---|---|
| [CONTEXT.md](CONTEXT.md) | the pack's substrate — the two laws, grounding rules, how the islands compose |
| [01-CONCEPT-LEDGER.md](01-CONCEPT-LEDGER.md) | 28 concepts (C1–C28) from the conversation, each with a transcript-verified quote |
| [00-EXTRACTION.md](00-EXTRACTION.md) | the two-channel video analysis — what was said, what was shown, what checked out |
| [02-ROSTER-50.md](02-ROSTER-50.md) | **historical** — the roster as planned, before any island was built |
| [03-FORGE50-AUDIT.md](03-FORGE50-AUDIT.md) | **historical** — the overlap audit that set every island's boundary |
| [04](04-WAVE1-GAUNTLET.md)/[05](05-WAVE2-GAUNTLET.md)/[06-GAUNTLET](06-WAVE3-GAUNTLET.md) | build and gauntlet record per wave — verdicts, defects, and what remains advisory |
| [07-HARDENING-PLAN-2.0.md](07-HARDENING-PLAN-2.0.md) | **live** — the 2.0 threat model and its five phases, with each phase's evidence |
| [COMPANION.md](COMPANION.md) | 22 concerns this pack deliberately does not own, and who does |
| [research/](research/) | seven primary-sourced briefs; [research/README.md](research/README.md) states the per-claim `UNVERIFIED` convention |
| [source/](source/) | eleven notable frames, plus the recipe that regenerates the transcript this pack was checked against |

## Honest state

v1.2 completes the roster: **50 islands**, mechanically clean and gauntleted, with every gate script carrying a red/green fixture pair it has been watched failing.

Most in-island rules are `advisory` and say so — six of the final fifteen ship no script at all, because who holds a design and whether a human can restate a change are not arithmetic, and a gate around judgment would be theatre. Several islands document a limit they chose not to close and ship a fixture capturing it as a run: `stability-order` cannot see a pure dependency cycle, `coverage-gaming-audit` cannot see a `conftest.py`-hooked suite, `comment-as-spec` cannot resolve an imported base class, `instruction-density-cap` under-counts a rule wearing no marker it recognises. An evidenced boundary beats a silent one.

### What is in the tree, counted from the tree

**50** islands under `skills/` · **28** ledger concepts (C1–C28) · **22** companion boundaries · **7** research briefs · **11** notable frames · every shipped skill script lane-checked, with `scripts/lane-check.py` printing how many it scanned rather than this line asserting a number that drifts.

**Not in the tree, deliberately:** the full transcript and the complete `.srt` caption file. Both are the whole of someone else's recorded conversation, so this repository cites them and does not redistribute them — they are in `.gitignore`, and [source/README.md](source/README.md) carries the two commands that regenerate them from the published video. Every quote-verification step in this pack runs against that regenerated file, not against a copy shipped here. A fresh clone therefore has the frames and the recipe, not the transcript.

**Document lifecycle**, so a stale plan is never read as a live claim: `README`, `CONTEXT`, `CHANGELOG`, `COMPANION`, the ledger and the briefs are **live** and describe the tree as it stands. `02-ROSTER-50` and `03-FORGE50-AUDIT` are **historical** — they record what was planned and why, before the islands existed, and are kept unrewritten rather than back-edited into agreement. `04`/`05`/`06` are **records** of a wave that has closed. `07-HARDENING-PLAN-2.0` is **live**: phases 1–3 are complete with their evidence written in, phase 4 (cross-family review at a frozen head) is in progress — one independent non-Anthropic round has been returned and closed, the SHA-bound receipt has not — and phase 5 (release integrity) is open. That is what remains before 2.0.

## Credit

The thinking is Robert C. Martin's, from a conversation with Matt Pocock ([video](https://www.youtube.com/live/zcLPGC-tvgk)). His own tools are public and worth reading before this pack — [swarm-forge](https://github.com/unclebob/swarm-forge), [crap4java](https://github.com/unclebob/crap4java), [crap4go](https://github.com/unclebob/crap4go), [crap4clj](https://github.com/unclebob/crap4clj) — and in his own words, the right move is not to download them but to point your agents at them and build your own. This pack is that instruction taken literally.

Built with the IDC Forge methodology. Boundaries in [COMPANION.md](COMPANION.md).

**No authority without evidence.**

Roll Tide · Island Development Crew · Huntsville, AL
