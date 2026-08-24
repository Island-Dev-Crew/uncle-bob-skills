---
name: gate-toolchain
description: Per-language tool map for the pack's two flagship gates - which CRAP scorer and which mutation runner exist for Java, Go, Clojure, JS/TS, Python, PHP, Rust and .NET, what coverage artifact each one eats, and whether it has an incremental or diff mode. Reach for it when standing a CRAP or mutation gate up in a language the harness has not gated before, or when a gate run got too slow to sit inside the agent loop - "which mutation tool for Rust", "is there a CRAP scorer for PHP", "our mutation run takes an hour", "what does crap4go read". Differentiator - this island picks the tool and states its input and mode facts only; the CRAP formula and thresholds belong to crap-gate, the mutation gate contract and diff scoping to mutant-hunt.
---

# Gate Toolchain: the right instrument, in diff mode

Two gates carry this pack: CRAP over what the coder just wrote (C6), and mutation testing over its tests (C7). Both are language-native. The scorer has to read the coverage artifact your test run already produced, and the mutation runner has to speak your compiler. This island is the lookup table between a language and those two instruments. It also carries the one fact that decides whether a gate can live inside the agent loop at all: **does the tool have an incremental or diff mode?**

Every row below is transcribed from the pack's two research briefs, [`crap-metric.md`](../../research/crap-metric.md) and [`mutation-testing.md`](../../research/mutation-testing.md). Where a brief records no mode, the cell says so rather than guessing. An invented flag is worse than an empty cell.

## The CRAP map

