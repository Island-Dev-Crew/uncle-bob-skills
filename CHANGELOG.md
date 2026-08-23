# Changelog

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

`scripts/verify-proofs.py` re-runs every command the islands document and compares exit codes. It exists because during this wave the verification method was the broken thing more often than the artifact — `$?` read after a pipe or a command substitution, a `grep -P` returning zero on a pattern that was present, `timeout` absent on macOS. Its own limits are stated in its docstring.

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
