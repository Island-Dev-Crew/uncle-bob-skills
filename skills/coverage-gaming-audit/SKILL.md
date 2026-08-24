---
name: coverage-gaming-audit
description: Audit a green coverage number for tests that execute code without asserting on it - assertion-free tests, assertions only on mocks, swallowed exceptions, unreviewed snapshots - and route every finding to the mutation run that settles it. Reports by default - on an audit or diagnosis ask the finding list is the deliverable, the fix-until-green loop is not entered, and deleting a test is never interchangeable with adding the missing assertion. Reach for it when a coverage report or CRAP score goes green and you do not yet believe it, when inheriting a suite of unknown quality, or when someone says "is this coverage real", "assertion-free tests", "gamed coverage", "100% coverage but nothing is tested", "audit this test suite". Differentiator - this island owns detection of gamed coverage and the routing to mutation; the score being distrusted belongs to crap-gate and the mutation run that proves the case belongs to mutant-hunt.
---

# Coverage Gaming Audit: execution is not assertion

Coverage instruments lines and branches. It records that a line **ran**. It records nothing about whether any test would have noticed had that line produced garbage. So a suite of assertion-free tests drives `cov(m)` to 100, collapses the CRAP score to plain cyclomatic complexity, and turns the pack's flagship gate green over code nobody is checking. The score rests on an assumption the ledger states outright (C6): *"a crap score of six means that there are six pathways through the function. They're all covered with tests"*. It cannot tell "covered with tests" from "covered with test-shaped code".

This is the documented hole in the metric, not a hypothetical. Coverage measures execution, not assertion quality, so assertion-free tests game it and teams optimise the number without reducing risk ([`research/crap-metric.md`](../../research/crap-metric.md)). It is also why the relay puts a hardener behind the cleaner: *"the guy who runs the mutation testing and he's absolutely merciless… it's going to have 100% coverage"* (C9). A hundred percent is the hardener's *starting* condition, never his verdict.

This island patrols the gap: **find the tests that execute without asserting, and route each one to the mutation run that proves the case.** Quotes reach it only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## Four ways a suite games the number

| Pattern | What it looks like | Why coverage loves it |
|---|---|---|
| **Assertion-free** | the test calls the function, prints or ignores the result, ends | every line under the call is executed and counted |
| **Mock-only** | every assertion observes the double: `assert_called_once_with(...)`, `.called`, `.call_args`, `.call_count` | asserts the double was poked, never that the code computed anything right |
| **Swallowed** | the body sits inside a broad `except` that cannot re-raise, or a `suppress(Exception)` | the code runs, the error is eaten, the test cannot go red |
| **Unreviewed snapshot** | a snapshot committed on first run and re-blessed whenever it breaks | the assertion exists but was never read by a human, so it asserts today's bug |

The first three are structural and machine-findable. The fourth is a review-history question no parser can answer, so it is `advisory` here. It is checked by asking when the snapshot was last read on purpose, and an auto-blessed snapshot counts as no assertion at all.

## Report or repair: read the invocation before anything runs

The two modes end differently, so classify the ask before the scanner starts.

**REPORT is the default, and on a diagnostic ask it is the whole job.** The questions this island answers to are diagnoses — *is this coverage real*, *audit this test suite*, a suite of unknown quality just inherited. To a question, the scan is the instrument and **the finding list is the deliverable**: run the scanner over the suite, report every finding with its file, line and pattern, state the verdict with the exit code that produced it, stop. Exit 1 is the answer, not a red to be cleared, and no test file is edited. The fix-until-green loop below is not entered on a question.

**REPAIR is entered only when the human asked for the repair** — *fix these*, *make the scan pass*, a named repair scope. Then the loop below applies, inside that scope and no wider.

**Deleting a test is never the other half of "add the assertion".** The two are not interchangeable: adding the assertion recovers the evidence the suite was missing, while deleting removes the finding *and* the coverage claim standing on it, and it is the cheapest path to exit 0 — exactly the move a fix-until-green loop reaches for, on an island whose whole subject is suites optimised toward a number. So deletion is out of scope on a REPORT run, and under a repair mandate it is proposed one test at a time, quoted with the reason it should go, and waits for that human to confirm that test. A gate whose fastest green is deleting the failing test measures nothing.

