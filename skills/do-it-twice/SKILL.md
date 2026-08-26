---
name: do-it-twice
description: Royce 1970 read forwards - the paper that drew the waterfall also called the single-pass model risky and prescribed building it twice, a pilot version first. Walk one thin end-to-end slice through the entire pipeline and capture the evidence before any parallel fan-out, because dispatching N agents down an unvalidated path multiplies one wrong assumption by N. Reach for it before spawning parallel agents or worktrees, when someone says 'let us parallelize this', 'spin up three coders', 'fan out the remaining stories', or 'the plan is ready, dispatch the fleet'. Differentiator - this island owns only the pre-dispatch evidence requirement and the record that carries it; ticket machinery, batch size, and fleet sizing belong to neighboring seats.
---

# Do It Twice: the paper the industry read backwards

Royce's 1970 paper, *Managing the Development of Large Software Systems*, drew the single-pass diagram everyone later called waterfall. The same paper then wrote that the model *"is risky and invites failure"*, and prescribed instead that you **do it twice**: build a pilot version first, then the deliverable ([seventies-canon](../../research/seventies-canon.md), [atdd-gherkin-agile](../../research/atdd-gherkin-agile.md)). The diagram was adopted. The warning printed beside it was not. Fifty-six years later, that warning is still the cheapest thing you can buy before a fan-out.

Bob names the temptation as literally the same one: *"The temptation is to specify, specify, specify and then give it to the agent. This is a very old temptation… in the 70s. It led us to the waterfall process"* (C19, quoted via [the ledger](../../docs/01-CONCEPT-LEDGER.md)). What the agent era adds is the multiplier: *"you could have three coders running at the same time. And my little laptop can support a lot more than three"* (C10). A fan-out does not divide risk across the fleet. **It multiplies one wrong assumption by the fleet size**, and every agent that reaches the same unwalked stage hits that wall independently, at full price. The failure mode is Bob's, exactly: *"they're running half-cocked off on some nonsense that you have to stop, back up, rewrite the plan"* (C19), now happening in N places at once.

## The rule

**Walk one thin end-to-end slice through the whole pipeline, capture the evidence, then dispatch in parallel.**

- **Thin.** One story, the smallest that still touches every stage. Bob's cadence is *"a story or two"* (C20); the pilot is the first of them, run alone.
- **End-to-end.** Every stage the fan-out will use. If the fleet runs specifier → coder → cleaner → hardener → QA (C9), the pilot walks all five. The stage the pilot skips is the stage every parallel agent finds together.
- **Evidenced.** Each stage leaves an artifact from a run that could have failed, per the pack's first law ([`CONTEXT.md`](../../CONTEXT.md)). *"It walked and it seemed fine"* is the claim; the captured artifact is the evidence. Pilot code may be thrown away. The artifacts may not.
- **Then dispatch.** Re-run the gate whenever the pipeline changes, because a changed pipeline is a new pipeline with a new unwalked stage.

