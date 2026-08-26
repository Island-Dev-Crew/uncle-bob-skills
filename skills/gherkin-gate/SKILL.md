---
name: gherkin-gate
description: The red-before-green gate on a story's Gherkin scenarios - the acceptance bar as an executable file bound to its story by content hash, proven failing before implementation and passing after, so it cannot decay the way a prompt rule decays. Reach for it when a story's .feature file exists and its acceptance evidence needs checking, when turning acceptance criteria into a gate instead of a steer, or when the user says "gate the Gherkin", "prove the scenarios red first", or "check the acceptance ledger". Differentiator - this island judges evidence only, and a check-shaped ask gets the verdict rather than an edit to the team's .feature file; authoring the scenarios belongs to the specifier seat and the UI-level QA procedure belongs to the qa-script seat.
---

# Gherkin Gate: the bar you cannot talk out of

The acceptance contract lives on disk, not in the prompt. The relay's specifier seat emits *"a Gherkin… given-when-then stuff. A high level acceptance test"* (C9). This island is the check that turns that file into a gate: every scenario proven red before implementation and green after, bound to its story and to the feature file's exact bytes. One concern: the evidence. Research ground for every non-transcript claim below is [`atdd-gherkin-agile.md`](../../research/atdd-gherkin-agile.md); quotes come only through the [concept ledger](../../docs/01-CONCEPT-LEDGER.md).

## Why a file beats an instruction

A rule in a long prompt is read *"in the Pirates of the Caribbean sense. They're more like guidelines"*. Prominence drains from the middle: *"the 50th and the 80th sentence in there, they're gone"* (C3). An acceptance criterion parked in CLAUDE.md is exactly such a sentence. It decays silently, and nothing reports the decay.

The same criterion written as a scenario in a `.feature` file cannot decay, because nothing about it is being remembered. It gets re-read and re-executed every run, and it answers with an exit code. That is the deterministic-tool loop: *"you must change the code until this tool says that it's okay"* (C4). The research brief reaches the same verdict from the BDD side. Gherkin survives because it is a gate rather than a steer: a pass/fail artifact outside the context window ([research](../../research/atdd-gherkin-agile.md)).

Hold onto the consequence: **an acceptance bar with no file path is not a bar.** This gate takes a path and refuses without one, so a criterion living only as prompt text can never be presented to it.

## What red-before-green buys

A scenario first observed passing proves nothing about the story. It may pass because it asserts nothing. It may exercise pre-existing behavior. It may have been written after the code and shaped to fit it: the bar retro-fitted to the implementation, decayed at the moment of writing. Only a scenario watched failing, then watched passing against the same bytes, has shown it discriminates. That is the pack's own gate ritual generalized from tooling to stories ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)).

The mechanical form of that rule, and the whole of what the gate decides: **for each scenario, the first recorded run is red (non-zero exit) and the last is green (exit 0).** Red-only means unfinished; green-only means unproven; green-then-red means broken.

## The acceptance ledger

Evidence is appended, in run order, to a tab-separated ledger beside the feature file. Five fields, one record per run:

```
phase<TAB>exit_code<TAB>story<TAB>feature_sha256<TAB>scenario
red	1	STORY-42	5cbb55ab…	Empty cart shows the empty state
green	0	STORY-42	5cbb55ab…	Empty cart shows the empty state
```

`feature_sha256` is the sha256 of the feature file's **raw bytes**, so the producer is the obvious one: `shasum -a 256 FEATURE` on BSD/macOS, `sha256sum FEATURE` on GNU. That is exactly what the gate recomputes. Hashing decoded text instead would apply universal-newline translation and silently forgive a CRLF checkout. The binding would still be called "exact bytes" while no longer being over bytes. A stale-evidence refusal prints both digests in full, never a prefix: two shas differing only past character 12 would otherwise print as one value while being refused as two. The 12 hex on the closing summary line labels a single value rather than comparing two, and stays short.

The feature file declares its own story in a Gherkin comment header, `# STORY: STORY-42`. That matches the header convention the [`qa-script-seat`](../qa-script-seat/SKILL.md) stamps on its executables, so both halves of the acceptance surface name the same story the same way.

Five bindings hold the evidence to the artifact, and the gate refuses on each:

