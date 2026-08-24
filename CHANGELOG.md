# Changelog

## Unreleased — toward 2.0

Hardening. Phases 1–3 of [07-HARDENING-PLAN-2.0.md](07-HARDENING-PLAN-2.0.md) are complete; phase 4 opened with an independent non-Anthropic review (OpenAI Codex) of the frozen `0eb75eb` head, which returned CHANGES REQUIRED on five pack-level findings. Each was reproduced here before anything was changed.

### Fixed — the proof verifier passed by reading less than it claimed

`verify-proofs.py` had no written grammar, only habits, and three shipped command shapes fell outside them. A **bare island-relative script** (`scripts/diff-scope.sh HEAD~1 HEAD …`) was skipped for its leading token, so `mutant-hunt` and `specifier-seat` — two gates whose entire red/green pair is written that way — reported *0 documented commands* and exited 0. An **exit code stated on the report line below the command's output** (`$ echo $?` / `$ rc=$?; echo "EXIT=$rc"`) was missed by a fixed two-line lookahead, so twenty-five real proofs across `comment-as-spec`, `leak-scan` and `values-not-disciplines` read as unannotated and were never re-run. A **`printf … | python3 gate.py`** stdin pipe was dropped in silence, taking `crap-gate`'s own proof with it.

The grammar is now one definition in the docstring — candidate, proof, allowlist — and every candidate lands in a named class that is printed: run, `PENDING`, `TEMPLATE`, `SKIPPED`, `REFUSED`. Coverage went from 323 executed to **370 of 432 candidates**, and the 62 that do not run now say so by name instead of vanishing. `--strict` makes any PENDING exit 4. A refusal now exits 1 rather than 3, because a block too dangerous to run is a finding, not an absence. `scripts/fixtures/proof-grammar-island` carries all five shapes in one block and was watched going red at 4 before the fix was trusted.

Two more, fixed by hand earlier in the same pass: exit 3 when nothing was executed at all (a verifier that ran nothing has verified nothing), and `margin-ledger` no longer reading a `#123` story id as a comment.

### Fixed — two more error paths wearing a verdict's exit code

The pack names this as its first bypass class, and two of its own tools still had it. `check-graph.py` answered an unreadable or malformed graph file with **exit 1** — the code that means "this architecture has a violation" — so running it from the wrong directory handed a fix-until-green agent a red architecture and it would start moving modules to satisfy a gate that had read nothing. `validate-island.py` recorded a path that is not a directory as a *failed F1 check*, making "I could not find this" indistinguishable from "this island is malformed". Both now exit 2, the code each already used for being called wrong. Neither change touches a documented verdict: the dirty and clean fixtures still exit 1 and 0, and `prove-gate.sh` still accepts the validator.

### Fixed — a claim of enforcement the island itself denies

`plan-decay-detector` advertised, in its discovery sidecar and its frontmatter, that "a gate halts the fleet" — while its own **Enforced vs advisory** section says "no hook wires it into a fleet today" and "this island only rings the bell". It now says it reports and exits 1 to *call* for a re-plan, which a human or a harness then has to honour. A sweep of the other forty-nine sidecars for enforcement verbs found three, each already qualified in its island.

`arch-lens` still told the reader to run its gate from `unclebob/skills/arch-lens`, a path that stopped existing when this pack was separated out of the Forge. Every other `unclebob/` string in the repo is a real GitHub URL of Martin's own tools.

Quote provenance was re-swept while a Codex finding about one smoothed quotation was being checked (it had already been fixed, and matches the ledger exactly). Of 242 quotations across the fifty islands, every one attributed to the conversation or to a book traces to the concept ledger or a research brief; the nineteen that do not are example prompts, tool output strings, and worked-example prose, none presented as anyone's words.

### Fixed — closed exit-code claims, made true

Every gate here publishes a closed set of exit codes, and a caller reads that set to decide whether the code under test passed. Two shutdown paths broke the promise without touching a line of gate logic: CPython replaces the status a script chose with **120** when its own shutdown flush meets a dead stdout — the ordinary `gate.py … | head` idiom is enough — and a shell gate killed by SIGPIPE returns **141**. Neither appears in any island's table.

`scripts/closed-stream-check.py` re-runs every command the islands document as a proof, with stdout closed and then stderr closed, and fails on any code no table names. It reuses `verify-proofs.py`'s grammar rather than keeping a second idea of what counts as a documented command, and it probes the real verdict paths rather than `--help` — the distinction that mattered, since an early usage exit often survived a dead pipe while the path that prints a report did not. Watched red at **41 leaks across 14 islands** before anything was changed; now **702 probes, 0 leaks**.

