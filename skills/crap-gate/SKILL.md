---
name: crap-gate
description: Per-function CRAP ceiling as a fix-until-green gate on agent-written code — the Savoia & Evans 2007 coverage-weighted complexity score, with threshold regimes for humans vs agents. Reach for it when wiring a quality gate over freshly generated code, setting or tuning a CRAP threshold, or when the user says "crap gate", "CRAP score", "coverage-weighted complexity", or "run crap over what you just wrote". Differentiator - this island owns the metric content (formula, regimes, input contract, the coverage hole); hook plumbing, gate infrastructure, and evidence format live on neighboring islands.
---

# CRAP Gate: small and fully tested

The cleaner seat's instrument. Bob states the live loop in one sentence: *"why don't you run crap over everything you've just done and it would run crap and then it would clean up the code"* (C6). Its shape is the deterministic-tool loop: *"you're putting them into a loop and you're saying, 'Okay, you must you must [sic] change the code until this tool says that it's okay.'"* (C4). This island supplies what that loop measures: the formula, the threshold regimes, the input contract, and the score's known blind spot. Every non-transcript claim below stands on [`crap-metric.md`](../../research/crap-metric.md). Quotes reach the page only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## The formula

```
CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)
```

`comp(m)` is the function's cyclomatic complexity. `cov(m)` is its automated-test coverage, in percent. The metric belongs to Savoia & Evans, 2007, at Agitar Labs. It is not Alberg's; [`crap-metric.md`](../../research/crap-metric.md) corrects that circulating misattribution.

The boundary behavior is the meaning:

- At 100% coverage CRAP degenerates to cyclomatic complexity, so the gate reads "small and fully tested." Bob's own gloss: *"a crap score of six means that there are six pathways through the function. They're all covered with tests"* (C6).
- At 0% coverage CRAP = comp² + comp. Complexity squared: untested branching is what the score punishes hardest.
- A breach is `score > threshold`; exactly-at passes. An untested two-path function scores exactly 6. So gate 6 tolerates untested trivial leaves, and gate 4 rejects them ([`crap-metric.md`](../../research/crap-metric.md)).

## Threshold regimes (advisory)

| Regime | Ceiling | Ground |
|---|---|---|
| human | 4 | Bob's human discipline (C17) |
| agent | 6 | Bob's live setting for agent-written code (C17) |
| experiment | 8 | his stated next push, evidence pending (C17) |

*"for a human I would keep crap numbers below four… but for the agents I've set this at six and… maybe I'll push it to eight"* (C17). The threshold is the part of a human discipline that moves when the worker changes (C17). So tune it empirically: run the gate at each candidate level, capture the outcomes, and let the captured evidence pick the number. An agent's opinion on the level is a hypothesis, never authority: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18). The regime choice itself stays advisory. No mechanical check picks it for you.

## Wiring the loop

Complexity is a near-free AST pass. Coverage is the dominant cost, and the test run already pays it, so CRAP adds close to nothing on top ([`crap-metric.md`](../../research/crap-metric.md)):

1. **Parse the coverage artifact the test run already produced** (JaCoCo XML, istanbul JSON, coverage.py, `go test -coverprofile`; per-language tool table in [`crap-metric.md`](../../research/crap-metric.md)).
2. **Join per-function cyclomatic complexity** onto those coverage rows.
3. **Feed the joined rows to the scorer and gate on its exit code.** [`scripts/crap-score.py`](scripts/crap-score.py) takes TSV rows `function <TAB> complexity <TAB> coverage_pct`. It prints a score per function and exits non-zero on any breach (captured run):

```bash
$ printf 'parse_row\t5\t80\nrender\t9\t40\n' | python3 scripts/crap-score.py --threshold 6
ok         5.20  comp=5 cov=80%  parse_row
BREACH    26.50  comp=9 cov=40%  render
2 functions, 1 over threshold 6
$ echo $?   # → 1
```

4. **Fix until green.** The formula responds to exactly two repairs: shrink the function (comp down), or test it (cov up). Then re-run. The loop ends only when the scorer exits 0 over the whole changed set (C4).

Scope the run to changed files only, so the loop stays fast enough to fire after every task (the `--changed` incremental pattern, [`crap-metric.md`](../../research/crap-metric.md)). Gate at the per-function grain. That is the metric's native grain, and it hands the agent an exact repair target. Per-module aggregates are dashboards, where hot spots hide behind averages. Both scoping rules are advisory.

## The known hole: name it, pair it

Coverage measures execution, not assertion. A test that calls the function and asserts nothing drives `cov(m)` to 100 and the score down to `comp(m)`, and the gate goes green on garbage ([`crap-metric.md`](../../research/crap-metric.md)). Mutation testing is the mandatory companion: the hardener's pass that kills assertion-free coverage. In this pack that concern belongs to the `mutant-hunt` island (roster line 5, [`02-ROSTER-50.md`](../../02-ROSTER-50.md)). A CRAP gate running without its mutation companion must say so in its evidence.

