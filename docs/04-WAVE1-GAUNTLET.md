# Wave 1 — fusion and gauntlet record

**Built:** 2026-08-19 · **Islands:** 20 of 20 · **Location:** [`skills/`](../skills/) · **Status:** all 20 mechanically green (240/240 checks); 19 cleared a blind critic; `arch-lens` failed three rounds before its true root cause was found — a defect in the validator itself, not the island.

Every island was authored by a builder seat under the authoring canon, then judged by a **blind critic** that never saw the build prompt — only the island's roster contract and the evaluation spec. Critics were instructed to falsify, and did.

## The gate that judged the gates

[`scripts/validate-island.py`](../scripts/validate-island.py) enforces 12 mechanical checks per island (F1–F11): frontmatter parses, `name` matches folder, no angle brackets, description within 60–1024 chars, sidecar interface complete, body cites the ledger, body states enforced-vs-advisory, body ≤250 lines, scripts pass `bash -n` / `py_compile`.

Per the pack's own `known-dirty-fixture` doctrine, the validator was not trusted until it failed: it goes **red with 6 failures** on [`scripts/fixtures/bad-island`](../scripts/fixtures/) and **green** on `good-island`. Both fixtures ship. Final sweep: **240 checks, 0 failed, 20 islands.**

## Verdict per island

| island | critic r1 | after fix | final |
|---|---|---|---|
| boredom-dividend · dependency-fence · essence-pointer · margin-ledger · mutant-excusal-ledger · priority-zone · qa-script-seat · specifier-seat · story-cadence · structure-interrogation · thrash-watch · threshold-port · trajectory-hygiene | PASS | — | **PASS (r1)** — 13 islands |
| crap-gate | FAIL | PASS | **PASS (r2)** |
| known-dirty-fixture | FAIL | PASS | **PASS (r2)** |
| mutant-hunt | FAIL | PASS | **PASS (r2)** |
| seat-relay | FAIL | PASS | **PASS (r2)** |
| spec-mulch | FAIL | PASS | **PASS (r2)** |
| steering-audit | FAIL | PASS | **PASS (r2)** |
| arch-lens | FAIL | FAIL | **FAIL again in round 3 — root cause found and fixed; see below** |

27 critic judgments, 19 pass / 8 fail. 54 agents, ~6.9M tokens.

## What the critics actually caught

The gauntlet earned its keep — every defect below is one a self-review would have missed, and each was verified fixed against the files, not taken on the fixer's word:

- **`steering-audit` — laundered evidence (S4).** The body claimed its checks were "demonstrated against a known-bad fixture in this island's own construction." No fixture existed anywhere. The critic proved the absence by search, noting the script's behavior was genuinely correct — but *a completed demonstration written as fact when it never happened* is the exact laundering [`CONTEXT.md`](../CONTEXT.md) forbids. Fixed by actually shipping the fixtures ([`skills/steering-audit/scripts/fixtures/`](../skills/steering-audit/scripts/fixtures/), 3 files), which the round-2 critic re-ran independently.
- **`crap-gate` — invented provenance (S5).** Claimed the "Alberg" misattribution came from auto-caption garbling. Grep proved "Alberg" appears nowhere in the transcript, SRT, or the ledger's garble registry. The correction was right; the *story about where the error came from* was fabricated. Now states only what the research grounds.
- **`seat-relay` — over-broad enforcement claim (S4).** Asserted every seat's exit gate is decided by a tool's exit code, while its own table showed seat 1's gate is partly prose judgment (the QA procedure only becomes executable at seat 5). Now scoped honestly. The same critic also caught that the island flagged two user-invoked neighbors but silently routed to a third (`gauntlet-loop`) that no agent can fire — a silent no-op under the authoring canon.
- **`mutant-hunt` — dead link + overstated research (S8, S5).** Linked twice to `gate-toolchain`, an unbuilt Wave-2 island, and claimed universally that "the mutation tool mutates only covered code" — true for PIT's default, false for Stryker, which reports uncovered mutants as survivors and would have produced false blocks under this gate's zero-survivor rule.
- **`known-dirty-fixture` — a command that could not run (S6);** **`spec-mulch` and `dependency-fence` — exit-code claims that did not match script behavior (S4).**

## What I found beyond the critics

Independent verification after the workflow surfaced three issues no round-1 critic caught:

1. **Cache residue in 7 islands** (one critic caught it in `arch-lens` alone): `scripts/__pycache__/` holding `.pyc` bytecode, which the fleet installer would copy to all four seats and fold into the signed tree manifest.
2. **`arch-lens` residual defects**, repaired by hand: two rules carried no enforced/advisory label while their siblings did. Because the fixer must not be the judge, a fresh blind critic re-judged in round 3.
3. **A quote-fidelity defect in the ledger itself** — the source of truth every island cites. C4 rendered Bob's stuttered *"you must you must change the code"* as smoothed prose inside a verbatim quote. Corrected with `[sic]`. The islands were clean: each quotes a fragment that is literally verbatim. A mechanical sweep of every distinctive conversational phrase used across the 20 islands found **all of them present in the transcript** — no island invented a quote.

## Round 3: the critic that falsified my own fix

The `arch-lens` round-3 critic failed the island again, and was right. My cache fix — delete the folders, add a `.gitignore` — was **structurally incapable of working**, and the critic proved it three ways:

