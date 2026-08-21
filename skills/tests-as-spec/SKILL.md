---
name: tests-as-spec
description: The unit suite written as the teaching document for the next fresh-context agent — names that state behaviour, arrangement that shows the module's shape, one behaviour per test, and the paths a newcomer guesses wrong. Reach for it when the reader of your tests is an agent that will not open the implementation, when a suite has to survive being handed to a context that never met its author, or when someone says "tests as documentation", "my test names say nothing", "make this suite readable for the next agent", "the tests should explain the system". Differentiator - this island owns the unit suite as a document for a reader; the story-level acceptance contract and the proof that the suite bites belong to neighbouring islands.
---

# Tests as Spec: the suite is the document

Bob's observation about how agents read a system is one line: *"They read tests to understand what the system does"* (C16). That is not a nice-to-have — it is the reading path. A model handed a deep module *"can read the interface without having to understand the implementation"* (C16, MP's framing, which Bob answers *"Yeah, absolutely"*), and Bob names the consequence exactly: *"They pay attention to the structure. It can allow them to not read the code beneath them, which is both a danger and an advantage… as long as the code is consistent, you're okay"* (C16).

So the unit suite is the artifact that closes the gap the skipped implementation opens. This island is about writing it for that reader. Research ground for the non-transcript claims below: [`ousterhout-debate.md`](../../research/ousterhout-debate.md) and [`martin-canon.md`](../../research/martin-canon.md). Quotes come only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## Who you are writing for

The reader is a specific person, and they are not you:

- **They arrive with no history.** Agents *"are born, do the task, and die so that the next one comes in with a clean context"* (C10). Every fresh seat meets your suite for the first time; nothing you explained in a previous session survives.
- **They will read all of it.** Agents read what they are sent — *"if you pass a spec to an agent they're probably going to read it"* — while *"the things that the agents write, the humans don't read"* (C24). An artifact aimed at agents may be long; the cost of a bad test name is not length, it is a wrong belief about the system.
- **They may never open the implementation.** That is the advantage and the danger in one move (C16). The suite is where the behaviour has to be legible, because the code beneath it will be skipped.

Ousterhout and Martin disagree about method length, comments, and process, and still agree that comprehensive unit tests are non-negotiable ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). For an agent reader the disagreement matters less than the reading path — interface, interface comment, and tests, with the implementation loaded only when something forces it.

## What a teaching suite does

**Name the behaviour, not the method.** `test_render_invoice_line` tells the reader that a function exists — which they already knew from the interface. `test_invoice_line_shows_unit_price_and_quantity` tells them what the system *does*, and it fails as a sentence when the behaviour changes. This is Clean Code's intention-revealing-names rule (Ch. 2, [`martin-canon.md`](../../research/martin-canon.md)) applied where a fresh context actually looks first. A name that mirrors the callable spends a line of the document restating the interface.

**Arrange so the module's shape shows.** Build the object the way a caller builds it, name fixture values after their role rather than their type, and let the setup block be the reader's first correct picture of how the pieces fit. Setup that reaches past the interface — poking private state, monkeypatching internals — teaches the reader a shape that callers cannot use.

**One behaviour per test.** A test asserting three unrelated things can only be named after one of them, so the other two are undocumented and the failure message points at the wrong idea. Splitting them is what makes the name honest.

**Cover the paths a newcomer would guess wrong.** The empty collection, the boundary value, the error the API raises rather than swallows, the second call that behaves differently from the first. A newcomer's wrong guesses are precisely what the suite exists to correct; paths that behave exactly as the name implies teach the least.

## The name floor

Only the first property has a deterministic floor today, and this island ships it. [`scripts/test-name-lint.py`](scripts/test-name-lint.py) parses Python test files with `ast` — never importing them, never writing bytecode — and fails on six conditions:

| code | fires when |
|---|---|
| `UNFOLDABLE` | a character survives the fold outside ASCII — `test_bøsic_høppy_pøth`, a Cyrillic or Han name. The split reads ASCII, so a leftover character would act as a word *separator* and shatter one word into fragments no filler set has heard of; a name the floor cannot read is rejected, never scored |
| `THIN-NAME` | fewer than `--min-words` behaviour words after the `test` prefix (default 3) |
| `PLACEHOLDER` | every word is filler or a digit — `test_case_2_works`, `test_basic_happy_path`, `test_it_works_ok`. Shorter placeholders (`test_1`, `test_it_works`) trip `THIN-NAME` first; the four *readability* codes are checked in this table's order, so a name reports the first of those it fails, not all of them |
| `MIRRORS-CODE` | the name is exactly a callable declared in `--against` — the method, not the behaviour |
| `DUPLICATE` | two tests share a name in one scope; in Python the later silently shadows the earlier. Orthogonal to the four above and reported alongside them, so a repeated thin name reports both |
| `NO-TESTS` | the file declares no test names — fail closed, so deleting the suite cannot go green |