## Boundaries

This island supplies metric content only:

- Where the scorer actually executes (pre-commit, PostToolUse, a CI step) is hook and pre-commit plumbing, and it belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails).
- Gate infrastructure (loopback routing, the ledger, band caps) belongs to [`archipelago`](../../COMPANION.md#archipelago).
- The captured score report enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format. The scorer's stdout plus its exit code become one rung of that packet's verification ladder, never a second evidence format.

## Enforced vs advisory

- `enforced`: the arithmetic and the verdict. [`scripts/crap-score.py`](scripts/crap-score.py) computes the exact formula, exits 1 on any `score > threshold`, and exits 2 fail-closed on every path where it did not actually score the input: malformed or empty input, an input it cannot read or decode, a non-finite or overflowing complexity, coverage, threshold or score, an output stream it cannot write, and any unexpected internal fault. An empty gate cannot pass, an unreadable one is not a breach, a `nan` ceiling is not a ceiling, and a report nobody received is not a verdict. Those three codes are the whole set: every exception is sealed at the exit, so no fault leaves wearing CPython's default status 1 — this gate's BREACH — and no undelivered output leaks CPython's shutdown code 120. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: everything upstream of and around the scorer today. That is the regime choice (4/6/8), the per-language artifact parsing and CC join, changed-files-only scoping, and the mutation-companion pairing. Each is stated so a later wave can mechanize it. Claiming more would launder advisory into enforced.

**Red/green proof.** The scorer earns its `enforced` line by going red on a known-bad input and green on a known-good one: the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. All three fixtures live beside it. Recompute from this island's directory:

```bash
python3 scripts/crap-score.py --threshold 6 scripts/fixtures/dirty-over-ceiling.tsv   # exit 1 — render_invoice 26.50 BREACH
python3 scripts/crap-score.py --threshold 6 scripts/fixtures/clean-under-ceiling.tsv  # exit 0 — 2 functions, 0 over
python3 scripts/crap-score.py --threshold 6 scripts/fixtures/nonfinite-input.tsv      # exit 2 — a nan row and an overflowing row are refused, not scored
python3 scripts/crap-score.py --threshold nan scripts/fixtures/dirty-over-ceiling.tsv # exit 2 — a non-finite ceiling used to pass every breach
bash -c 'printf "f\377\t2\t0\n" > /tmp/crap-undecodable.tsv; python3 scripts/crap-score.py /tmp/crap-undecodable.tsv' # exit 2 — bytes that are not UTF-8 were never scored
bash -c 'python3 scripts/crap-score.py scripts/fixtures/clean-under-ceiling.tsv | true; exit ${PIPESTATUS[0]}' # exit 2 — a dead output pipe, not CPython's 120
bash -c 'python3 scripts/crap-score.py --threshold 6 0<&-' # exit 2 — a closed stdin is not a breach
bash -c 'printf "caf\303\251_render\t2\t100\n" > /tmp/crap-nonascii.tsv; PYTHONIOENCODING=ascii python3 scripts/crap-score.py /tmp/crap-nonascii.tsv' # exit 2 — a name this stdout cannot encode was never reported
bash -c 'python3 scripts/crap-score.py --help | true; exit ${PIPESTATUS[0]}' # exit 2 — a help screen nobody received, not CPython's 120
```

The clean fixture carries the boundary case: `is_expired`, comp 2, cov 0, scoring exactly 6.00, passing. So the pair proves the gate discriminates at the ceiling rather than rejecting everything. The seven runs under it are the non-verdict half of the same ritual, each watched failing: the third fixture is a coverage/CC join that emitted `nan` and an overflowing complexity — both used to print `ok` and exit 0 — then a `nan` ceiling, undecodable bytes, and a dead output pipe. The last three are faults that used to leave by CPython's own status instead of this table: a closed stdin and a function name an ASCII-only stdout cannot encode each exited 1, this gate's BREACH, and a help screen written into a dead pipe exited 120. Deleting any of these fixtures returns the gate to `unverified`.

## Done means

- [ ] Threshold declared with its regime named (human 4 / agent 6 / experiment 8); any other number grounded in captured runs, not agent vote (C18)
- [ ] `crap-score.py` exits 0 over every function in the changed set at the declared threshold
- [ ] The scorer's report captured into the evidence packet, with mutation-companion status stated

An open box means the verdict stays `unverified`: repair (shrink or test), re-run the scorer, re-check the boxes.

**Small and fully tested, or the tool does not consent. The agent loops until it does (C4).**