| Binding | Refused when |
|---|---|
| **story** | the header is missing, or two headers disagree, or header and invocation disagree, or no record names this story id |
| **content** | a record's `feature_sha256` differs from the feature file's hash right now: the scenarios moved after the run, so the run is stale |
| **coverage** | a scenario head has no valid record, or a record names a scenario the feature does not contain |
| **ordering** | the first valid run for a scenario is not red, or the last is not green |
| **dialect** | the file declares a `# language:` other than `en` (see below) |

A refusal names its line and, where one exists, its scenario. An evidence refusal (no red, still red, stale sha) has exactly three honest repairs: run the missing phase, re-run against the current feature bytes, or fix the code the scenario is refusing. A *structural* refusal is not on that list. Unbound or conflicting header, unnamed or duplicate head, a trimmable-prefixed head, a non-English dialect: the repair for each is to fix the file the message names, then re-run. Both lists name repairs; on a check-only ask they are reported as proposals and not applied (*Running the gate*, below).

Story ids are compared with exact string equality, never a substring or regex test. That is the reason `STORY-4` evidence cannot be laundered into a `STORY-42` pass. Records naming a *different* story are filtered out before judging, not refused: a shared ledger is normal, and exact equality means a foreign record can neither satisfy a scenario here nor be laundered into one. What a foreign record cannot do is substitute for evidence. If filtering leaves nothing, the story binding refuses. Two `# STORY:` headers naming different ids are refused rather than resolved by first-wins: a file two readers bind to two stories is ambiguous, and one of them would be gating on the other's evidence.

A **scenario head** is any of Gherkin's four *English* spellings: `Scenario:`, `Scenario Outline:`, `Scenario Template:`, `Example:`. The language treats `Example:` as a plain synonym for `Scenario:`. Recognising fewer would make a real scenario invisible to the gate, which would then demand no evidence for it and consent. (`Examples:`, the Outline's data table, is not a head and never matches.) A head with no name is refused as unbindable, the way a duplicate name is: there is nothing for a record to name.