## The scan

[`scripts/assertless-scan.py`](scripts/assertless-scan.py) reads Python test files with `ast`. It never imports or executes them. Per test function it flags the three structural patterns:

```bash
python3 scripts/assertless-scan.py tests/                       # dirs are filtered to test_*.py / *_test.py
python3 scripts/assertless-scan.py tests/test_billing.py        # or explicit files
python3 scripts/assertless-scan.py tests/ --assert-helper assert_invoice_matches
```

| Exit | Meaning |
|---|---|
| 0 | clean verdict: every scanned test asserts on something |
| 1 | dirty verdict: at least one finding |
| 2 | usage, IO, or parse error (never a verdict), `--help` included |
| 3 | nothing to audit: no test functions found, so nothing can be certified |

Exit 3 is the fail-closed rule the pack applies to every gate: an empty scan is not a pass. Distinct meanings get distinct codes, so a broken invocation can never be read as a clean suite. **No error path may borrow a verdict's code.** A missing path, an unreadable or undecodable file, a syntax error, a non-identifier `--assert-helper`, argparse's own usage error, a recursion or memory blow-up, and any unforeseen internal exception all exit 2, never 1. `--help` exits 2 with them, because 0 here is a *verdict*, not an acknowledgement.

The rule extends to the *output*. A verdict whose evidence never reached the artifact is not a verdict, so a closed stdout or a broken pipe exits 2 rather than handing a CI consumer a bare exit code over an empty capture. (`1>&-` makes `sys.stdout` None and `print` a silent no-op.)

Those four are the only codes that leave the process, and that has to hold through *interpreter shutdown*. CPython flushes the std streams on the way out and *replaces* the exit status with 120 when that flush raises. Returning 2 is therefore not enough on its own. A `--help` written into a dead stdout pipe, and argparse's own usage error written into a dead stderr, each reported 120 until the script grew a seal of its own: it flushes both streams itself, downgrades a verdict whose output never landed to 2, and points the dead fd at `/dev/null` so the shutdown flush has nothing left to fail on. Both probes are captured below.

The same rule governs *collection*. A test function is collected from every statement body at module scope: behind a `sys.version_info` guard, inside a `try/except ImportError`, in a nested class. Pytest collects those too, and a scan that silently skipped them would report green over tests it never read.

Under-collection is the false green this island exists to catch, so the scanner refuses to reach it by accident. Filenames match case-insensitively, so a `Test_Billing.py` is read rather than skipped. Source is decoded `utf-8-sig`, so the BOM a Windows editor writes is content rather than a parse error that takes the whole directory scan to exit 2. Reading a file pytest would not is a false red, and this island fails closed.

Over-collection of the *count* is a false evidence line for the same reason. Files therefore carry one documented identity key, `(st_dev, st_ino)`, the filesystem's own answer. `./f`, `d//f`, `d/../d/f`, an absolute spelling, a symlink, a hardlink, a letter-case variant, an NFC and an NFD spelling of one macOS name, and a directory plus a file inside it all scan once instead of inflating the scanned total.

Four deliberate strictnesses, all anti-fooling. Each closes an idiom swap, an edit that changes the wording of a test without changing what it proves. That is exactly the edit an agent in a fix-until-green loop reaches for:

