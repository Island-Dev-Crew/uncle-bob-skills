---
name: boyscout-ratchet
description: Baseline-and-ratchet on touched files - every file an agent touches must leave measurably no worse than it arrived (CRAP score, cyclomatic complexity, coverage), with crap4j's project-allowance pattern so a legacy repo can adopt a gate it cannot pass today. Reach for it when an absolute quality gate would fail the whole repo on day one, when adding a no-regression check to a diff, or when the user says "boy scout rule", "ratchet the metrics", "no worse than baseline", or "we can't turn the gate on yet". Differentiator - this island owns the relative no-regression discipline and the legacy-adoption path; the CRAP formula, its threshold regimes, and the absolute per-function ceiling belong to the crap-gate island, whose numbers this one consumes.
---

# Boy Scout Ratchet: nothing leaves worse than it arrived

The gate you cannot pass today is the gate you never turn on. A legacy repo meets an absolute ceiling with three hundred violations, someone sets the threshold to "whatever we score now," and the gate becomes a thermometer. The ratchet is the way out: measure once, freeze that number as a **baseline**, and require only that the **diff** move in the right direction. Day one costs nothing and the repo can only improve.

Uncleaned agent output degrades the next agent's run, which is why the pack cares: *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). Bob's cleaning loop measures with CRAP: *"why don't you run crap over everything you've just done and it would run crap and then it would clean up the code"* (C6). This island supplies the **relative** verdict that loop needs, on a codebase where the absolute one is out of reach. Non-transcript ground: [`crap-metric.md`](../../research/crap-metric.md).

## The record

One row per file, committed to the repo: a path key and three metric columns, four tab-separated fields.

```
path <TAB> worst_crap <TAB> max_complexity <TAB> coverage_pct
```

The path is the join key, so `ratchet.py` puts it through one documented key function (`key_of`) before comparing. `./api/x.py`, `api//x.py`, `api\x.py` and `api/x.py/` are one file. Without that step, a cosmetic variant from a different upstream step misses its baseline row, falls to the lenient new-file branch, and a regression rides the ceiling. The same key function also makes two spellings of one file inside one record collide as a duplicate (exit 2) instead of counting twice.

