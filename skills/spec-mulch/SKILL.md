---
name: spec-mulch
description: Treat a story spec as scaffolding that mulches on merge — it exists to launch one story through the relay, then is deleted; the durable specification is the end result plus its standing gates (gherkin, tests, the dependency fence), never the plan doc. Reach for it when a merged story's spec file still sits in the repo, when a specs folder is proposed as living documentation, or when someone says "keep the spec updated", "archive the specs", or "can I delete the spec now". Differentiator - it mulches plan documents, not code (throwaway code is prototype's seat), and it is a named divergence from spec-pipeline's publish-the-spec rule.
---

# Spec Mulch: the spec dies on merge

A story spec is scaffolding, not source. It exists to launch exactly one story through the relay; the moment that story merges, the spec has done its whole job and comes down — *"the specifications are ephemeral… they go away"* (C22, [ledger](../../01-CONCEPT-LEDGER.md)). What endures is never the plan doc but the end result and the standing gates that hold it in shape: *"I look at the end result and say, well, that is the specification"* (C22). This island encodes that lifecycle: a mulch-on-merge marker every spec carries from birth, and a check that goes red while any launched story's scaffolding survives.

## Two boundaries, stated up front

- **Explicit divergence from spec-pipeline.** [`spec-pipeline`](../../COMPANION.md#spec-pipeline) Stage 1 ends with the spec *published* where the repo keeps specs — a durable artifact. This pack diverges from that published-spec rule, deliberately and by name: under the mulch doctrine the published spec has a lifespan of exactly one story. Publish it to launch, mark it to die, delete it on merge. Everything else about Stage 1 stays spec-pipeline's; only the artifact's fate is overridden here.
- **Throwaway code is not this island.** The throwaway-artifact move for *code* is [`prototype`](../../COMPANION.md#prototype)'s seat — and prototype's verdict runs the other way, keeping its disposable code as a runnable primary source on a branch. Spec Mulch owns throwaway *plan documents* only, and keeps a dead spec nowhere, because the durable truth already exists in a stronger form.

## What survives the mulch

Mulch, not shred: the spec's nutrients return to the standing artifacts before the file dies.

| From the spec | Durable home |
|---|---|
| Acceptance criteria | the Gherkin scenarios — already executable, already gating |
| Behavior detail | the unit tests the coder seat wrote |
| Structural intent | the dependency fence's direction file |
| A decision worth remembering | an ADR — the one prose survivor, recording *why*, never *what to build* |

The end result plus these gates IS the specification (C22). If deleting the spec would lose something, that something is not yet in a durable home: promote it first, then delete.

## The mechanism

1. **Birth**: the story spec carries the line `MULCH-ON-MERGE: <story-id>` at line start (frontmatter or the first lines — anywhere greppable).
2. **Launch**: the relay runs off the spec. Agents read all of it — *"if you pass a spec to an agent they're probably going to read it"* (C24) — so write it for the launching agent, at whatever length the story needs.
3. **Merge time**: promote the survivable nutrients (table above), delete the spec file, then run the check:

```bash
<this-skill-dir>/scripts/mulch-check.sh <repo-dir>              # whole tree
<this-skill-dir>/scripts/mulch-check.sh <repo-dir> <story-id>   # this story only
```

Red lists the survivors; promote, delete, re-run until green. Green means every launched story's scaffolding is gone.

## The deeper resistance: the missing-source itch

*"There is no equivalent to source code. We humans wrote the source code. So that was the final specification. Well, that doesn't exist anymore."* (C22). Whoever feels that absence reaches for a persistent spec corpus — a specs folder kept as "living documentation," a human-readable stand-in for the source nobody writes now. Two facts break the move:

- **Reading asymmetry** (C24): agents read what you send, but *"the things that the agents write, the humans don't read."* A retained spec written for an agent audience has no human reader and no agent job left.
- **Un-mulched specs drift silently**: the SDD tooling wave's own reviewers found spec/implementation divergence going undetected (Kiro, per [research](../../research/atdd-gherkin-agile.md)). A stale spec doesn't just sit; it lies. The same research file's ruling on the transcript: "the spec's job is to launch one story through the gauntlet, then die."

The itch for a what-does-this-system-do document is legitimate; scratch it with the Gherkin suite, the fence file, and a green run — artifacts that fail loudly the moment they diverge, which prose never does.

## Enforced vs advisory (v0)

- **Enforced when run**: [`scripts/mulch-check.sh`](scripts/mulch-check.sh) is deterministic — it scans every text file under the target (any extension; binaries and `.git` skipped), exits 1 while any line-start-marked spec survives, exits 0 when clean, prose mentions of the marker ignored; the story filter matches the story id as a whole token, never a substring.

**Red/green proof** — the gate carries its own [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) acceptance in the repo. Run from `scripts/`:

```bash
./mulch-check.sh fixtures/dirty-repo   # exit 1 — lists specs/story-17-checkout-tax.txt
./mulch-check.sh fixtures/clean-repo   # exit 0 — the same tree after the mulch
```

The two trees differ by exactly one file: the surviving marked spec (a `.txt`, so the extension-blind scan is under test too). The ADR sits in *both* trees and opens a line with a backticked `MULCH-ON-MERGE: story-17`, yet is never listed — green here is the line-start anchor working, not the string being absent. On the dirty tree the story filter also separates: `story-17` exits 1, `story-1` exits 0.

- **Advisory at v0 — the merge block itself**: no hook or CI job wires the check into merges today, so run it manually at merge time. A later wave lands the pre-merge hook through `agent-guardrails` plumbing; until then, calling this a blocked merge would be laundering advisory into enforced.
- **Advisory**: marker placement, one-spec-one-story sizing, and the resistance to persistent spec corpora — judgment calls, not gates.

## Done when

- The merged story's spec file is deleted and `mulch-check.sh` exits green over the repo (or the story id).
- Every nutrient the spec carried is findable in a durable home — a scenario, a test, a fence rule, or an ADR.
- The loop ran explicitly: check → red lists survivors → promote → delete → re-check → green. It repeats at every merge; the check is idempotent.

**The spec launches the story and dies; what merged — and the gates that hold it — is the specification.**