- **Assertions inside a nested `def` or `lambda` do not count, blanket, called or not.** An assertion in a callback the test never invokes is decoration, and a parser cannot tell a live callback from a dead one, so the rule applies to both. A test whose only `assert` sits in an inner function is reported `NO-ASSERTION` either way. An inline helper that really does the checking is excused by name, below.
- **An assertion that only observes the double is `mock`, whatever its idiom.** `gateway.charge.assert_called_once_with(1200)`, `assert gateway.charge.called`, `assert gateway.charge.call_args == ((1200,), {})` and `self.assertEqual(gateway.charge.call_count, 1)` are one claim in four costumes. An `assert` statement, or a `self.assertX(...)`, whose *every* value chain terminates in `.called`, `.call_count`, `.call_args`, `.call_args_list`, `.mock_calls`, `.await_count` or `.await_args` scores as a mock assertion, not a real one. **Hoisting a name does not change that, in either direction.** On the *expected* side, a name bound only to literals contributes exactly what the inline literal contributed: nothing. That holds whether it sits in the test, in the class body as `self.EXPECTED_CALLS` (including one inherited from a base class *written in the same file*), or at module scope. On the *observed* side, a name bound only to mock observations carries those observations transitively, through a wrapping call, and through the walrus. So `actual = gateway.charge.call_args; assert actual == ((1200,), {})` stays `MOCK-ONLY` exactly as the inline form does. A name that is ever bound to something the code produced is a real value however it is spelled, whichever binding is written first. One real value in the same assertion makes it real again.
- **A broad handler is a swallow unless its body can propagate.** Not only `pass`/`...`: `return`, `continue`, `print(e)` and logging bodies eat the failure identically. So does an assert that cannot fail: `assert True`, `assert 1`, `ok = True; assert ok`, `assert not False`, `assert 1 + 1`, `assert 1 == 1`, `assert "x" in "xyz"`, or the same tautology in the unittest costume, `self.assertTrue(True)` / `self.assertEqual(1, 1)`. Each is one token off `pass`. The handler passes only if it can still turn the test red: a `raise`, an `assert` whose test does not *fold* to a constant true, a `fail()`, or a declared assert-helper (`assert False, "must not raise"` folds to false, propagates, and passes). The fold is arithmetic done on the parse tree over literals only; nothing is imported, executed or `eval`'d. It is also deliberately bounded: `is` / `is not` are left alone because literal identity is not a language guarantee, and operands past a size cap are refused rather than computed. What it cannot fold reads as able to propagate, which is a disclosed limit with a fixture below, not a silent one. **The class, `suppress` and `pytest.fail` are resolved by import binding, not by spelling.** `except Exception:`, `except builtins.Exception:` and `except Boom:` after `from builtins import Exception as Boom` are one handler in three costumes. `with suppress(Exception):` is the same swallow with no handler node to find, whether the name arrives plain (`suppress`), renamed (`from contextlib import suppress as quiet`), or through the module (`contextlib.suppress`, `import contextlib as ctx` included). A narrow `except FileNotFoundError: pass` is cleanup and passes, and so does a narrow class renamed at import: resolving bindings widens the net by binding, never by alias alone.
- **Nothing is allow-listed by default.** `raises` / `warns` / `deprecated_call` count only through a real pytest binding: the `pytest` module however aliased, or a name imported `from pytest import raises`. A `.raises()` method on some arbitrary object is not an assertion, and by the same rule a `.suppress()` method on some arbitrary object is not contextlib's and is not a swallow. The only way to widen the allowlist is the written excusal below.

**Known false-positive class**, stated rather than hidden. A suite that delegates its assertions to a named helper scans as assertion-free. That covers both the top-level kind (`assert_invoice_matches(actual, expected)`) and the nested `def` or `lambda` the test itself invokes, which the blanket nested-scope rule flags exactly like an uncalled one. `--assert-helper NAME` teaches the scanner that helper in either shape, and each use is a **written excusal the run records itself**. Every summary line ends `— helpers declared: NAME, ...`, or `helpers declared: none`. So does **every line the run prefixes `error:`**: argparse's usage error, the non-identifier helper, the missing path, the parse and decode errors, the unwritable stdout, the broken pipe, the exit-3 empty scan and the catch-all alike, recovered straight from `argv` when a failure lands before the parse finishes. (The usage banner argparse prints above its own message is not an `error:` line and carries nothing.) A widened run is therefore never shaped like a genuine clean one in the captured artifact. That is the same spirit as the excusal discipline on [`mutant-excusal-ledger`](../mutant-excusal-ledger/SKILL.md). Both cases fail *closed*, red and never green, so the cost of the strictness is a declaration, not a missed finding. Silently widening the allowlist to clear a red run is gaming the gamed-coverage detector, and the output line is what makes "silently" impossible.

