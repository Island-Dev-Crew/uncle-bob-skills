---
name: mutant-hunt
description: The merciless hardener gate - prove a story's tests can fail by injecting single-operator mutants into the diff's covered lines and demanding zero non-equivalent survivors on the diff, never a global score, under a runtime budget cap. Reach for it after a story's suite goes green and the question becomes whether the tests would actually catch a break - "run mutation testing on this diff", "harden this story", "any surviving mutants", "would these tests catch anything". Differentiator - this island owns only the metric and its budget; excusing an equivalent survivor belongs to mutant-excusal-ledger, and the gate's loop plumbing belongs to agent-guardrails and archipelago.
---

# Mutant Hunt: zero survivors on the diff

A passing suite is a claim; a killed mutant is evidence from a check that could have failed. This island is the hardener's pass (C7): flip one operator at a time in the story diff, run the suite against each mutant, and require that every non-equivalent mutant on the diff dies. The ledger quote that defines the gate: *"for each of those flips, it runs your entire test suite and expects the test suite to fail… if it doesn't fail, well, that's a surviving mutant and it must be killed"* (C7).

## The mechanism

Grounded in [`research/mutation-testing.md`](../../research/mutation-testing.md):

- A **mutant** is one small syntactic change: sign flips (`+`→`-`), relational flips (`<`→`<=`, `==`→`!=`), conditional negation, return-value default replacement — the standard operator families PIT still ships.
- **Kill vs survive**: the suite fails on the mutant → killed; the suite passes → a surviving mutant, proof the change is unobserved by any assertion. **Mutation score** = killed ÷ total.
- Lineage: Lipton's 1971 class paper; DeMillo, Lipton & Sayward, *IEEE Computer* 1978. Cost shelved it for decades — an overnight run circa 2000, now *"maybe it took it 30 minutes instead of an overnight run and then it would plug all the holes"* (C7).
- Scale proof: Google runs mutation diff-scoped (covered, non-arid lines only) at ~2B LOC; incremental modes (PIT incremental analysis, Stryker incremental) turn a ~30-minute run into under 2 minutes on a typical PR. Both claims: [`research/mutation-testing.md`](../../research/mutation-testing.md).

## The gate contract — the diff, never a score

1. **Scope = story diff ∩ covered lines.** The diff's new-side line ranges are computed mechanically (script below); for the coverage intersection, run the tool in its coverage-targeted mode (PIT's default; Stryker via `coverageAnalysis`) so only covered lines are mutated — coverage-targeting is an acceleration mode a tool offers, not a universal property. Where the tool lacks that mode, intersect the diff ranges with the coverage report before feeding the filter ([`research/mutation-testing.md`](../../research/mutation-testing.md)). Docs-only diffs produce an empty scope and the gate passes vacuously — record the empty-scope exit as the evidence.
2. **Requirement = zero surviving non-equivalent mutants inside that scope.** A global score is the wrong instrument here: a 92% repo-wide score averages the story away and says nothing about whether *this* change's tests can go red. Gate on the diff.
3. **Every survivor returns to the coder as a kill-task** (format below). The gate holds until each survivor is killed by a new red-capable test or excused in the ledger island — never excused here.

## Scope is mechanical

[`scripts/diff-scope.sh`](scripts/diff-scope.sh) emits the diff's mutable line ranges, one `path:start-end` per added/modified hunk (new-side numbering; pure deletions skipped):

```bash
scripts/diff-scope.sh <base-ref> [head-ref] [repo-dir]
# exit 0 scope emitted · exit 1 empty scope (vacuous pass, record it) · exit 2 usage/git error
```