Eleven Python gates gained the seal they lacked, six shell gates gained a `PIPE` trap, and `leak-scan`'s interrupt probe turned out to have the exact hole it was built to test for — written into a dead stdout it returned 120 itself. Fourteen seals were also printing the literal text `{type(_exc).__name__}` instead of the exception, from a doubled brace inside an f-string, so the diagnostic that was supposed to explain an internal failure explained nothing.

Two gates were turning input they could not read into a verdict. `sys.stdin` takes its error handler from the locale, and on a UTF-8 locale that is `surrogateescape`: undecodable bytes became surrogates and were **scored**, so `crap-gate` printed `BREACH` and `margin-ledger` printed a margin over bytes that were never valid — while the same bytes in a *file* were refused, because that path decoded strictly. `margin-ledger` was worse still: the file path let `UnicodeDecodeError` escape uncaught, and an uncaught exception exits 1, which is its `LOST` verdict. Both now decode strictly on every path and on every machine, and `margin-ledger` publishes the fourth code (3) it had always been able to return.

### Fixed — two scanners read files nobody had pointed them at

Both `leak-scan` and `coverage-gaming-audit` follow symbolic links on purpose: a test suite reached through a symlinked directory is collected and run by pytest, and a scan that refused to descend reported clean over tests it never opened. Following them, though, meant a link inside a scanned tree could aim at a sibling checkout, and the scanner then read — and printed findings from — files outside everything the caller named. Documenting that behaviour was never authority to take it.

Each now resolves every candidate path and refuses, **by name**, any that lands outside the roots it was given; `--allow-root` is how a caller widens the scan deliberately, rather than leaving the decision to a link. The refusal fail-closes at exit 2 instead of pruning in silence, because a quiet prune is the same false green the follow-links default already produced once. Neither is a sandbox, and the docstrings say so: a hard link or a bind mount is a real entry inside the tree and no path test sees through it.

`leak-scan`'s own symlink probe had gone hollow while this was being fixed — its link pointed at a target *inside* the walked root, so the probe passed against a scanner patched to ignore links entirely. It now links outside the root and is watched failing on that patched scanner before it is trusted.

### Fixed — the verifier counted proofs whose scenario it never built

Executing each documented command with only its block's *variable assignments* replayed in front of it meant `D=$(mktemp -d)` ran again for every command, handing each one a different empty directory. The `printf` that writes the fixture into `$D` was classed PENDING and never executed at all, so `coverage-gaming-audit`'s BOM/CRLF proof scanned an empty tree and the fold-cap proof pointed at a file that did not exist. Both were reported as the island's mismatches; both reproduce exactly as documented when the block runs as a block. The tool's docstring had disclosed the false-red direction of this and not the false-green one — a proof that passes because its scenario was never built is the failure this tool exists to catch elsewhere.

A block's earlier unannotated steps now join the prefix and run in one shell with the command, so the substitution is re-evaluated and the fixtures are rebuilt inside the directory it just made. Two shapes still cannot be replayed verbatim — a heredoc body, and a step off the allowlist such as a `cd` or a `(subshell)`. A command behind one of those is **UNSEQUENCED**: it runs, a mismatch still counts, but a match is no longer counted as a verified proof. Running whole blocks in a single shell was tried first and rejected on evidence: an uncaptured heredoc swallowed the generated script and one `cd` relocated everything after it, taking mismatches from 5 to 34.

Two islands retired their own gaps rather than living behind one. `spec-mulch` stated "Run from `scripts/`" in a sentence above the block, which no verifier can read — its commands now carry `bash -c 'cd scripts && …'`. `boyscout-ratchet`'s broken-pipe probe annotated `# exit 2` while the heredoc only *printed* the child's status and itself exited 0; it is now a one-line `python3 -c` that exits the code it reports. That annotation had never been produced by any run.

The pack now stands at **351 verified proofs, 19 unsequenced, 0 mismatched** of 432 candidates — a smaller verified number than the 370 claimed before, and an earned one. The rebuilt verifier was watched going red on two mutants (a gate forced to exit 0, a scanner forced never to flag) before it was trusted.

### Fixed — release documentation that outran the tree

The README said islands 21–50 were unbuilt, counted 21 companion boundaries where COMPANION lists 22, and described `source/` as holding the transcript and captions — which are `.gitignore`d on purpose, because they are the whole of someone else's recorded conversation. The inventory is now counted from the tree, source availability is stated where a reader meets it, and one status section fixes each root document as **live**, **historical**, or **a closed record**, so a planning draft is never read as a current claim.

`02-ROSTER-50.md` and `07-HARDENING-PLAN-2.0.md` carried their original status banners — "DRAFT r2, awaiting Jon's cut" and "plan, not work" — after being, respectively, fully built and three-fifths executed.