**What the scan cannot see**, each one shipped as a run below rather than left to be discovered. The tautology class outside a handler still scores as a real assertion: `assert True` standing alone, `assert result is not None` on a function that can only return that object, an assertion on a value the code never varies. Inside a broad handler it does not, *as far as the fold reaches*. A tautology the fold refuses, one routed through a call (`assert bool(1)`) or past its size cap (`assert 10 ** 100000`), reads as able to propagate and the handler passes. Any mock observation reached by a chain the list above does not name escapes too (`assert gateway.charge.call_args.args == (1200,)` terminates in `.args`, so it reads as real).

Name resolution reaches imports and this one file. So a broad class or `suppress` rebound by *assignment* (`Boom = Exception`) reads as narrow, a class constant inherited from a base class *imported from another module* is unresolvable from one parse tree and reads as a real value, a constant fetched through a call (`getattr(consts, "CALL_ARGS")`) rather than written as a literal reads as a real value, and a test function generated at runtime rather than written as a `def` is never collected at all.

Then **collection scope**, since a file the scan never reads is the quietest false green of all. A directory argument is walked with `os.walk(followlinks=True)` and matched against `test_*.py` / `*_test.py` with Unicode `\w`, so a symlinked test tree and a non-ASCII module name (`test_café.py`) are both collected. Pytest runs both, and an ASCII-only pattern with a link-refusing walk silently skipped them while reporting clean. Each directory is visited once by its real path, so a symlink cycle terminates instead of spinning. What still falls outside: a test file whose name matches neither pattern, and a suite reached only through a `conftest.py` hook or a custom collector. These pass the parser and prove nothing. The scan is a screen, not a proof, which is the whole reason for the next section.

## A finding is a candidate; a surviving mutant is the proof

Detection is cheap and shallow; mutation is expensive and conclusive. The mutation run flips one operator at a time and demands the suite notice: *"for each of those flips, it runs your entire test suite and expects the test suite to fail… if it doesn't fail, well, that's a surviving mutant and it must be killed"* (C7). **A surviving mutant on a covered line is the direct evidence that an assertion is missing**, the thing coverage can never tell you ([`research/mutation-testing.md`](../../research/mutation-testing.md)). Mutation testing is therefore the mandatory companion of any coverage-derived gate, not an optional upgrade.

The routing under a repair mandate, run as a fix-until-green loop the agent cannot exit until the tools consent (C4). On a REPORT invocation it stops after step 1, at the reported findings:

1. **Scan.** Run the scanner over the changed tests. Exit 1 hands you a list of suspect tests with file, line, and pattern.
2. **Repair at the finding.** Add the assertion the test was missing. A test that asserts nothing is worse than no test: it buys coverage credit for nothing — which is why the repair is the assertion. Deleting the test is a scope change, not the other option: per-test human confirmation, per the rule above.
3. **Re-scan** to exit 0.
4. **Mutate the code those tests cover.** Exit 0 from the scanner means every test asserts *something*; only the mutation run tells you whether it asserts the *right* thing. Hand the scope to the mutation gate.
5. **Every survivor returns as a kill-task**: write the test that fails on that exact change. The loop closes only when both tools consent.

Steps 4 and 5 run on the neighbouring island, not here. Skipping them leaves the audit `unverified`: a clean scan plus no mutation run is a suite proven to contain assertions, not a suite proven to catch bugs.

## Boundaries