A leading `#` opens a comment **only on a line carrying no tab**. The anchor is the tab, not the `#`. So a four-field row whose path legitimately begins with `#` (Emacs' `#autosave#`) gets judged rather than silently dropped from the record, because a dropped row is a false green.

`key_of` reduces those forms and no others, so the rule is **join or refuse**. A key it cannot reduce to the baseline's repo-relative form exits 2 instead of reaching the new-file branch: absolute (`/repo/api/x.py`, routine istanbul/jest `coverage-final.json` output), drive-prefixed (`C:\api\x.py`), or tree-escaping (`../api/x.py`).

The other half of the hazard is two spellings that a filesystem calls one file but a dict does not. They differ only by letter case (`API/Router.py` vs `api/router.py`), by Unicode form (NFC versus the NFD a macOS tree walk hands back), or by a trailing dot or space (`api/router.py.`, which Windows erases when it stores the name). All three are refused across both records at once, with both spellings named and escaped.

No exact-match pass runs ahead of that check, and none is needed. A record that spells every path one way, all caps included, has no fold partner and joins normally, so only a *mixture* is refused. That covers the rare case-sensitive tree genuinely holding both, where the gate names the collision rather than guessing which file you meant.

A fourth spelling joins nothing at all. A key carrying an invisible codepoint is refused on sight, and the refusal names the codepoint: the UTF-8 BOM that PowerShell's `Out-File`, .NET's `StreamWriter` and Excel's CSV export all write by default, a zero-width space, an NBSP. (A BOM at the *head* of a record is consumed by the `utf-8-sig` read instead of becoming part of a key, so ordinary Windows output simply joins.) Relativize and spell paths one way upstream. That refusal is the difference between a gate and a gate-shaped hole: unjoinable keys are exactly where a regression on all three axes would otherwise report green.

**Per-file grain, deliberately** (advisory: no check enforces the grain). [`crap-gate`](../crap-gate/SKILL.md) gates per *function*, which is the metric's native grain and the right repair target. A ratchet needs something else, an identity that survives a refactor, and functions get renamed, split, and inlined by exactly the work the ratchet is meant to encourage. A file survives that. So the row carries the file's worst function score, its max complexity, and its coverage: three worst-case summaries, chosen so that improving them cannot hide a decline underneath.

## The mechanic

1. **Record the baseline** from a full run, and commit it. It is a checked-in artifact, reviewable in a diff like any other.
2. **Compare on the touched set only.** The current record lists the files this change touched; everything else is out of scope, which is what keeps the loop fast enough to fire after every task.
3. **A regression fails.** CRAP up, complexity up, or coverage down against that file's baseline row. Equal passes; better passes. The direction is the whole point.
4. **New files have no baseline to ride**, so they answer to the absolute ceiling instead: crap-gate's number, passed in, never redefined here.
5. **Rewrite the baseline downward only**, on green, as part of the same commit. A baseline refreshed after a red run is a gate switched off with extra steps (advisory; see the boundary on hook plumbing below).

## The legacy budget

crap4j shipped this pattern with its own numbers: threshold 30, with a project-level allowance of **at most 5% of methods over it** ([`crap-metric.md`](../../research/crap-metric.md)). Ported here, the budget is a second, absolute check that runs beside the ratchet: across the merged project view, the share of files over the ceiling may not exceed `--budget`. That is what lets a repo with a `legacy/report_writer.py` scoring 41 turn the gate on this afternoon.

The two knobs mean different things and belong to different islands. `--ceiling` is the per-function bar from [`crap-gate`](../crap-gate/SKILL.md), quoted here. `--budget` is this island's own: the size of the exception pocket, and the honest admission that the pocket exists.

The budget is itself a ratchet, by construction. Touched files may not get worse and new files must clear the ceiling, so the over-ceiling set can only shrink. Tighten the number as it does. Leaving `--budget` at its opening value forever converts an adoption ramp into a permanent allowance. That is the failure mode this island exists to prevent, and no script here detects it (advisory).

## Running it

[`scripts/ratchet.py`](scripts/ratchet.py) compares two records and gates on its exit code. It computes no metric of its own; it consumes numbers produced upstream:

```bash
python3 scripts/ratchet.py --baseline baseline.tsv --current touched.tsv --ceiling 6 --budget 5
```

Exit codes carry distinct meanings, so a broken pipeline can never read as a pass: **0** green, **1** a real verdict (regression, new file over ceiling, or budget bust), **2** usage/IO/malformed input. Those three are the only codes a gate run produces. `--help` runs no gate, and it is the one invocation that exits 0 without judging anything.

Direct probes prove each of these fail-closed cases, and every one of them exits 2:

- an empty or comment-only record, or a duplicate row for one path;
- a non-numeric or `nan` value: a `nan` would win every comparison silently, so the parser's anchored `^[0-9]+(\.[0-9]+)?$` rejects it;
- a digit run long enough that `float()` overflows it to `inf`, the same silent switch-off wearing a spelling the regex admits;
- coverage over 100, or a space-separated line;
- a path key that is not repo-relative, or one that collides with another only by case, Unicode form or a trailing dot;
- a key carrying an invisible codepoint (a mid-file BOM, a zero-width space, an NBSP) that would join nothing;
- a key holding a bare CR or U+2028: both split the line, and the fragment left of the break carries no tab, so it cannot be four fields;
- an unreadable baseline, or a record that is not valid UTF-8 (latin-1 or UTF-16). A `UnicodeDecodeError` is a `ValueError`, not an `OSError`, so it is caught explicitly rather than crashing out on the code reserved for a verdict;
- a `--ceiling` or `--budget` that is out of range or non-finite.

No unhandled exception can wear a verdict's code either: the run is wrapped, and any crash exits 2. A closed stdout exits 2 as well, because `print()` to a `None` stdout is a silent no-op, and a verdict that reached nobody is not evidence. So does a broken pipe, the same fault one fd state further along (`ratchet.py … | head -1`). Catching the `BrokenPipeError` is not enough on its own: the bytes left in the buffer are flushed again at interpreter shutdown, and that second raise replaces the status with **120**. So the failed stream's fd is redirected to the void before the handler returns, and the 2 is what the pipeline reads. Both streams, not just stdout: a broken *stderr* turned the error message itself into a 120 until `report()` did the same.

The flags carry the record fields' `nan` hazard too. argparse parses them with `float()`, which accepts `nan`, `inf` and `1e400`. A non-finite ceiling makes every comparison False. It would print `at or under ceiling nan` over a 9.10 score and turn this island's own red fixture green, so both flags are checked with `math.isfinite` rather than left to a range comparison that only rejects them by accident:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-new-over-ceiling.tsv --ceiling nan --budget 5
# input error: --ceiling must be a finite positive number, got nan   → exit 2
```

`--ceiling inf`, `--ceiling 1e400`, `--budget nan` and `--budget inf` each exit 2 the same way.

**Red/green proof.** The gate earned its `enforced` line by being watched failing, the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Recompute from this island's directory:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-regression.tsv --ceiling 6 --budget 5   # exit 1
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/clean-improved.tsv --ceiling 6 --budget 5     # exit 0
```

The dirty fixture is well-formed and inside budget, so it fails on the ratchet alone. It fails for the sharpest possible reason: `api/router.py` moves 3.20 → 5.40 with coverage 95% → 78% and is still under a ceiling of 6. The absolute per-function gate waves it through, and only the ratchet catches it. The clean fixture carries the equality case (`web/view.py` unchanged, passes) and a new file at 4.00 under the ceiling, proving the gate discriminates rather than rejecting everything. A third fixture covers the new-code path:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-new-over-ceiling.tsv --ceiling 6 --budget 5   # exit 1
```

It reports `NEW-OVER` and `BUDGET-BUST` together: a new file over the ceiling both breaks the new-code bar and eats the pocket. A fourth covers the join key:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-path-variant.tsv --ceiling 6 --budget 5   # exit 1
```

It carries the dirty fixture's exact regression spelled `./api/router.py`, ordinary output from coverage.py, `go test -coverprofile` or istanbul. Normalized, it joins its baseline row and reports `WORSE api/router.py`. Unnormalized, it read as new code and passed under the ceiling. `api//router.py` and `api\router.py` exit 1 the same way. A fifth covers the other half of that rule, the spelling the key normalization *cannot* reduce:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-abs-path.tsv --ceiling 6 --budget 5   # exit 2
```

It is the same regression again at `/repo/api/router.py`, worse on all three axes (crap 3.20 → 5.99, complexity 4 → 6, coverage 95% → 10%) yet under a ceiling of 6. That is precisely the row that reported `ok new` and exit 0 before this refusal existed. `C:\api\router.py` and `../api/router.py` exit 2 the same way, on either record.

Six more fixtures close holes a blind critic forged against this gate, each captured failing:

```bash
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-case-variant.tsv  --ceiling 6 --budget 5    # exit 2
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-nfd-variant.tsv   --ceiling 6 --budget 5    # exit 2
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/bad-encoding-latin1.tsv --ceiling 6 --budget 5    # exit 2
python3 scripts/ratchet.py --baseline scripts/fixtures/dirty-inf-value.tsv \
  --current scripts/fixtures/dirty-regression.tsv    --ceiling 6 --budget 5    # exit 2
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-hash-path.tsv     --ceiling 6 --budget 5    # exit 1
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/dirty-bom-path.tsv      --ceiling 6 --budget 5    # exit 2
python3 scripts/ratchet.py --baseline scripts/fixtures/baseline.tsv \
  --current scripts/fixtures/clean-improved.tsv --ceiling 6 --budget 5 1>&-    # exit 2
```

Every one of them was a false or mis-coded green first. The case variant, the NFC/NFD pair, the `#`-prefixed row and the BOM'd record each reported exit 0 on a file that had regressed or blown the ceiling. The BOM one did it on the `dirty-abs-path` regression in a fourth spelling, worse on all three axes and still under the ceiling. The `inf` baseline reported exit 0 with the crap axis silently switched off. The latin-1 record crashed out on exit 1, the code reserved for a real verdict, sending a CI consumer to repair code over an encoding fault. The closed stdout returned 0 having printed nothing at all. Deleting any fixture returns the gate to `unverified`.

The broken pipe is the last one. It needs a reader rather than a file, so it is a probe rather than a fixture, captured at exit 2 where it returned 120 before fd 1 was neutralised. The probe **exits with the code it is reporting** and prints nothing itself: written as a heredoc that only printed the child's status, the block annotated exit 2 while the command itself returned 0 — an annotation no run had produced, and one no line-based verifier could re-run. It stays silent because a probe of a dead output stream must not itself depend on a live one.

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);p=subprocess.Popen([sys.executable,"scripts/ratchet.py","--baseline","scripts/fixtures/baseline.tsv","--current","scripts/fixtures/clean-improved.tsv","--ceiling","6","--budget","5"],stdout=w,stderr=subprocess.PIPE);os.close(w);_,err=p.communicate();sys.exit(p.returncode)'  # exit 2 — ratchet writes `io error: cannot emit the verdict: [Errno 32] Broken pipe` to stderr
```

## Boundaries

- **The metric itself belongs to [`crap-gate`](../crap-gate/SKILL.md)**: the CRAP formula, the 4/6/8 threshold regimes, the absolute per-function ceiling, the coverage-versus-assertion hole, and the per-language coverage-artifact wiring. This island owns only the relative no-regression discipline and the legacy-adoption path, and it calls that metric. `ratchet.py` never computes a CRAP score, and `--ceiling` is a number handed to it. Change a threshold there, not here.
- **Where the check executes belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails)**: the pre-commit hook, the PreToolUse guard, or the CI step that runs `ratchet.py` and that also enforces baseline-write hygiene (who may rewrite `baseline.tsv`, and after which verdict). This island states the rule; that island is the plumbing that can make it stick.
- **Loopback, ledgers, and band caps belong to [`archipelago`](../../COMPANION.md#archipelago)**; the captured run enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format as one rung of a verification ladder, never a second evidence format.

## Enforced vs advisory

- `enforced` — the comparison and the verdict. [`scripts/ratchet.py`](scripts/ratchet.py) fails any file whose CRAP or complexity rose or whose coverage fell. It joins on one key function, so a path variant either joins its baseline row or the gate refuses to run and names what it found (`./`, `//`, `\`, trailing slash, letter case, Unicode form, trailing dot or space, absolute, drive-prefixed, tree-escaping, invisible codepoint); it never reroutes a regression to the lenient new-file branch. It judges every four-field row, including one whose path starts with `#`. It fails any new file over the passed-in ceiling, and fails a merged over-ceiling share above the budget. It exits 2 on every malformed, unreadable, non-UTF-8, overflowing or non-finite input listed above, on any unhandled exception, and on a stdout it cannot print the verdict to, whether closed or broken. Where a printed number would round onto the one it is compared against, the message widens until the two render differently, on `WORSE` lines, `ok` lines and the budget line alike, walking out to `.17g`, which round-trips a double and so cannot collapse two distinct floats onto one string. Run red and green before this line was written. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — everything around the comparator: the per-file grain, the choice of budget number and the duty to tighten it, the downward-only baseline-rewrite rule, and the upstream production of the records themselves. Each is stated plainly so a later wave can mechanize it; calling any of them enforced today would launder an intention into a check.

## Done means

- [ ] Baseline recorded from a full run and committed, with the `--ceiling` value named and attributed to [`crap-gate`](../crap-gate/SKILL.md)
- [ ] `ratchet.py` exits 0 over the touched set: no regression on any recorded file, every new file under the ceiling
- [ ] Budget stated as a number with its current over-ceiling share, and tightened whenever that share falls
- [ ] The run's stdout plus exit code captured into the evidence packet; baseline rewritten in the same commit, downward only

An open box leaves the verdict `unverified`. Repair the file that regressed, by shrinking it or testing it, then re-run and re-check.

**Every file leaves cleaner than it arrived, or the diff does not land; the ratchet turns one way (C2).**