The pilot is not a spike or a design experiment (that is [`prototype`](../../COMPANION.md#prototype)'s seat, and throwaway code is its concern). It is the same pipeline the fleet will use, run once, at width one.

## The pilot record

A three-key text file. There is no comment syntax: every non-blank line is a record or the whole file is malformed, so no comment rule can silently swallow a row.

```text
slice=sign-in story, one thin end-to-end walk
stage=specifier
stage=coder
stage=cleaner
stage=hardener
stage=qa
walked=specifier|0|evidence/specifier.feature
walked=coder|0|evidence/coder-tests.log
walked=cleaner|0|evidence/cleaner-crap.txt
walked=hardener|0|evidence/hardener-mutants.log
walked=qa|0|evidence/qa-script.log
```

`stage=` declares the pipeline. `walked=` records what the pilot actually did, as stage, the exit code the stage's command returned, and the artifact it left.

Two tolerances are at work here, and they are worth keeping apart. The record *grammar* tolerates a leading BOM on the file, CRLF endings, and indentation. Stage *names* join through one documented key function: NFC, stripped, casefolded. A spelling inside that fold, such as letter case or NFD against NFC, normalises into the plain spelling's verdict. The shipped `spelling/tolerated.txt` carries all five of those forms at once — a leading BOM, CRLF, an indented line, a case variant, an NFD spelling — and exits 0 below. A spelling outside the fold misses its join and lands in the strict branch, refused twice over: once as an unwalked stage, once as evidence for an undeclared one. A compatibility spelling is the shipped case (`spelling/variant.txt`, exit 1 below). A zero-width character or soft hyphen buried in a stage name is that same class, a bare U+FEFF included, because `norm()` never strips one: a BOM inside a stage name is refused where a BOM at the head of the file is tolerated (forged, exit 1, run in the session that wrote this line). Two declarations colliding under the key are malformed, never quietly merged.

Artifact identity is the `(device, inode)` pair, so `evidence/run.log` and `evidence/./run.log` are recognised as one file. For that same reason two byte-identical copies are two files, a hole stated under *What this gate cannot see* and shipped as `copied/`.

## The gate

[`scripts/pilot-gate.py`](scripts/pilot-gate.py) consents only when every declared stage has exactly one walked entry, at exit 0, whose artifact is an existing non-empty regular file that no other stage cites.

| exit | meaning |
|---|---|
| `0` | CONSENT: the record is complete and its artifacts are on disk. `--help` also exits 0. |
| `1` | REFUSE: fewer than two stages, a stage never walked, evidence for an undeclared stage, a recorded non-zero exit, or an artifact missing, empty, not a regular file, or shared with another stage. |
| `2` | ERROR: usage, unreadable/undecodable/malformed record (a stage name over 64 characters included), an artifact that cannot be stat'ed for any reason other than absence, a dead stdout (closed outright before the run, or broken so the flush raises), or an internal failure. **An error is never a verdict.** |

### Red, green, and the codes they produced

Run from this island's directory; recompute rather than trusting these lines.

```bash
python3 scripts/pilot-gate.py scripts/fixtures/clean/pilot.txt          # exit 0
python3 scripts/pilot-gate.py scripts/fixtures/dirty/pilot.txt          # exit 1
python3 scripts/pilot-gate.py scripts/fixtures/shared/pilot.txt         # exit 1
python3 scripts/pilot-gate.py scripts/fixtures/malformed-pilot.txt      # exit 2
python3 scripts/pilot-gate.py scripts/fixtures/fabricated/pilot.txt     # exit 0
python3 scripts/pilot-gate.py scripts/fixtures/copied/pilot.txt         # exit 0
python3 scripts/pilot-gate.py scripts/fixtures/spelling/tolerated.txt   # exit 0
python3 scripts/pilot-gate.py scripts/fixtures/spelling/variant.txt     # exit 1
```

`dirty/` is the archetype, and it fails for exactly one reason: `stage 'qa' declared but never walked`, everything else evidenced. It is a well-formed record, so it goes red on content, not on syntax. `shared/` fails on `one artifact cannot be evidence for two stages`, because one file is cited under two spellings of its path. That is an identity match, not a content match. `malformed-pilot.txt` carries a `#` line and is refused as malformed with code 2, never laundered into a verdict. `spelling/` ships both directions of the key function in one directory. `copied/` consents, on purpose: it is the limit fixture for the hole below.

Dead-output-stream probes, captured (CPython would otherwise replace the status with 120):

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/pilot-gate.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # printed 2
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/pilot-gate.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # printed 2
python3 scripts/pilot-gate.py scripts/fixtures/clean/pilot.txt >&- 2>/dev/null    # exit 2
```

A dead stdout becomes `2` in both of its flavours, never a silent `0`. Broken — the write end of a closed pipe — raises in the teardown flush and upgrades the code, which is the first two probes. Closed outright before the run (`>&-`, or a parent that does `os.close(1)` before `execv`) never raises at all: CPython leaves `sys.stdout` as `None` and builtin `print()` silently returns. So the gate tests for that at entry and errors rather than issuing a verdict nobody can read. That is the third probe; the same record prints CONSENT and exits 0 with stdout open. A closed *stderr* alone is not an error, because the verdict still reaches stdout, and that run stays a verdict.

## What this gate cannot see

Per [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md), the pair proves the gate *can* refuse, not that it cannot be fooled. Two holes are left open on purpose, and each one ships as a consenting fixture rather than a description.

The first: **the gate reads the record and stats the artifacts; it never re-runs the pilot and never reads artifact content.** `scripts/fixtures/fabricated/` is a complete record over three placeholder files — `evidence/coder-tests.log` reads `TODO: pretend the tests passed`, and the qa and specifier files carry the same shape of line — and it exits 0, captured above. Closing that hole would mean content-matching for placeholder words, which would red-flag any legitimate log containing the string `TODO`, and a false-positive machine trains everyone to ignore the gate.

The second hole is the one word `cp`. **Artifact identity is `(device, inode)` and content is never read, so two byte-identical copies of one log are two files to `stat`.** Every *path-spelling* alias of one file within a filesystem is caught: the same path spelled two ways (the shipped `shared/`, exit 1), a symlink, a hardlink, a `..` traversal, a macOS case-variant path. Each of those is one inode. The last four were run against this gate in the session that wrote this line, each refused at exit 1; the first is the shipped fixture. A copy is a new inode, so `scripts/fixtures/copied/`, holding `evidence/run.log` for one stage and a byte-identical `evidence/copy-of-run.log` for the other, exits 0, captured above. The letter of the check passes. Its intent, one artifact per stage, does not. Closing it would mean digesting content and refusing two identical files, which two legitimately identical stage logs would trip: the same false-positive machine as the `TODO` scan.

So the boundary is stated instead of hidden. This gate enforces that the evidence *exists and is per-stage*. That the evidence is *real* is the reviewer's judgment, and the artifacts themselves belong in [`evidence-packet`](../../COMPANION.md#evidence-packet)'s format, which this record only indexes.

## Enforced vs advisory

- `enforced` — record completeness: every declared stage walked once at exit 0 with its own existing, non-empty artifact, unshared *by inode identity*, and `copied/` marks where that stops. `pilot-gate.py` exits non-zero otherwise, red/green/error runs captured above.
- `enforced` — malformed input, unreadable records, unreadable artifacts and a dead stdout exit `2`, never `1`; `malformed-pilot.txt` and the three stream probes above are the captured runs. Hostile spellings split into two answers, both shipped rather than asserted, because a record can be strangely spelled and still honest. The forms the docstring *tolerates* (a leading BOM, CRLF, letter case, NFD against NFC, an indented line) reach the same verdict as the plain record (`spelling/tolerated.txt`, exit 0). The forms *outside* the fold are refused (`spelling/variant.txt`, exit 1). Exit codes pass a bounded-integer regex before the one `int()` in the script, so a 5000-digit code and `NaN` are malformed rather than numbers: both were run in the session that wrote this line and both exited 2.
- `advisory` — that the slice is genuinely **thin**, genuinely **end-to-end**, and that the artifacts are genuine. No checker on this island reads artifact content or measures slice size. Those are the reviewer's call, and the two consenting fixtures, `fabricated/` and `copied/`, mark where the machine stops.
- `advisory` — the two-stage minimum (`MIN_STAGES = 2`) is this island's only tunable threshold. The other two bounds are grammar, and they hold different jobs. The 5-digit exit-code bound keeps unbounded input out of `int()`. The 64-character stage-name bound keeps a stage name to one short token: a longer name is malformed and exits 2 rather than earning a verdict, so raising that bound changes which real pipeline names the gate will accept at all (a 64-character name consents, a 65-character one exits 2; both run in the session that wrote this line). Neither bound is a judgment to retune. The minimum is a floor on shape, not a judgment of coverage. Retuning it is a threshold move under C17, and belongs to [`threshold-port`](../threshold-port/SKILL.md).
- `advisory` — re-running the gate after a pipeline change. The gate has no memory: it stores nothing between runs, hashes no pipeline, and compares a record against no predecessor, so it cannot notice that a stage was added since the last consent. That rule, stated under *The rule* and again in *Done when*, rests on discipline until a hook enforces it.
- `advisory` — wiring the gate into a pre-dispatch hook. Nothing here installs itself; hook and denylist plumbing is [`agent-guardrails`](../../COMPANION.md#agent-guardrails)'s seat.

## Boundaries

- **Tracer-bullet TICKET machinery.** Turning a slice into tickets with blocking edges, and implementing at pre-agreed seams, is [`spec-pipeline`](../../COMPANION.md#spec-pipeline)'s seat. This island owns only the pre-dispatch evidence requirement and the record that carries it; it defines no ticket, no dependency edge, no seam.
- **Batch-size doctrine.** How much to plan and how many stories per look is [`story-cadence`](../story-cadence/SKILL.md) (C19, C20, C21). This island says nothing about batch size. It says the *first* batch runs at width one.
- **Fleet sizing.** How many agents the fan-out should carry, and the communication-path math that caps it, is [`mythical-agent-month`](../mythical-agent-month/SKILL.md)'s seat (Wave 3, landing alongside this island). This island is indifferent to N; it only refuses to let N start unevidenced.
- **Parallel isolation mechanics.** Worktrees, and the rule that worktree artifacts are inadmissible until re-derived from a fresh clone, belong to [`worktree-fleet`](../../COMPANION.md#worktree-fleet). Note the interaction: a pilot evidenced only inside a worktree is not yet evidence by that island's rule.
- **The stages themselves.** What a specifier or a QA seat does is [`seat-relay`](../seat-relay/SKILL.md) (C9); whether the acceptance scenarios went red before green is [`gherkin-gate`](../gherkin-gate/SKILL.md). This island never opines on a stage's content, only on whether it was walked.

## Done when

Every line below inherits its word from *Enforced vs advisory* above; the tag is repeated here so the checklist and that section cannot drift apart.

- [ ] The pipeline the fleet will run is declared, stage by stage, in a pilot record. `enforced` as shape: fewer than `MIN_STAGES` stages exits 1, and two declarations colliding under the key exit 2. That the declared list *is* the pipeline the fleet will run is your word, not the gate's.
- [ ] One thin story has walked every one of those stages, alone, before any second agent started. `advisory` on both halves: nothing measures thinness, and the gate reads a record rather than the wall clock, so it cannot see whether a second agent had already started.
- [ ] Each stage left a real artifact of its own, and `python3 scripts/pilot-gate.py <record>` exits 0 in one run. `enforced` that the artifact exists, is non-empty, and is unshared by inode; `advisory` that it is *real* (`fabricated/`, exit 0) or *its own* rather than a copy (`copied/`, exit 0).
- [ ] The gate is re-run after any change to the pipeline, because a changed pipeline has a new unwalked stage. `advisory`, as is the human read below: the gate holds no memory of the previous pipeline and cannot ask for this itself.
- [ ] A human has looked at the artifacts. `advisory` by construction, because the gate cannot tell a real log from a fabricated one and says so.

**Build it twice: one slice alone with its evidence captured, then the fleet. A fan-out over an unwalked path does not spread the risk, it buys the same mistake N times.**