- **[`crap-gate`](../crap-gate/SKILL.md) owns the score this island distrusts**: the formula, the human 4 / agent 6 / experiment 8 regimes, the input contract. This island never computes or re-tunes a CRAP score; it audits whether the coverage term feeding one was earned.
- **[`mutant-hunt`](../mutant-hunt/SKILL.md) owns the mutation run that settles it**: diff scoping, operator families, the zero-survivors-on-the-diff contract, the runtime budget cap. This island owns **detection of gamed coverage and the routing to mutation**; it hands over scope and stops.
- **Writing a suite that teaches is the sibling [`tests-as-spec`](../tests-as-spec/SKILL.md)** (Wave 2, [roster](../../02-ROSTER-50.md) line 24): naming, arrangement, and a suite readable as the specification by the next fresh context. That island is about tests worth reading; this one is about tests worth trusting.
- **Where the scan executes** (pre-commit, PostToolUse, a CI step) belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails), and the loop plumbing around it to [`archipelago`](../../COMPANION.md#archipelago).
- **The captured findings enter [`evidence-packet`](../../COMPANION.md#evidence-packet) format**: the scanner's stdout and its exit code become one rung of the packet's verification ladder, never a second evidence format. The `--assert-helper` excusal needs no separate note. It is printed on the summary line the packet already captures, and a stdout that could not be written exits 2 rather than contributing a verdict with no evidence behind it.

## Enforced vs advisory

- `enforced`: the three structural verdicts and their exit codes. [`scripts/assertless-scan.py`](scripts/assertless-scan.py) parses with `ast`, exits 1 on any `NO-ASSERTION` / `MOCK-ONLY` / `SWALLOWED` finding, exits 0 only when at least one test was scanned and none was flagged, exits 3 fail-closed when there is nothing to audit, and exits 2 on every error path: usage (`--help` included), IO, decode, parse, an unwritable stdout, and any unhandled internal exception. No crash can be read as a verdict. It seals its own exit rather than leaving it to the interpreter, so a std stream it cannot flush at shutdown cannot substitute CPython's 120 for the code it chose. Run against Python test files today; **no other language ships a scanner here**, so on a non-Python suite every rule on this page is `advisory` until you build the equivalent parser.
- `enforced`: the `--assert-helper` excusal *record*. Every summary line and every `error:` line names the declared helpers, so a widened run cannot be mistaken for a clean one in a captured artifact. Whether the declaration was *justified* is still a human judgement, and that part is `advisory`.
- `enforced`: this island's own shape, checked by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: the REPORT-by-default routing and the per-test confirmation before any deletion. The scanner reports findings and an exit code; nothing in it can tell an audit ask from a repair mandate, and no gate here can refuse a deletion. The discipline is the human's until a later wave mechanizes it, and a run that reached exit 0 by deleting tests states which ones.
- `advisory`: the snapshot-review pattern (no parser can see review history), the justification behind each `--assert-helper`, the tautological-assertion class outside a broad handler, and inside one the part of it the literal fold refuses, which `test_limit.py` above captures as a run. The routing to mutation is advisory too: the mutation run happens on [`mutant-hunt`](../mutant-hunt/SKILL.md) under *its* enforcement, and this island cannot make it fire. Each is stated so a later wave can mechanize it; claiming more would launder advisory into enforced.

**Red/green proof.** The scanner earns its `enforced` line by having been watched failing: the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Both fixtures live beside it; recompute from this island's directory:

```bash
python3 scripts/assertless-scan.py scripts/fixtures/test_gamed_suite.py      # exit 1 — 34 scanned, 34 findings
python3 scripts/assertless-scan.py scripts/fixtures/test_asserting_suite.py  # exit 0 — 17 scanned, 0 findings
```

The dirty fixture fails for the right reason, one finding per test: one per gaming shape *and one per idiom swap*, so a reworded evasion goes red rather than clean:

- `NO-ASSERTION`: a bare run, an `assert` marooned in a nested `def`, an unanchored `fake.raises(ValueError)`, and a bare run behind a `sys.version_info` guard
- `MOCK-ONLY`: `assert_called_once_with(...)`, `assert gateway.charge.called`, `assert gateway.charge.call_args == (...)`, `self.assertEqual(gateway.charge.call_count, 1)`; the same claims with the expected literal hoisted into a local, a rebound fixture parameter, a module constant, a class body, or a base class; and the mirror hoist of the *observation* into a local, into a walrus, and into a local read back by `self.assertEqual`
- `SWALLOWED`: `except Exception: pass`, `: return`, `: print(e)`, `: assert True`, `: assert ok` under `ok = True`, `: assert not False`, `: assert 1 + 1`, `: assert True or charge_card`, `: self.assertTrue(True)`, `except builtins.Exception:`, `except Boom:` under `from builtins import Exception as Boom`, `with suppress(Exception):`, `with contextlib.suppress(Exception):`, and `with quiet(Exception):` under `from contextlib import suppress as quiet`

The clean fixture carries the boundary cases that must *not* trip: `pytest.raises`, a bare `from pytest import raises`, `self.assertEqual` on a real value, a mock *call* assertion and a mock *observation* assertion each standing beside a real one, a hoisted mock observation standing beside a real one, a broad handler that re-raises, a broad handler asserting a constant *false*, a broad handler calling `self.fail(...)` (whose arguments are literals but which always raises), a narrow `except FileNotFoundError: pass` cleanup, a narrow class renamed at import, a `.suppress()` method on an arbitrary object, a literal-bound local and a literal class constant each used as the *expected* value beside a real observation, a local holding a value the *code* produced, and an asserting test behind a version guard. Each pins one strictness against over-reach, since a fix that flagged every alias, every guarded def, every local, every class attribute, or every handler assert would still pass the dirty fixture. More captured runs pin the rest. Each proves an error path cannot borrow a verdict, and the last two prove what the scanner reads and what it admits it misses:

```bash
python3 scripts/assertless-scan.py scripts/fixtures/test_gamed_suite.py 1>&-   # exit 2 — closed stdout, never a silent verdict
(set -o pipefail; python3 scripts/assertless-scan.py scripts/fixtures/test_gamed_suite.py | true)  # exit 2 — broken pipe, not a dirty verdict
python3 scripts/assertless-scan.py scripts/fixtures/ scripts/fixtures/test_gamed_suite.py     # exit 1 — 51 scanned, not 85: one key per file
python3 scripts/assertless-scan.py scripts/fixtures/test_gamed_suite.py --assert-helper "a b" # exit 2 — a helper must be an identifier
python3 scripts/assertless-scan.py --help                                                     # exit 2 — usage is not a clean verdict

# The shutdown seal: a dead pipe under the two paths that write before the seal can run.
# These print the CHILD's exit status directly, so no shell `$?` can be lost on the way back.
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/assertless-scan.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'  # 2, not 120
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/assertless-scan.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'  # 2, not 120

D=$(mktemp -d)
printf '\xef\xbb\xbfdef test_bom_gamed():\r\n    charge_card(1)\r\n' > "$D/Test_Bom.py"
python3 scripts/assertless-scan.py "$D"                       # exit 1 — a BOM, CRLF and a capitalised filename are read, not skipped
printf 'def test_unfoldable():\n    try:\n        assert charge(1) == 1\n    except Exception:\n        assert 10 ** 100000\n' > "$D/test_limit.py"
python3 scripts/assertless-scan.py "$D/test_limit.py"         # exit 0 — DISCLOSED LIMIT: a tautology past the fold's size cap passes
```

plus: a file with no test functions exits 3, a missing path exits 2, an undecodable or unparsable file exits 2, argparse's own usage error exits 2, and a suite delegating to a helper exits 1 undeclared / 0 with `--assert-helper NAME`, the green line reading `helpers declared: NAME`, never bare. The `test_limit.py` run is the shape of an honest hole: the gate consents, and the consent is on the page with its command beside it. Read each code with `cmd; rc=$?` on its own line. `$?` after a pipe is the *pipe's* status (hence the `pipefail` subshell above), and a command substitution elsewhere on the line (`f $(basename x); rc=$?`) overwrites it. Both mistakes report a verdict the run never returned. Deleting either fixture returns the scanner to `unverified`.

## Done means

- [ ] The invocation was classified REPORT or REPAIR before the scan ran, and a REPORT run ended at the reported findings
- [ ] Scanner exits 0 over the changed tests, with every `--assert-helper` used recorded as a written excusal
- [ ] Each finding was repaired by adding the missing assertion, never by loosening the scan; any deletion was confirmed by the human, test by test
- [ ] Mutation run fired on the code those tests cover, with zero unhandled survivors, on [`mutant-hunt`](../mutant-hunt/SKILL.md)
- [ ] Any CRAP or coverage number reported alongside states its mutation-companion status
- [ ] Non-Python suites state plainly that the scan is `advisory` here, so the verdict reads `unverified` rather than green

An open box means the verdict stays `unverified`: repair, re-scan, re-mutate, re-check the boxes. A REPORT run leaves every box below the first open by design — its deliverable is the finding list and the verdict, and the suite reads `unverified` until someone asks for the repair, which is the honest state and not a green.

**Coverage proves the line ran. Only a dead mutant proves someone was watching.**