### Fixed — install topology, said out loud

The README offered `cp -R skills/crap-gate ~/.claude/skills/`. All fifty islands link outside their own directory (442 distinct relative targets; 42 cite the pack validator or `prove-gate.sh` as the sole evidence for their only `enforced` claim), so that copy severs the evidence graph and keeps only the prose. Full-pack install is now the documented topology and single-island copying is named as a reading copy.

### Fixed — provenance that contradicted itself

`source/README.md` headed a two-command pipeline "Regenerate the transcript in one command". The research briefs cited a private `/private/tmp/…` transcript path that no reader has, `seventies-canon.md` opened "All research verified … UNVERIFIED: none" while its own last line admitted the tactical/strategic vocabulary was not verified, and `lost-in-the-middle.md` said no published URL for the interview was found while `source/README.md` records one. Labels are now per claim, and both briefs point at the regenerable `source/transcript.txt`.

## v1.2 — 2026-08-23

Wave 3: fifteen islands on strategy, economics and education. **The 50-island roster is complete.** 600 mechanical checks.

### Islands

Who decides (`conceptual-integrity-owner`, `no-silver-bullet-triage`, `manageability-review`); fleet economics (`mythical-agent-month`, `do-it-twice`, `change-cost-probe`); structure by secrets (`parnas-partition`, `coupling-budget`); keeping ourselves honest (`measurement-humility`, `egoless-fleet`, `instruction-density-cap`, `plan-decay-detector`); and the education layer (`human-subagent`, `strategy-shelf`, `abstraction-ladder`).

### The honest-script result

Builders were given the tier A/B/C standard, the six bypass classes and the exit-code seal **upfront** this time, and told per island whether a gate was expected. Nine shipped one with fixtures; **six shipped none and said so** — who holds a design, whether complexity is essential, whether a human can restate a change, how to drill a junior. None of that is arithmetic, and a gate around it would be theatre. Front-loading the standard raised the floor without making the critics redundant: two islands passed round one, the rest still failed a critic that forged inputs.

### Fixed — four false greens, each reachable by ordinary input

- `instruction-density-cap` counted **zero** directives in a plainly numbered rules file. Its marker test was a fixed 16-character list, so a bolded `**1.**`, an emoji bullet and `■` were invisible — while `■`'s level-1 and level-2 siblings were on the list, so a three-level list pasted from Google Docs counted its top two and silently dropped the third. Now a Unicode property test, with leading emphasis stripped. All twenty existing documented counts unchanged.
- `measurement-humility` was defeated by **one punctuation mark**: `none?` and `-none-` read as substance and passed REVIEWED, 192 leaking spellings in all. Peeling is now by Unicode category, with the unpeeled spelling kept as a candidate so a bare `?` still registers as the evasion it is, plus a letter-or-digit floor on thresholds.
- `plan-decay-detector` aimed a whole plan at the wrong tree in silence: `--root` defaulted to `.`, so an all-`absent` plan run from an unrelated directory reported PLAN HOLDS and exited 0. `--root` is now required — which is what the island's own exit-code paragraph had promised.
- `strategy-shelf` was fully defeated by an **HTML comment**: its anchor probe stripped code fences but not `<!-- -->`, so commenting out all four Forge anchors still exited 0 while GitHub would emit no anchor for any of them.

### Honest state

The roster is complete; what remains is the hardening pass — cross-model verification, supply-chain and tamper-evidence work — reserved for 2.0. Disclosed limits each ship a fixture capturing the boundary as a run.

## v1.1 — 2026-08-21

Wave 2: fifteen canon-mechanics islands, where the conversation's claims meet the books behind them. Pack total 35 islands, 420 mechanical checks.

### Islands

Structure measured rather than argued (`stability-order`, `component-cohesion`, `interface-budget`, `leak-scan`); comments and errors as design (`comment-as-spec`, `define-errors-out`); drift caught early (`boyscout-ratchet`, `tornado-detector`, `strategic-ledger`); the acceptance surface (`gherkin-gate`, `tests-as-spec`, `acceptance-surface-review`); and three that patrol the pack's own metrics (`coverage-gaming-audit`, `gate-toolchain`, `values-not-disciplines`).

### A harder gauntlet, and a stopping rule

Critics were told to **forge inputs** rather than re-run the author's fixtures, after Wave 1 ended with three gates that separated their own fixtures perfectly and were still bypassable. All 15 islands failed round 1. Four adversarial rounds followed, each closing what it was handed and finding subtler holes — so round 3 replaced "find nothing" with a tiered standard: fix any false green reachable by realistic input, fix-or-disclose hostile-input holes as fixtures, and make every sentence exactly true. That last tier always terminates, and it is where the first law bites hardest: a claim the implementation cannot back is laundering whether or not anything exploits it.