Feed the ranges to the language-native mutation tool's file/line filter. Run the tool in incremental or diff mode; whole-repo runs stay outside the loop. Tool-per-language will be `gate-toolchain`'s concern — an unbuilt roster target with no island yet. Until it exists, pick from the tool list grounded in [`research/mutation-testing.md`](../../research/mutation-testing.md): pitest (JVM), Stryker (JS/TS/C#), mutmut (Python), cargo-mutants (Rust), gremlins (Go).

## Survivors become kill-tasks

Each survivor goes back to the coder as one concrete, falsifiable task:

```text
KILL-TASK  src/pricing.ts:41
  operator   relational flip
  original   if (qty >= bulkMin)
  mutant     if (qty > bulkMin)
  task       write a test that fails on this exact change
  proof      rerun this mutant; the new test goes red on the mutant, green on the original
```

The proof line is the point: a kill-task is done when rerunning the *same* mutant shows the new test failing. "I added a test near that line" is a claim; the rerun is the evidence.

## The budget cap

The gate exists inside the productivity margin (C5): *"as long as you can keep the margin of productivity higher than a human, you're still ahead of the game"*. A mutation pass that eats the margin loses the game it was built to win, so every run carries a wall-clock cap:

- Set the cap before the run — a sane default is a small multiple of the story's own build+test time; incremental/diff modes make typical PR runs minutes, not hours ([`research/mutation-testing.md`](../../research/mutation-testing.md)).
- On cap overrun, stop and report exactly which scope ranges ran and which were cut. A truncated run is a **partial verdict on the ranges it covered** and `unverified` on the rest — say so plainly; a truncated run never reports as a full pass.

## Verify → fix → reverify

1. Compute scope (`diff-scope.sh`); empty scope → vacuous pass, record the exit, done.
2. Run the mutation tool in diff/incremental mode over the scope, under the cap.
3. Zero non-equivalent survivors → gate passes; hand the report onward (boundaries below).
4. Survivors → emit one kill-task each; coder writes the killing tests.
5. Rerun the same mutants. Loop 4–5 until zero survivors remain unhandled — each one either killed or excused *in the ledger island*, never silently dropped.

Done means: every mutant in scope is killed, excused-with-justification (ledger), or explicitly reported `unverified` under a cap overrun. No fourth state.

## Boundaries — what this island owns and what it points at

- **Metric content only.** The plumbing that wires this gate into a loop the agent cannot exit — hook installation, gate ordering, block-vs-warn enforcement — belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails) and [`archipelago`](../../COMPANION.md#archipelago). This island defines what the gate measures and demands; those islands decide where it sits and what it blocks.
- **Evidence goes to [`evidence-packet`](../../COMPANION.md#evidence-packet)** — the same links `crap-gate` uses. The bundle: the scope output, the tool's report (survivor list, kill count, runtime), and the cap verdict, hashed so a reviewer recomputes instead of trusting.
- **Equivalence excusals belong to [`mutant-excusal-ledger`](../mutant-excusal-ledger/SKILL.md).** Equivalence is undecidable (Budd & Angluin 1982) and 4–39% of mutants are equivalent in practice ([`research/mutation-testing.md`](../../research/mutation-testing.md)), so a literal 100% raw kill is unreachable — that is exactly why the excusal path exists and why it lives in its own island with a written justification per excusal. **This island never excuses a survivor itself.** A survivor leaves here only as a kill-task or as a referral to that ledger.

## Enforced vs advisory

- `enforced` — scope computation: `diff-scope.sh` is deterministic, syntax-checked, and fails closed (exit 1 on empty scope, exit 2 on git/usage error).

**Red/green proof.** The gate's own known-dirty/known-clean pair lives beside it in [`scripts/fixtures/`](scripts/fixtures/mkrepo.sh) (shared `base/`, two heads). Run from this island's directory, these two commands gave these exit codes:

```bash
scripts/diff-scope.sh HEAD~1 HEAD "$(scripts/fixtures/mkrepo.sh dirty)"   # exit 1 — deletions-only diff, empty scope (RED)
scripts/diff-scope.sh HEAD~1 HEAD "$(scripts/fixtures/mkrepo.sh clean)"   # exit 0 — emits pricing.js:3-3 and pricing.js:6-8 (GREEN)
```

The same pair run through [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s `prove-gate.sh` printed `ACCEPTED` at exit 0. Bad-ref input exits 2. Re-run the pair on every change to the script.

- `enforced` — island structure: `unclebob/scripts/validate-island.py` gates this file's frontmatter, sidecar, ledger citations, and line budget at exit 0.
- `advisory` at v0 — the mutation run, the zero-survivor requirement, and the budget cap: no per-language runner ships here yet. Run the language-native tool from the list above (`gate-toolchain`, the roster island that will own tool selection, is not built yet) and treat *its* exit code as the gate; a verdict claimed without a tool report is `unverified`. A later wave may add a runner harness that promotes these to enforced; until it exists, this island says advisory and means it.

**No authority without evidence. A green suite is a claim; a killed mutant is the proof — zero survivors on the diff, inside the margin.**