Gherkin is i18n by design, and that sentence's own argument applies to the gate. A `# language: de` directive swaps the keywords wholesale: `Szenario:`, `Beispiel:`, accented `Scénario:`, `Escenario:`. A localized head an English-only class cannot see is exactly the invisible scenario described above, real to the runner, evidence-free, consented to. This island does not carry Cucumber's dialect table, so it refuses instead. **A feature declaring a `# language:` other than `en` is refused, exit 1, naming the line and the dialect**; normalise the file before gating it. The directive is matched through the same trimmable prefix as a head (below), so a `# language: de` carrying a leading U+FEFF or a stray control byte refuses too. That prefixed form was a round-2 hole, because cucumber-js honours it and switches dialect. Inside the accepted input space (`en`, declared or defaulted) those four spellings are the *complete* set of scenario keywords, so the coverage claim below is exactly as wide as the check. Two residues stay `advisory`: a runner configured with a non-English default dialect for a file carrying no directive (the gate reads the file, not the runner's config), and a directive prefixed by a character *outside* the trimmable class.

The same argument decides the head prefix, which is read as a deliberately over-wide trimmable class and not as `[ \t]`. The class holds three groups. Unicode horizontal whitespace (U+00A0, U+2007, U+3000), which is what a paste out of Jira, Confluence or Docs carries. The C0 controls and DEL: Java's `String.trim()` strips every codepoint ≤ U+0020, and gherkin-java matches keywords against `lineText.trim()`. And the zero-width/BOM family, since U+FEFF sits in ECMAScript's WhiteSpace production, so cucumber-js trims it and runs the scenario. Deriving that class from Python's `\s` alone was the round-2 hole: a head prefixed with U+FEFF or `\x1b` matched *neither* pattern, so nothing disagreed and the head was dropped rather than refused. Recognising fewer characters hides a real scenario exactly the way recognising fewer keywords does. And a head only one parser can see is ambiguous rather than merely untidy: **a head whose prefix holds any character in that class other than ` ` or `\t` is refused**, exit 1, naming the line and the first such codepoint, never silently normalised. (First, not each: one ambiguous character is enough to refuse the head, and the message says which one to look for.)

The class is enumerated from those two trim rules, not universal, and that is its **disclosed edge**: a head prefixed by something outside it, such as U+202A and the bidi controls, is still dropped silently rather than refused. Neither of those two rules trims a bidi control, so neither of those two runners executes such a head. What a runner this island did not read does with one is not established here, and [`limit-bidi-head.feature`](scripts/fixtures/limit-bidi-head.feature) ships the drop as a captured exit-0 run rather than leaving it undisclosed.

Scenario names and story ids then meet through one documented join key, applied identically to both sides: `str.strip()`, then Unicode NFC. The ledger applies that same `str.strip()` to every field, so a character can never be whitespace to one half of the gate and content to the other. NFC is not cosmetic on macOS: a runner that reports a decomposed name (`e` + U+0301) against a composed head (U+00E9) misses its join, and the gate would report an orphan record for a scenario spelled identically on screen. Case is never folded, so two names differing in case are two scenarios. In the ledger, a line is a **record** if it splits into five tab-separated fields whose first is `red` or `green`; that test runs *before* the `#`-comment skip, so a data row can never be deleted by the comment rule.

## Running the gate

**Read the ask before you run it: report or repair.** The gate only ever reports. It reads the feature file and the ledger, computes, prints, exits; it opens neither path for writing. Repair is a second, separate act, and it edits a team's `.feature` file or their code. Which one is authorised comes from what the user asked for, never from the verdict that comes back.

- **Audit- or diagnosis-shaped ask** - *check the acceptance ledger*, *is STORY-42 gated*, *prove the scenarios red first*, *why is this refusing*. Run the gate, report the exit code and every refusal with the line and scenario it named, and stop there. **The verdict is the deliverable**; the fix-until-green loop is not entered. Name the honest repairs for each refusal as a proposal the human accepts or declines, and perform none of them. A `.feature` file is the [`specifier-seat`](../specifier-seat/SKILL.md)'s artifact and the team's acceptance contract: normalising a U+00A0 head, re-hashing a stale record or rewording a scenario on a check-only ask erases the evidence the check was run to surface, and leaves the ledger binding a story to bytes nobody agreed to.
- **Repair-shaped ask** - *get STORY-42 green*, *fix the acceptance evidence*, *make the gate pass*. Now the loop below is the job: repair, re-run, repeat until the tool consents (C4).

Ambiguous ask: run the gate, report, then ask which. A report costs one re-run; an unwanted repair costs the human a file to reconstruct. The gate itself is already well-behaved here - it refuses a prefixed head or a stale hash rather than normalising either - so every edit that follows a refusal is the reading agent's choice, and on a check-only ask it is not the agent's to make.

```bash
python3 scripts/gherkin-gate.py STORY-ID FEATURE-FILE LEDGER-TSV
```

Three exit codes, three distinct meanings, never shared, so an unreadable path can never be mistaken for a verdict. No fourth status leaves the script's own paths. The thing that kept trying to add one is **120**: CPython re-flushes *both* std streams at interpreter shutdown and replaces the process status with 120 if either raises. A dead stdout pipe reached it first (`gate … | head -1`). Covering fd 1 alone then left a dead stderr pipe reaching it three more ways: a usage error, a `die()` diagnostic, and a verdict whose own broken-pipe report could not be written. So the script now flushes each stream itself while a status can still be chosen, and points the failing fd at the null device; all five forms are captured as runs below. (A fault *before* `main` is reached, such as a failed interpreter start, belongs to Python and not to the gate, and still exits 1.)

- **0** is consent: every scenario bound, hashed fresh, red first and green last.
- **1** is refusal, a real verdict: missing red, still red, stale hash, unbound or conflicting story header, orphan or missing record, a scenario head carrying a trimmable prefix that is not ` ` or `\t`, a non-English `# language:` dialect.
- **2** is usage or input error: an unreadable *or undecodable* file, a malformed ledger line, no scenarios, no records, a stream the gate cannot write to (a closed fd 1, a reader that hung up mid-pipe, *and* a hung-up stderr under a usage or input error), and any unexpected exception. Fail-closed; an empty acceptance file cannot pass. A `.feature` or ledger saved as UTF-16 or latin-1 is a routine editor artifact, and it lands here rather than crashing into 1: a wrapper branching on `1 = refuse` must never read a decode failure as a story that failed. The same reasoning forces the catch-all. Python exits 1 on an unhandled exception, which is this gate's refusal code, so an internal fault would otherwise be filed by CI as a story that failed its acceptance bar. No error path inside the script exits 0 or 1: usage, IO and internal faults all land on 2. A leading UTF-8 BOM is the benign member of that family. It is stripped before the header is matched, rather than hiding the `# STORY:` line and refusing a sound file for the wrong reason. And a U+FEFF *anywhere* else now sits inside the trimmable class, so that strip is no longer the thing carrying the case. The digest still covers it, because the digest is over bytes.

Fix until green (C4), **on a repair-shaped ask only**: repair per the two refusal kinds above, then re-run. Editing the ledger to describe a run that did not happen is the one repair the gate cannot see (below).

**Red/green proof.** The gate earns its `enforced` claims by having been watched failing, and each of its three exit codes by a captured run. Recompute from this island's directory rather than trusting the transcript:

```bash
G=scripts/gherkin-gate.py; F=scripts/fixtures        # capture as: python3 …; rc=$?; echo "EXIT=$rc"
python3 $G STORY-42 $F/checkout.feature            $F/clean-red-then-green.tsv     # exit 0 — 3 scenarios, 0 refusals
python3 $G STORY-70 $F/recu.feature                $F/clean-nfd-record.tsv         # exit 0 — NFD record joins its NFC head
python3 $G STORY-42 $F/checkout.feature            $F/dirty-green-only.tsv         # exit 1 — "first run is green … never proved red"
python3 $G STORY-77 $F/refund.feature              $F/dirty-example-unrecorded.tsv # exit 1 — "no valid red/green evidence"
python3 $G STORY-91 $F/dirty-nbsp-head.feature     $F/dirty-nbsp-head.tsv          # exit 1 — "trimmable character (U+00A0)", 2 refusals
python3 $G STORY-13 $F/dirty-feff-head.feature     $F/dirty-feff-head.tsv          # exit 1 — "trimmable character (U+FEFF)", 2 refusals
python3 $G STORY-24 $F/dirty-ctrl-head.feature     $F/dirty-ctrl-head.tsv          # exit 1 — "trimmable character (U+001B)", 2 refusals
python3 $G STORY-58 $F/dirty-localized-head.feature $F/dirty-localized-head.tsv    # exit 1 — "'# language: de' declares a non-English Gherkin dialect"
python3 $G STORY-35 $F/dirty-feff-language.feature $F/dirty-feff-language.tsv      # exit 1 — same, on a U+FEFF-prefixed directive at line 2
python3 $G STORY-63 $F/dirty-two-story-headers.feature $F/dirty-two-story-headers.tsv  # exit 1 — "declares conflicting stories"
python3 $G STORY-42 $F/checkout.feature            $F/dirty-tail-sha.tsv           # exit 1 — both 64-hex digests printed, differing only at char 64
python3 $G STORY-46 $F/limit-bidi-head.feature     $F/limit-bidi-head.tsv          # exit 0 — LIMIT: the U+202A head is dropped, "1 scenarios"
python3 $G STORY-42 $F/undecodable.feature         $F/clean-red-then-green.tsv     # exit 2 — "input-error: cannot read feature file"
python3 $G STORY-42 $F/checkout.feature $F/clean-red-then-green.tsv 1>&-           # exit 2 — "stdout is closed"
bash -c 'python3 '"$G"' STORY-42 '"$F"'/checkout.feature '"$F"'/clean-red-then-green.tsv | true; echo ${PIPESTATUS[0]}'  # 2 — was 120
# the three dead-STDERR forms, each 120 until the tail flushed both streams. rc printed by the probe itself:
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"'"$G"'","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'                                    # 2 — usage error, hung-up stderr
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"'"$G"'","STORY-42","'"$F"'/undecodable.feature","'"$F"'/clean-red-then-green.tsv"],stderr=w,stdout=subprocess.DEVNULL).returncode)'  # 2 — die() into a hung-up stderr
python3 -c 'import os,subprocess,sys;a,w=os.pipe();os.close(a);b,w2=os.pipe();os.close(b);print(subprocess.run([sys.executable,"'"$G"'","STORY-42","'"$F"'/checkout.feature","'"$F"'/clean-red-then-green.tsv"],stdout=w,stderr=w2).returncode)'  # 2 — both streams hung up
python3 -c "import hashlib,runpy,sys; hashlib.sha256=lambda *a: 1/0; sys.argv=['g','STORY-42','$F/checkout.feature','$F/clean-red-then-green.tsv']; runpy.run_path('$G',run_name='__main__')"  # exit 2 — injected fault is not a refusal
```

Every fixture is a realistic near-miss, not garbage. `dirty-green-only` holds two scenarios properly red-then-green and a third implemented first and only ever recorded passing; it fails on the ordering rule, exit 1, the verdict code. `refund.feature` writes its second scenario with the `Example:` synonym and records nothing for it: the keyword the gate must not overlook, refused on coverage rather than silently consented to. `dirty-nbsp-head.feature` is the indentation twin of that case. Its second head was pasted in with U+00A0 indentation and never recorded, which an ASCII-only class cannot see at all, so it refuses twice: once for the ambiguous head, once for the evidence that head never got. `dirty-feff-head` and `dirty-ctrl-head` are the same shape one class wider, a U+FEFF and an `\x1b` prefix, the two characters that made this check consent in round 2. `dirty-feff-language` is the dialect directive under the same prefix.

`dirty-tail-sha.tsv` is the diagnostic case rather than a bypass: its sha matches the feature's for 63 of 64 characters, so a 12-char display would have printed two identical values while refusing them as different. `limit-bidi-head.feature` is the one fixture that **passes**, and is shipped to prove a limit rather than a guarantee: its U+202A-prefixed head is outside the trimmable class, so the gate reports "1 scenarios" for a file holding two heads. `dirty-localized-head.feature` is the *keyword* twin: a `# language: de` file whose English head is fully recorded and whose `Szenario:` head carries nothing, though a real Cucumber run executes that scenario. Before the dialect binding existed this file consented, exit 0. `dirty-two-story-headers.feature` carries two `# STORY:` lines and likewise used to consent for whichever came first. `recu.feature` is the consent side of the join key: its head is composed, its ledger records decomposed, and the two must meet.

`undecodable.feature` is a latin-1 save with no valid UTF-8 in it, and proves the exit-2 arm is real rather than merely claimed. The closed-stdout, broken-pipe, dead-stderr and injected-fault runs prove the other mouths of exit 2, each against a measured baseline: the unguarded `sys.exit(main(argv))` shape exits 1 on the injected fault (measured), the pipeline form exited 120 before fd 1 was muted, and each of the three dead-stderr forms exited 120 until the tail flushed stderr too. A refusal whose stderr is dead still exits 1, and a consent still exits 0: those paths write nothing to stderr, so no output is lost and the verdict stands. Deleting any fixture returns the corresponding claim to `unverified`.

## Boundaries: who owns what

- **Authoring the scenarios is upstream.** Turning a settled intent doc into a Gherkin spec (one `Feature:` block, concrete example values, declarative behavior-level phrasing) is the [`specifier-seat`](../specifier-seat/SKILL.md), and that seat's own handoff check enforces the file's structure. This island judges what that seat produced and never re-teaches how to write a scenario. Consistent with that split, the gate does not look for a `Feature:` line or grade a scenario's wording; a spec defect goes back to the specifier, not into this gate.
- **The UI-level QA procedure is the other half of the acceptance surface, and is not here.** The human-viewpoint procedure and its determinized executable belong to the [`qa-script-seat`](../qa-script-seat/SKILL.md) (C9). Gherkin gates behavior; that seat gates the system as a human drives it.
- **Behavioral UI assertion primitives are a Forge concern.** The entrypoint contract, checkpoints, stable locators and anti-flake rules are owned by [`computer-use-smoke`](../../COMPANION.md#computer-use-smoke). Nothing here re-implements an assertion primitive.
- **Where the gate fires** (pre-commit, a PostToolUse hook, a CI step) is [`agent-guardrails`](../../COMPANION.md#agent-guardrails). This island supplies the verdict, not the plumbing.
- **The captured stdout plus exit code become one rung of an [`evidence-packet`](../../COMPANION.md#evidence-packet)**, never a second evidence format.

## Enforced vs advisory

`enforced`, meaning a mechanical check exists today and was run in both directions ([`scripts/gherkin-gate.py`](scripts/gherkin-gate.py), fixtures beside it):

- Ordering: first run red, last run green, per scenario.
- Story binding by exact equality on the join key; conflicting `# STORY:` headers refused. Content binding by sha256 over the feature file's **raw bytes**, the value `shasum -a 256 FEATURE` prints.
- Coverage both ways over all four **English** scenario keywords (`Scenario:`, `Scenario Outline:`, `Scenario Template:`, `Example:`) under the trimmable prefix class of Unicode horizontal whitespace, C0 controls and DEL, and the zero-width/BOM family, with both sides keyed by the same `str.strip()` + NFC. Within a feature the gate accepts, every head *that class can see* carries evidence, every record names a real scenario, and duplicate, unnamed or trimmable-prefixed heads are refused rather than skipped. Heads prefixed outside the class are the disclosed limit above, shipped as a fixture.
- Dialect: a feature declaring `# language:` anything but `en` is refused (exit 1) whenever the directive carries at most a trimmable prefix, so no localized head reachable that way is silently outside the coverage claim.
- Exactly three exit statuses leave this script on every path the fixtures and probes above reach: the tail flushes stdout *and* stderr itself and mutes the failing fd, so the interpreter's shutdown flush of either stream cannot promote a chosen status into CPython's 120.
- Diagnostics that carry a comparison print both operands in full: the stale-evidence refusal prints two 64-hex digests, never prefixes of them.
- Contradictions: a `red` record that exited 0, or a `green` record that exited non-zero, is refused rather than counted.
- Ledger parsing: record-shape is tested before the `#`-comment skip, so no evidence row is dropped silently.
- The acceptance bar must be a file. The gate takes a path and exits 2 without one it can read and decode. Exit 2 is isolated from exit 1 on every error path the fixtures and probes above reach, including unexpected exceptions, a closed stdout, a hung-up stdout pipe and a hung-up stderr pipe.
- This island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).

`advisory` at v0, meaning required by this doc but checked by no script yet:

- **The known hole: the ledger is a self-report.** The gate enforces the *shape* of the evidence, not the honesty of the runner. Nothing here proves the red record came from an actual failing run rather than a typed line. Close it by letting the runner append records: an append-only ledger written by CI, each record carrying its run id or commit, with the result captured in [`evidence-packet`](../../COMPANION.md#evidence-packet) format. Until that wiring exists, a ledger nobody watched being written stays `unverified`, never laundered into `verified` ([CONTEXT.md](../../CONTEXT.md)).
- **The i18n residue.** The gate refuses a declared non-English dialect but does not *speak* one, and it reads the file rather than the runner's configuration: a Cucumber configured with a non-English default dialect, against a feature carrying no `# language:` directive, could execute a localized head this gate never sees. Close it by loading Cucumber's own `gherkin-languages.json` keyword sets, or by requiring the directive to be present. A localized feature file is out of scope until then: refused, never gated.
- **The prefix-class residue**, disclosed above and shipped as `limit-bidi-head`: the trimmable class is enumerated from the two trim rules this island actually read, ECMAScript's WhiteSpace production (gherkin-javascript) and Java's `String.trim()` (gherkin-java). It is not derived from a specification and not surveyed across the other runners. A head or a `# language:` directive prefixed by a character outside it is dropped rather than refused. Close it by refusing any head-shaped line whose prefix is not exactly `[ \t]*`, which would also refuse files no runner objects to: a cost this island has not yet judged worth paying.
- **The report/repair separation, on the agent's side.** The script half is `enforced` by construction: it opens the feature file and the ledger read-only (`read_bytes`/`read_text`) and writes only to stdout and stderr, so running the gate cannot alter what it judges. What no check enforces is the reading agent's restraint after a refusal - nothing here stops one from rewriting the `.feature` file on a check-only ask. Close it by running the gate under a permission boundary that denies writes to the story's artifacts ([`agent-guardrails`](../../COMPANION.md#agent-guardrails)), not by adding more prose.
- Whether each scenario asserts what the story actually means (specifier's bar, and mutation testing's job for the unit layer).
- Whether the red run truly preceded implementation in wall-clock time; ledger order is the proxy.
- Scoping the gate to the changed story rather than the whole suite.

## Done means

- [ ] The feature file exists on disk with a `# STORY:` header naming this story
- [ ] Every scenario has a red record captured **before** the implementation commit, and a green record after
- [ ] `gherkin-gate.py` exits 0 for the story at the feature file's current hash
- [ ] The run's stdout and exit code are captured into the evidence packet, with the self-report hole stated

An open box means the verdict stays `unverified`, and on a check-only ask that report is the finished deliverable. On a repair ask, repair by running the missing phase, re-hashing after a scenario edit, or fixing the code. Then re-run the gate and re-check the boxes; the loop ends only when the tool consents (C4).

**A bar that was never watched failing is a guideline; the file that goes red first is the gate.**