- **It regenerates.** [`scripts/validate-island.py`](../scripts/validate-island.py) ran `python -m py_compile` for check F11, which *writes bytecode into the island it is validating*. Every validation run recreated what I had deleted. Confirmed independently: sweep to 0, one validator run, back to 14 artifacts.
- **`.gitignore` was the wrong lever.** The fleet installer copies from the filesystem, not from git — and the whole pack is untracked, so git was never the leak path.
- **The installer does not filter.** `scripts/install.py` calls `shutil.copytree` at lines 749, 1237, 1276 with no `ignore=` argument.

The real fix: F11 now checks syntax with an **in-process `compile()`** and writes nothing. `py_compile` could never be silenced with `-B` or `PYTHONDONTWRITEBYTECODE`, because writing bytecode is precisely its purpose — an assumption that looked right and was wrong until it was run. Proven both directions: a full 20-island sweep now regenerates **zero** artifacts, and F11 still fails a deliberately broken `.py` (`syntax error: invalid syntax`).

The critic's other two catches were also real and are fixed: a rule stated twice (once unlabeled), and an advisory spot-check whose documented command reported **green on a file that does not exist** — the exact failure it existed to catch. The replacement was verified across all four cases (clean 0, absolute-URL 1, protocol-relative 1, missing 1).

## Wave 1.1 — proving the gates, and the bypasses it exposed

Ten islands lacking fixtures went through a build-then-blind-verify fleet: an author built the fixture pair and ran it; a **separate verifier that did not build them** re-executed the proof and tried to falsify it. All ten proofs held — and the verifiers found that three gates, while correctly separating their own fixtures, **could be bypassed by inputs the fixtures never tried.** Each was reproduced by hand before being fixed:

- **`qa-script-seat` / `qa-bind-check.sh` — the gate did not bind.** Its STORY check was line-anchored, but the QA-DOC and QA-SHA256 checks used unanchored `grep -F`, so three forged scripts passed: one whose "headers" existed only inside an `echo` argument and a shell variable (**no binding headers at all**), one bound to `<doc>.OLD-REVISION`, and one whose hash was the real hash plus a suffix. Its SKILL.md claimed the check "exits non-zero when the headers are missing" — false as written. All checks are now line-anchored end to end, and the QA-DOC header is compared by **resolved path**, which also fixed a false-RED where `./doc.md` and the absolute path were rejected as different bindings. Reproduced before and after: both forgeries pass on the old script, both are rejected by the new one, and the shipped fixtures still separate.
- **`spec-mulch` / `mulch-check.sh` — regex injection in the story filter.** The story id was interpolated raw into a `grep -E` pattern, so a metacharacter turned the filter into a pattern: `story-1.2` silently matched a `story-142` spec — the exact false-positive the code's own comment promised to prevent. The id is now escaped; verified that `story-1.2` no longer matches `story-142`, that `story-142` still matches itself, and that the prefix `story-14` correctly does not match.
- **`margin-ledger` — colliding exit codes.** A missing or unreadable ledger exited 2, the code its SKILL.md reserves for "fail-closed on an empty or malformed ledger", so running from the wrong directory produced a path error indistinguishable from a legitimate verdict. IO and usage errors now exit 3; verified across all five paths (clean 0, breach 1, empty 2, missing file 3, bad `--floor` 3).

Two gates also carried the same `py_compile` cache defect as the validator; both now check syntax without writing. `arch-lens` — held out of the fleet while under review — got its fixture pair last: the dirty graph is deliberately valid JSON of the correct shape so it clears G1/G2 and goes red only on the structural checks the gate exists to catch (undeclared parent, self-edge, pathless module, bad path), because a fixture failing for an unrelated reason proves nothing.

The remaining verifier notes were documentation, not defects — copyable command blocks that relied on prose for their working directory, now stated in the blocks themselves — plus one honest disclosure worth keeping: `specifier-seat`'s Given/When/Then checks are file-global greps, not scenario-scoped, and its enforced claim is already worded exactly that narrowly.

## Open finding — not mine to fix on this branch

`scripts/install.py` copies skill folders with no ignore filter, so any `__pycache__/` or `.pyc` present on disk ships to all four fleet seats and enters the signed tree manifest. Canonical `skills/` is clean today, so nothing is currently leaking; the exposure appears the moment a canonical skill ships a `.py` script that anyone executes. One-line fix: pass `ignore=shutil.ignore_patterns("__pycache__", "*.pyc")` to the `copytree` calls at lines 749, 1237, 1276. **Left untouched deliberately** — that file is hardened 2.0.3 code under active Codex review, and a silent edit there could collide with that work. Jon's call.

## Honest state of the pack

- `enforced` today: the 12 mechanical validator checks, run over all 20 islands, reproducible by anyone (`python3 scripts/validate-island.py skills/*/`).
- `enforced` today, additionally: **all 12 gate scripts now ship a red/green fixture pair and every one was re-executed** — 12/12 exit non-zero on their dirty fixture and 0 on their clean one, and running all of them leaves zero cache artifacts behind. The pack's own `known-dirty-fixture` law is satisfied: no gate is trusted on assertion, each is trusted because it was watched failing.
- `advisory` today: most in-island rules — these are v0 islands, and each says so in its own enforced-vs-advisory section.
- Not yet done: registry entry, fleet distribution, cross-family review at a fixed SHA, Waves 2–3. Nothing is committed — the pack is untracked on `v2.0.3-hardening`.

**No authority without evidence. The critics falsified; the fixes were verified against the files; what remains unproven is named above.**