| language | tool | coverage artifact it consumes | incremental / diff mode |
|---|---|---|---|
| Java | [crap4java](https://github.com/unclebob/crap4java), Martin's own | JaCoCo instruction counters | **`--changed`**, recorded |
| Go | [crap4go](https://github.com/unclebob/crap4go), Martin's own | `go test -coverprofile` | not recorded; verify at the tool |
| Clojure | [crap4clj](https://github.com/unclebob/crap4clj), Martin's own | Cloverage / LCOV | not recorded |
| JS / TS | js-crap-score | istanbul JSON | not recorded |
| Python | crap4py (port of crap4go/crap4clj; exits non-zero on breach); Qt Coco 7.5 | brief records the port lineage, not the input format; confirm before wiring | not recorded |
| PHP | PHPUnit's built-in code coverage (CRAP column) | PHPUnit's own coverage run | not recorded |
| Rust | cargo-crap | not recorded | not recorded |
| C# / .NET | NDepend, crap4dotnet | not recorded | not recorded |

Three of these are Martin's own repos, still updated. That is also the reason to read them rather than adopt them. Pointing at an exemplar instead of downloading it is [`essence-pointer`](../essence-pointer/SKILL.md)'s concern (C23), not this island's.

## The mutation map

| language | tool | incremental / diff mode |
|---|---|---|
| JVM (Java, Kotlin, Scala) | PIT / pitest | **incremental analysis** reusing prior results, recorded |
| JS / TS | Stryker (stryker-js) | **incremental mode**: ~30 min to under 2 min on a typical PR |
| C# / .NET | Stryker (stryker-net) | not recorded |
| Python | mutmut, cosmic-ray | not recorded |
| Rust | cargo-mutants (zero-config) | not recorded |
| Go | gremlins, go-mutesting | not recorded; whole-module runs still take *hours* on big Go modules |

*Which* mutants a scoped run then selects is [`mutant-hunt`](../mutant-hunt/SKILL.md)'s contract, not this table's: the story diff intersected with covered lines, plus the tool's coverage-targeted mode. The briefs record coverage-targeting as a general acceleration. They name no tool's option for it, so no option name is transcribed here.

That last cell is the whole argument in one line. Google mutates only diff-touched, covered, non-arid lines, one mutant per line, at ~2B LOC ([`mutation-testing.md`](../../research/mutation-testing.md)). Scale did not buy them whole-repo runs; scoping did.

## The hard rule: incremental, or outside the loop

**Inside the agent loop, a gate runs in incremental or diff mode. Whole-repo runs are scheduled work, not loop work.**

The reason is the margin, and the margin is the accounting unit (C5): *"eventually you will slow the agents down to the point where they're slower than humans. And at that point you've lost the game"*. A mutation pass that takes an hour on every story does not harden the pipeline. It eats the thing the pipeline was built to produce. The same arithmetic revived both gates in the first place: mutation testing that once meant an overnight run now means *"maybe it took it 30 minutes instead of an overnight run"* (C7), and CRAP that once meant walking every function by hand now means *"run crap over everything you've just done"* (C6). Thirty minutes is already a stretch for a per-story gate; thirty minutes times every story is a lost game.

So each declared gate takes one of three shapes, and the shape is stated, never assumed:

1. **Tool has a native incremental/diff mode** (crap4java `--changed`, PIT incremental, Stryker incremental). Run it in that mode inside the loop.
2. **Tool has none, but takes a file or line filter**. Feed it the diff's ranges and keep it in the loop. Computing those ranges is [`mutant-hunt`](../mutant-hunt/SKILL.md)'s script, not this island's.
3. **Tool has neither**. It runs on a schedule outside the loop, and every story it did not cover is `unverified` until that run lands. Say that out loud in the evidence; a nightly job is not a per-story gate.

## Declare the choice where a script can read it

A toolchain picked in conversation decays; a toolchain declared in a file gets checked. Write one TSV row per gate you actually run:

```
language<TAB>gate<TAB>tool<TAB>scope_arg<TAB>command
java	crap	crap4java	--changed	crap4java --changed --threshold 6
typescript	mutation	stryker	--incremental	npx stryker run --incremental
```

[`scripts/toolchain-check.py`](scripts/toolchain-check.py) reads that manifest and enforces exactly three claims per row. The tool is the mapped implementation for that language and gate. The command names that tool. The run is really diff-scoped: the declared flag is flag-shaped, present in the command, not negated, and no whole-repo flag sits in either column.

```bash
python3 scripts/toolchain-check.py [manifest.tsv]   # stdin when no file
# exit 0 every row mapped and diff-scoped (--help also prints usage and exits 0)
# exit 1 verdict, a row breaches
# exit 2 usage / IO / closed or unflushable stdout / closed stdin / undecodable /
#        malformed or empty / any other internal error (fail closed) · exit 130
#        interrupted (Ctrl-C, caught only to re-signal it, so a kill reads as a
#        kill). 0, 1, 2, 130 — no other code, and that is sealed rather than
#        assumed: the tail catches argparse's own SystemExit and flushes both
#        streams itself, so a dead output pipe cannot swap CPython's shutdown
#        code 120 in over the verdict. Both spellings are probed below.
```

The scope column is what makes the declaration falsifiable. Before checking it, the script strips shell comments from the command, then splits what survives the way a shell resolves quotes and escapes before any expansion. `shlex` does that splitting. When `shlex` refuses the command outright (unbalanced quotes, a trailing lone backslash), a fallback splits on whitespace and resolves the same escapes and quote marks by hand, so broken quoting cannot smuggle a deny-listed flag past the scan. Every token then keys through one normaliser: Unicode NFC, which also drops a U+FEFF byte-order mark.

Stripping and splitting are two passes, not one parser, so the claim is only the one they are checked on: **both agree where a word starts, and therefore where a comment begins.** The cut honours the same backslash escaping `shlex` does. So `--msg 'it'\''s # 1' --whole-repo` keeps its trailing flag instead of losing it to a "comment", and a `#` that does not start a word (`-Dmessage=fix#123`) is not a comment at all. `"--whole-repo"`, `--whole"-"repo` and a BOM-prefixed `java` are the words they are, not new ones.

**Both columns are read, because a gate can be switched off in either.** Negation wins wherever it sits, and however the scope is spelled. Every token sharing the declared flag's head is scanned, so `--incremental --incremental=false` and `--incremental=true --incremental=false` are both rejected in either order: a command that both enables and disables its own scope is not a scoped run. `--incremental=false` *declared* is rejected too, a scope switched off being no scope. Negation means an `=`-valued spelling: `false/no/off/none`, empty, or a value that reads as zero (`=0`, `=00`, `=0.0`). A space-separated `--incremental false` is two tokens, and is *not* read as negation. That limit is fixtured below.

The whole-repo deny-list reads both columns as well, comparing the flag head, so `--all=true` falls to the same rule as `--all`. `mutmut run --whole-repo` breaches even when the scope column declares a clean `--incremental`, because the deny-listed flag sits in the command that actually runs. Beyond that: `--incremental` declared beside a bare `npx stryker run` is rejected as absent, as is one parked behind a `#`, and a non-flag word like `run` is rejected as not flag-shaped.

Neither the scope check nor the tool check can be satisfied by a substring, but they anchor differently. A bare scope declaration matches on the flag head, so `--in-diff` is answered by `--in-diff=story.diff`. A declaration carrying its own value must match the whole token, so `--in-diff=story.diff` is not answered by `--in-diff=other.diff`. Tool matching runs on whole squashed *segments*. That is why `echo --changed` is rejected as naming no tool, and so is `echo --changed -Dcapital=1` declaring `pit`.

**Red/green proof.** All six fixtures live beside the script. Recompute from this island's directory; these twelve commands gave these exit codes:

```bash
python3 scripts/toolchain-check.py scripts/fixtures/dirty-whole-repo.tsv      # exit 1 — 17 declarations, 16 breaching
python3 scripts/toolchain-check.py scripts/fixtures/clean-diff-scoped.tsv     # exit 0 — 7 declarations, 0 breaching
python3 scripts/toolchain-check.py scripts/fixtures/bom-prefixed-clean.tsv    # exit 0 — 7 declarations, 0 breaching
python3 scripts/toolchain-check.py scripts/fixtures/limit-space-separated.tsv # exit 0 — the disclosed limit, run
python3 scripts/toolchain-check.py scripts/fixtures/tab-hidden-row.tsv        # exit 2 — malformed: line 5: empty field
python3 scripts/toolchain-check.py scripts/fixtures/undecodable-bytes.tsv     # exit 2 — input error: 'utf-8' codec can't decode byte 0xff …
python3 scripts/toolchain-check.py 0<&-                                       # exit 2 — input error: stdin is closed
PYTHONIOENCODING=ascii python3 scripts/toolchain-check.py scripts/fixtures/clean-diff-scoped.tsv  # exit 0 — text degrades, verdict stands
python3 scripts/toolchain-check.py scripts/fixtures/clean-diff-scoped.tsv >&-  # exit 2 — input error: stdout is closed, never a verdict
# the two paths that used to exit 120, plus the interrupt — returncode captured, not piped:
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/toolchain-check.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'    # 2 — usage error onto a dead stderr, not 120
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/toolchain-check.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # 2 — --help onto a dead stdout, not 120
python3 -c 'import signal,subprocess,sys,time;p=subprocess.Popen([sys.executable,"scripts/toolchain-check.py"],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(0.6);p.send_signal(signal.SIGINT);print(p.wait())'  # 130 — a kill reads as a kill
```

The dirty fixture fails for sixteen distinct right reasons, while its first row passes: a `--whole-repo` scope, its `--all=true` spelling, `crap4java` declared as Go's scorer, a `--incremental` claim absent from the Stryker command, one hidden behind a `#`, one negated as `--incremental=false`, one negated in the scope column itself, one negated by `=00`, one carrying *both* spellings at once, a *valued* `--incremental=true` answered by `--incremental=false`, a clean `--incremental` declared over a command that still runs `--whole-repo`, the same breach in quotes (`"--whole-repo"`), the same breach hidden behind the `'\''` escape idiom and a `#`, the same breach after a mid-word `fix#123`, an `echo --changed` that never invokes the tool it declares, and an `echo --changed -Dcapital=1` that declares `pit` and only buries those letters inside `capital`.

The clean fixture answers in the other direction. It holds a two-word binary (`cargo mutants`), a Maven coordinate (`org.pitest:pitest-maven`), a legitimately quoted `# ` argument, a valued scope (`--incremental=true`) honoured by its command, and a non-ASCII path. The gate may reject none of them. So the pair proves the gate discriminates rather than rejecting every file.

Everything that is not a verdict exits 2, never 1 and never 120: malformed rows, a row hidden behind a tab-led `#` (comment detection is anchored to column 1, so no row vanishes unannounced), a missing file, a directory, closed stdin, an empty manifest, a manifest the decoder chokes on, a write that fails on a closed stdout, and a usage error or a `--help` whose output pipe is already dead. An input error must never read as a verdict. A latin-1 em-dash pasted from an editor is a bad file, not a bad row. A UTF-8 BOM is the other side of that principle: it is a file-format artifact, so it is stripped and judged as the word it prefixes, never turned into a bad row. Deleting any fixture returns the gate to `unverified`.

**One disclosed limit, fixtured not fixed.** `limit-space-separated.tsv` exits 0 on `npx stryker run --incremental false`. The scope reads present because negation is only read in its `=`-valued spellings, and a bare `false` in the next token is as often a positional argument as a value. Widening the rule would buy this case at the price of false reds on `--in-diff 0`-shaped arguments, so the claim is narrowed instead: verify a space-separated boolean against your tool once, the way the advisory below already asks you to verify the flag exists.

## Boundaries: what this island owns and what it points at

This island owns **tool selection per language and each tool's input and mode facts**. Nothing else:

- **The CRAP formula, its threshold regimes, and the score's coverage hole** belong to [`crap-gate`](../crap-gate/SKILL.md). It decides *what number fails*; this island decides *which binary computes it*.
- **The mutation gate contract** (diff scoping, zero non-equivalent survivors, kill-tasks, the budget cap) belongs to [`mutant-hunt`](../mutant-hunt/SKILL.md). It decides *what the run must prove*; this island decides *which runner your language has*, and whether that runner can be scoped at all.
- **Where the tool executes** (pre-commit, PostToolUse, a CI step, a nightly schedule) belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails), and the loop machinery around it to [`archipelago`](../../COMPANION.md#archipelago).
- **The captured tool report** enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format as a verification-ladder rung, never a second evidence format.
- **Choosing a model or an agent for a task** is [`model-routing`](../../COMPANION.md#model-routing)'s axis. This island routes nothing but binaries.

## Enforced vs advisory

- `enforced` — the manifest verdict. `toolchain-check.py` rejects a tool that is not the mapped implementation for its language and gate. It rejects a command whose tokens never name that tool as a run of whole squashed segments. It rejects the named whole-repo flags (the `DENY_SCOPE` list, matched on the flag head after shell-quoting *and backslash escaping* are resolved, on the `shlex` path and the fallback alike) **in either column: declared as the scope, or merely sitting in the command that runs**. It rejects any non-flag-shaped scope, and a scope argument absent from the command it claims to be part of. It rejects a negated scope in either column, bare or valued: hidden in a shell comment, answered anywhere in the command by an `=false`/`=off`/`=0`-valued twin, present *and* negated in the same command in either order, or declared falsey itself. It reports every malformed row rather than dropping any. And it exits 2 fail-closed on missing, unreadable, closed-stdin, undecodable, malformed, or empty input, on a closed or unflushable stdout, and on any other internal error, argparse's own usage exit included, so no error path can wear a verdict's code or CPython's 120. Proven red and green above.
- `enforced` — island shape: the pack validator (`scripts/validate-island.py` at the pack root) gates this file's frontmatter, sidecar, ledger citations, script syntax, and line budget.
- `advisory` — **that the flag you declared exists in the tool's CLI, and that the named tool is the process that runs.** The gate checks the flag is flag-shaped and really in your command; it cannot know your tool's option set. A declared `--diff` that the tool ignores passes the gate and fails reality, so verify the flag against the tool once, then let the gate hold it. The tool check likewise compares names with case and separators ignored. It is anchored to whole segments but matched across token joins, so `cargo mutants` satisfies `cargo-mutants` and `org.pitest:pitest-maven` satisfies `pitest`: it catches a command that never mentions the tool, not one that mentions it in passing (`echo mutmut --incremental` passes). Whole-repo spellings outside `DENY_SCOPE` (`--full-run`) still pass in both columns, because the deny-list is a named set, not a semantic judgement. Negation outside its `=`-valued spellings passes too, per the fixtured limit above.
- `advisory` — the map rows themselves. They are transcribed from the research briefs at a point in time; tools ship, rename, and gain modes. A row marked *not recorded* is an instruction to go look, not a verdict that no mode exists.
- `advisory` — the three shapes above (native mode / filter-fed / scheduled outside the loop) and the choice among them. No mechanical check today measures your gate's wall-clock against the margin; [`margin-ledger`](../margin-ledger/SKILL.md) is where that accounting lives.

## Done means

- [ ] Every gate you run appears as a manifest row: language, gate, tool, scope flag, real command
- [ ] `toolchain-check.py` exits 0 over that manifest
- [ ] Each declared scope flag verified once against its tool's own documentation (the advisory gap above, closed by hand)
- [ ] Any tool with no incremental, diff, or filter mode is stated as scheduled-outside-the-loop, and the stories it has not covered are marked `unverified`

An open box means the toolchain claim stays `unverified`. Fix the row (swap the tool, add the scoping flag, or move the run out of the loop), re-run the checker, re-check the boxes.

**A gate the loop cannot afford is not a gate, it is a nightly job wearing a gate's name (C5).**