**What counts as a test is the runner's definition, not a prettier subset.** A name is a test if it starts with `test` — pytest's own default `python_functions = test*` — whether it is a `def`, an `async def`, or a `unittest` method. **How** it is bound counts: `=` is not the only binder, so the walker records the target name of an assignment (`test_1 = _impl`), an import alias (`from helpers import test_total`), a walrus (`if (test_1 := _impl)`), a `for` target, a `with ... as`, a `match` capture, an `except ... as`, an augmented assignment, and a name a nested def declares `global` — `global` being the one keyword that makes a function body bind at *module* scope, where pytest looks. **Where** it is written counts too: pytest collects what the module binds when it executes, so a binding nested in `if`/`try`/`with`/`for`/`while`/`match` is collected exactly like one at the top level, and the walker follows every block those statements own — refusing only to enter the scopes that bind elsewhere (a function or lambda **body** — read for its `global` declarations and nothing else — and a comprehension's own `for` target, which PEP 572 keeps inside the comprehension while putting a walrus in the containing scope). A class body is not one of those: the walker **does** enter it, carrying the class name as the scope, which is how `unittest` methods are reached and how `DUPLICATE` is scoped. Names are folded through **one** key function before any comparison — NFKD, combining marks dropped — then split on underscores *and* camel/digit boundaries, so `testtotal` states one word, `testcase2works` states only filler, and `test_it_wörks` cannot launder past the filler set that catches `test_it_works`. That fold keys only what *decomposes*; a Latin letter NFKD leaves atomic (`ø ł đ æ œ ß`) would survive into the split as a separator — shattering `bøsic` into `b` + `sic` — so a name carrying one is **rejected** rather than scored. Collecting narrower than the runner is itself the forge: delete the underscores, push the suite one indent down behind a version guard, swap `=` for `:=`, declare the name `global` inside a helper, or respell it with letters the fold cannot read, and a narrower collector reports the file clean while pytest runs every worthless test in it.

Exit codes are distinct by meaning, and the gate produces no fourth: **0** clean, **1** violations found, **2** usage, IO, decode, parse, encode, or write failure. (The one code it cannot own is an interpreter that never starts — `PYTHONIOENCODING=bogus` exits 1 before `main()` exists, which no line inside the file can catch.) A missing file and a suite full of bad names must never look alike to the loop that consumes the verdict — and neither must an undecodable one, whose `UnicodeDecodeError` is a `ValueError` and so slips past an `OSError`/`SyntaxError` guard into the exit code that means "violations found". The same rule governs the far end: a verdict that cannot be **delivered** (fd 1 closed, a reader that hung up mid-print, or an accented name printed to a stdout whose encoding cannot represent it, as under `PYTHONIOENCODING=ascii`) exits 2 — an uncaught `BrokenPipeError` exits 1, a `None` stdout exits 1 on the flush, and `UnicodeEncodeError` is another `ValueError` that walked past an `OSError`-only guard and exited 1 with a half-written verdict. `RecursionError` and `MemoryError` are caught for the same reason, and the binding scan is iterative so a pathological expression cannot raise one.

**Red/green proof.** The lint earns its `enforced` line by having been watched failing — the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Every suite fixture describes the same module; recompute from this island's directory:

```bash
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/dirty-suite.py      # exit 1 — MIRRORS-CODE, PLACEHOLDER, THIN-NAME, DUPLICATE
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/laundered-suite.py  # exit 1 — 5 names seen, 4 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/guarded-suite.py    # exit 1 — 6 names seen, 5 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/bound-suite.py      # exit 1 — 5 names seen, 4 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/accented-suite.py   # exit 1 — 4 names seen, 3 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/stroke-suite.py     # exit 1 — 4 names seen, 4 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/global-suite.py     # exit 1 — 3 names seen, 2 violations
python3 scripts/test-name-lint.py --against scripts/fixtures/module-under-test.py \
    scripts/fixtures/clean-suite.py      # exit 0 — 4 test name(s), 0 violation(s)
PYTHONIOENCODING=ascii python3 scripts/test-name-lint.py \
    scripts/fixtures/accented-suite.py   # exit 2 — verdict computed, cannot be encoded
python3 scripts/test-name-lint.py scripts/fixtures/bom-suite.py      # exit 1 — a BOM is a verdict, not a parse error
python3 scripts/test-name-lint.py scripts/fixtures/deleted-suite.py  # exit 1 — NO-TESTS
python3 scripts/test-name-lint.py scripts/fixtures/binary-suite.py   # exit 2 — cannot decode input
python3 scripts/test-name-lint.py scripts/fixtures/nope.py           # exit 2 — cannot read input
python3 scripts/test-name-lint.py scripts/fixtures/dirty-suite.py >&-  # exit 2 — cannot write verdict
python3 scripts/test-name-lint.py --min-words 0 scripts/fixtures/clean-suite.py  # exit 2 — usage
```

The dirty fixture is valid Python and fails on its **names** — one `MIRRORS-CODE`, one `PLACEHOLDER`, one `THIN-NAME`, one `DUPLICATE`; the other two codes need a file it cannot also be (empty of tests, or named outside ASCII), so `deleted-suite.py` and `stroke-suite.py` carry those. A fixture that failed on a parse error would prove nothing about the check. The clean fixture carries the boundary case — `test_refund_requires_receipt` states exactly three words, so the pair proves the gate discriminates at the floor instead of rejecting everything — and a camelCase `unittest` method, so the lint is shown reading both conventions. `deleted-suite.py` is the obvious forge (delete the tests, keep the helpers). Six fixtures are the laundering forges, each one worthless suite hidden by a different trick, and none of them is a sentence — each is a captured run whose **pytest parity was measured, not assumed** (`pytest 9.1.1 --collect-only -q`, on the Python the island was built against):

| fixture | the trick | pytest collects | lint sees | violations | exit |
|---|---|---|---|---|---|
| `laundered-suite.py` | delete the underscores; one module-level alias | 5 | 5 | 4 | 1 |
| `guarded-suite.py` | move the names behind `if`/`with`/`try-else` and an import alias | 6 | 6 | 5 | 1 |
| `bound-suite.py` | bind with a walrus, a `for` target, a `with ... as`, a `match` capture — no `def`, no `=` | 5 | 5 | 4 | 1 |
| `accented-suite.py` | respell the words with diacritics (one name written NFD on disk) | 4 | 4 | 3 | 1 |
| `stroke-suite.py` | respell with the Latin letters NFKD leaves atomic — `ø ł æ œ` | 4 | 4 | 4 | 1 |
| `global-suite.py` | bind from inside a helper's body, behind `global` | 3 | 3 | 2 | 1 |
| `clean-suite.py` | *(the control)* | 4 | 4 | 0 | 0 |

The last four were each added when a blind critic forged past the collector, and each closed the hole it found: a walrus and a `for` target bind a name the file's own text spells; `test_it_wörks` folds to filler only if something folds it; `test_bøsic_høppy_pøth` scored **six** behaviour words until the fold learned to refuse what it cannot read; and `global test_1` inside `_install()` binds at module scope, which is the walrus forge moved one indent down behind a keyword. `binary-suite.py` is not valid UTF-8 and must exit 2 rather than 1 — an unreadable input is not a verdict; `bom-suite.py` is the mirror error, valid Python behind a byte-order mark that must produce a **verdict** rather than a false `cannot parse`. `>&-` closes fd 1 so the verdict cannot be delivered at all: also 2, never 1, and so is the verdict an ASCII-only stdout cannot encode. Deleting any fixture returns the lint to `unverified`.

The floor is a floor. It rejects names that *cannot* be behaviour statements; it cannot confirm that a name which passes is **true**. That check is a human or reviewer spot-check, and saying otherwise would launder advisory into enforced.

## Boundaries

- **The acceptance contract is not here.** Given-When-Then scenarios at story level, authored by the specifier seat and required to fail red before implementation and pass green after, belong to [`gherkin-gate`](../gherkin-gate/SKILL.md) (roster line 25, [`02-ROSTER-50.md`](../../02-ROSTER-50.md)). That island owns the story-level contract; this one owns the unit suite as documentation. A suite can read beautifully and still implement the wrong story — that is what the acceptance gate is for.
- **Whether the suite bites is not here.** Coverage measures execution, not assertion; the proof that these tests would actually fail on a behaviour change is mutation testing, owned by [`mutant-hunt`](../mutant-hunt/SKILL.md), with its excused-survivor discipline in [`mutant-excusal-ledger`](../mutant-excusal-ledger/SKILL.md). A well-named suite of assertion-free tests is a well-written lie.
- **This is not TDD restated.** Strict red-green interleave is explicitly *not* imposed on agents: *"I don't think it makes any sense to make an agent write a single line of a test and then write a single line of the production code"* — they *"write a function and then write the test for that function"*, and *"They always fall back on doing that… So I figure that's probably okay"* (C17). The value (tests everywhere, and they must be readable) transfers; the human ritual does not. Nothing here dictates when the test gets written.
- **Token budgeting the interface-first read** — how much implementation an agent may load before it must justify the load — belongs to [`interface-budget`](../interface-budget/SKILL.md) (roster line 26, [`02-ROSTER-50.md`](../../02-ROSTER-50.md)), not this island.
- **Where the lint executes** (pre-commit, PostToolUse, a CI step) belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails); **document-level context-economy levers** for any agent-read artifact belong to [`writing-for-agents`](../../COMPANION.md#writing-for-agents); the captured lint output enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format as one rung, never a second format.

## Enforced vs advisory

- `enforced` — the name floor and the verdict: `test-name-lint.py` implements the six codes above, collects every `test*` name **the linted file's own text binds through a static target name** — defs and `unittest` methods, assignment and augmented-assignment targets, import aliases, walrus targets, `for` targets, `with ... as`, `match` captures, `except ... as`, and names a nested def declares `global` — wherever they are written, including inside `if`/`try`/`with`/`for`/`while`/`match` and inside a class body, exits 1 on any violation, exits 1 on a file with zero tests, and exits 2 on usage, IO, decode, parse, encode, or write failure. **Within those binding forms** the collected set is a superset of pytest's in exactly one direction: a name written behind a guard that never runs, declared `global` by an installer nobody calls, or bound to something that is not callable, binds no test at runtime and is judged anyway — the fail-closed side to be wrong on. Outside them it is a subset rather than a superset, and the residual contract below names where — a `python_functions` override, parametrized ids, dynamic binding, star-imports — each one fail-open. Every command in the proof block was run in both directions, and the parity column of the table above was measured against `pytest --collect-only`, before this line was written. One caveat with teeth: `MIRRORS-CODE` fires only when `--against` names the module under test, so a run without it quietly checks five codes instead of six — which is why the checklist demands the argument. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — everything else on this island, stated plainly so a later wave can mechanize it: arrangement that shows the module's shape, one-behaviour-per-test, guess-wrong path coverage, and the truth of a name that clears the floor.
- `advisory` — **the residual input contract, named rather than left to be discovered.** The lint is Python-only (other languages are unchecked today) and it reads a file's own text, so what it cannot see is: a `python_functions` pattern **overridden** in `pytest.ini`/`pyproject.toml` (a suite collected as `check_*` is invisible to a `test*` floor), **parametrized ids** — `@pytest.mark.parametrize` generates `test_x[case-2]` at runtime and the floor judges only the stem `test_x` — **dynamically generated tests** (`pytest_generate_tests`, factory loops, and names bound through a dict, `setattr`, `globals()[...]` or `exec` — routes where no static target name is written down, which is exactly where the enforced line stops), and **star-imports** — `from dirty_helpers import *` binds names the importing file never spells, so only the declaring file can be judged (a named alias, `from dirty_helpers import test_total`, is spelled and is checked). Each of those runs green here and can still teach a fresh context nothing. One more limit worth naming rather than discovering: the word split reads **ASCII**, so every character the NFKD fold leaves outside it — Han, Cyrillic, and the Latin letters that do not decompose (`ø ł đ æ œ ß`) — trips `UNFOLDABLE`. That is fail-closed by construction rather than by luck (unread, such a character *separates* words instead of being one, which scored `test_bøsic_høppy_pøth` at six), but it means the floor **rejects** such a suite rather than judging it; retune or replace the splitter before pointing this at a codebase that names its tests outside ASCII. Point the lint at the file that declares the names, and treat a suite built by any of those routes as unchecked until a later wave measures it.
- `advisory` — the number 3 itself. It is the shortest name that can carry subject, predicate, and object, not a measured optimum; retune it the controlled way, per [`threshold-port`](../threshold-port/SKILL.md), and never by asking an agent to vote on it.

Bob's enforcement corollary is why the split is drawn here rather than wider: *"You can't tell an agent to be clean. You have to measure the cleanliness that they produce and have them correct failures"* ([`martin-canon.md`](../../research/martin-canon.md)). The measured part is enforced; the rest is named as prose and marked as prose.

## Done means

- [ ] `test-name-lint.py` exits 0 over every test file in the changed set, with `--against` pointed at the module under test
- [ ] Each new test names one behaviour, and its name still reads true after the assertions are read
- [ ] The empty case, the boundary, and the raised-error path are present or explicitly noted as absent
- [ ] Mutation status stated (from [`mutant-hunt`](../mutant-hunt/SKILL.md)) — a readable suite with unkilled mutants is documentation of something untested
- [ ] The lint output captured into the evidence packet

An open box means the verdict stays `unverified`: rename or split the test, re-run the lint, re-check the boxes.

**The next agent reads your tests instead of your code — so write the suite it will have to learn the system from.**
