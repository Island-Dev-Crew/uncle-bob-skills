# Changelog

## v1.0 — 2026-08-19

First release. Wave 1 of the roster: twenty islands mined from the Robert C. Martin × Matt Pocock conversation on directing AI coding agents.

### Islands

Twenty skills across six concerns — doctrine (`boredom-dividend`, `threshold-port`, `margin-ledger`), the five-seat relay (`seat-relay`, `specifier-seat`, `qa-script-seat`), the gates (`crap-gate`, `mutant-hunt`, `mutant-excusal-ledger`, `dependency-fence`, `known-dirty-fixture`), context economy (`steering-audit`, `priority-zone`, `trajectory-hygiene`), structure (`arch-lens`, `structure-interrogation`), planning (`story-cadence`, `spec-mulch`, `essence-pointer`), and the human (`thrash-watch`, `human-subagent`, `strategy-shelf`).

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