### Fixed

- `comment-as-spec` walked only a class body, so moving methods into a base class hid the entire inherited surface — undocumented members and leaking comments alike. Now resolved transitively through same-module bases, with two fixtures pinning it.
- `coverage-gaming-audit` matched test filenames with an ASCII-only pattern and refused to descend into symlinked directories, while pytest collects and runs both — so `test_café.py` and a symlinked suite were scanned as clean without being read. Fixed, with a real-path visited set so a symlink cycle terminates.
- Five islands' exit-code tables denied a fourth code their scripts could emit: CPython replaces the exit status with **120** when its shutdown flush hits a dead pipe, leaking either through `except SystemExit: raise` re-raising past the seal or through no seal at all. Every island claiming a closed set now emits only the codes it names.
- `known-dirty-fixture` gained *the pair is necessary, not sufficient* — its own thesis corrected by Wave 2, with the six bypass classes found empirically across both waves.

### Added

`scripts/verify-proofs.py` re-runs the commands the islands document and compares exit codes. (It re-ran fewer than this sentence claimed; v2.0 defines the grammar and says what it skipped.) It exists because during this wave the verification method was the broken thing more often than the artifact — `$?` read after a pipe or a command substitution, a `grep -P` returning zero on a pattern that was present, `timeout` absent on macOS. Its own limits are stated in its docstring.

### Disclosed limits

`stability-order` cannot see a pure dependency cycle; `coverage-gaming-audit` cannot see a suite reached only through a `conftest.py` hook and has a fold size cap; `comment-as-spec` cannot resolve an imported or dotted base class. Each ships a fixture capturing the boundary as a run.

## v1.0 — 2026-08-19

First release. Wave 1 of the roster: twenty islands mined from the Robert C. Martin × Matt Pocock conversation on directing AI coding agents.

### Islands

Twenty skills across six concerns — doctrine (`boredom-dividend`, `threshold-port`, `margin-ledger`), the five-seat relay (`seat-relay`, `specifier-seat`, `qa-script-seat`), the gates (`crap-gate`, `mutant-hunt`, `mutant-excusal-ledger`, `dependency-fence`, `known-dirty-fixture`), context economy (`steering-audit`, `priority-zone`, `trajectory-hygiene`), structure (`arch-lens`, `structure-interrogation`), planning (`story-cadence`, `spec-mulch`, `essence-pointer`), and the human (`thrash-watch`). (`human-subagent` and `strategy-shelf` were named in an early roster draft under this heading but were not built until v1.2 — corrected here rather than left claiming a release contained islands it did not.)

### Evidence

- **28 concepts** extracted from the conversation, each carrying a quote verified against the transcript by grep. No island quotes the conversation from memory; every island cites the ledger.
- **Seven research briefs** from primary sources, with unsourced claims flagged `UNVERIFIED` rather than smoothed over. Standing corrections: the C.R.A.P. metric is Savoia & Evans 2007; "Dex Hardy" in the captions is Dex Horthy; a literal 100% mutation kill is unreachable, so the hardener ships an excusal ledger.
- **240 mechanical checks** across the twenty islands, all green. The validator was proven red on a deliberately broken fixture before it was trusted.
- **Twelve gate scripts, each with a red/green fixture pair**, every one executed in both directions.

### Built by gauntlet

Each island was authored by one agent and judged by a blind critic that never saw the build brief. Thirteen passed first time, six after one fix round, one took three. Findings that were caught and fixed rather than shipped:

- An island claiming its checks were "demonstrated against a known-bad fixture" when no fixture existed.
- Invented provenance for a real correction.
- An `enforced` label covering a gate that was partly prose judgment.
- Dead links to islands that do not exist yet.
- A syntax check that wrote `__pycache__` into every island it validated — including two gate scripts carrying the same defect.

Three gates separated their own fixtures but could still be bypassed by inputs the fixtures never tried, each reproduced by hand before being fixed:

- `qa-bind-check.sh` used unanchored matching, so a script with **no binding headers at all** passed the binding gate, as did a superstring hash and a script bound to `<doc>.OLD-REVISION`. All checks are now line-anchored and the doc header is compared by resolved path.
- `mulch-check.sh` interpolated the story id raw into a regex, so `story-1.2` silently matched a `story-142` spec — the exact false positive its own comment promised to prevent.
- `margin-ledger.py` returned the same exit code for an unreadable ledger and a genuine fail-closed verdict, so running it from the wrong directory read as a real result. IO and usage errors now exit 3.

### Known state

Most in-island rules are `advisory` and say so. Islands 21–50 are specified in the roster and not yet built.
