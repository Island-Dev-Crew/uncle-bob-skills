---
name: tornado-detector
description: Trend alarm on files-touched-per-change - Ousterhout's tactical tornado caught while it is still blowing, now that a fast agent can smear one design decision across a codebase in an afternoon. Reach for it when a small feature keeps touching many files, when reviewing a burst of agent-written changes, or when the user says "why does this one-line change touch nine files", "are we accumulating change amplification", "run a tornado check", or "files per feature is creeping up". Differentiator - it raises one threshold alarm on one measured trend and hands anything actionable to the survey island; it never mines churn hot spots, ranks refactors, or judges whether an agent is stuck.
---

# Tornado Detector: change amplification, caught in the act

Ousterhout's **tactical tornado** is the prolific engineer who ships fast and leaves complexity behind. **Change amplification**, one small change forcing edits in many places, is the first of the three symptoms his frame predicts from dependencies and obscurity ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). This island measures exactly one number, **files touched per change**. It watches that number's trend, and alarms when it climbs.

The agent-era sharpening: a tornado no longer needs a prolific human. The conversation supplies both halves of that reading. Agents are tactical engines by nature: *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* ([C25](../../01-CONCEPT-LEDGER.md)). And they run at a speed no human matches: *"They are fast with code. I am slow with code"* (C1). A pattern that used to take one prolific engineer a quarter now takes one fast agent an afternoon. That inference is this island's own, not Bob's. It is `advisory`, and the number below is what makes it checkable.

Why it is worth an alarm rather than a note: mess compounds, and agents degrade on it exactly as humans do: *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). Amplification is the leading indicator; the spin is the bill.

## The signature

**One small feature, many files.** When a change of modest intent touches a wide file set, one design decision is smeared across the codebase. That is Ousterhout's *information leakage* red flag: the same fact reflected in multiple modules ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). The trend matters more than any single change. A repo whose files-per-change drifts upward is dissolving its own module boundaries in real time.

**Look-alikes to filter out before measuring** (all `advisory`: judgment, no script decides them):

- **Sweeps.** Renames, formatter runs, license headers, dependency bumps. Wide by construction, carrying no design decision.
- **Generated and locked artifacts.** Build output, lockfiles, snapshots, compiled schemas. They inflate the count without anyone deciding anything.
- **Genuinely cross-cutting features.** A new locale, a new tenant column. Wide once is a feature; wide every week is a design.
- **Batch size drift.** Bigger stories touch more files honestly. Hold the batch roughly constant, or the metric measures your planning instead of your architecture.

## The measurement

**Grain (advisory).** One row per *feature*: a squash-merged PR or a story, falling back to per-commit when that is all the history you have. Per-commit rows on a branch that commits ten times per feature under-count amplification; per-release rows hide it entirely.

**Extraction (advisory).** Emit `change_id<TAB>files_touched`. Git's native order is newest-first, and a reversed climb reads as a fall. So the scanner has no default order. Capture either way, but declare which (`--reverse` below means `--order oldest-first`), or the scan exits 2 rather than guessing:

```bash
git log --reverse --no-merges --pretty=format:'#%h' --name-only \
    -- . ':(exclude)*.lock' ':(exclude)dist/*' \
  | awk 'BEGIN{OFS="\t"}
         /^#/  { if (id!="" && n>0) print id, n; id=substr($0,2); n=0; next }
         NF    { n++ }
         END   { if (id!="" && n>0) print id, n }' > changes.tsv
```

Confirm the row count against `git rev-list --count --no-merges HEAD` before trusting a verdict; the pathspec exclusions are the noise filter above, and the parser is a convenience, not a proof.

**The row rules the scanner enforces on that file** (each one exits 2 rather than dropping data, because a vanished row is a false green):

- **Comments are anchored to what cannot be data.** A line is a comment only if it holds no TAB and its first non-space character is `#`. Any line with a TAB is a row, so a PR-style id (`#1234<TAB>7`) is *counted*, never skipped, and the grain above may mix `#`-ids with hashes freely. A tab-less line that is not blank and not `#` is malformed, not ignored.
- **Nothing is dropped invisibly.** Every verdict line, green and ALARM alike, prints `parsed N rows, skipped M` — reconcile both numbers against `git rev-list --count`.
- **One row per change, ids unique** under a single key function (NFC + casefold, so `A1B2` and `a1b2` are one change). A repeated id is malformed: averaging one change twice dilutes the window. Ids are one ASCII token, `[A-Za-z0-9._@/:+#-]{1,64}`; a non-ASCII variant is refused, never normalized into some other row.
- **`files_touched` is a bounded integer**, `1 .. 1000000`. Past that the capture is corrupt, not a repo.
- **A leading byte-order mark is refused, not stripped.** U+FEFF is neither whitespace to `lstrip` nor an id character, so a capture saved by a Windows editor already failed closed. But it failed with a generic complaint about line 1 (*expected 2 fields, got 1* when line 1 is a comment, *not a single id token* when it is a row), which invites deleting the line rather than the mark. The scanner names the mark and exits 2. It does not strip it: silently editing the capture it is auditing is the same move as silently dropping a row.

## The alarm

[`scripts/tornado-scan.py`](scripts/tornado-scan.py) compares the mean of the last `--window` changes against the `--baseline` changes immediately before them, and reports its verdict on its exit code. Every code the scanner *chooses* is one of three:

| Exit | Meaning |
|---|---|
| 0 | no tornado signature |
| 1 | ALARM — the only code the scanner chooses that means tornado |
| 2 | everything else, fail closed: usage (an undeclared `--order`, a non-finite threshold), malformed or undecodable input, a leading BOM, insufficient history, a channel that cannot carry the run (closed stdin, closed stdout, an output pipe whose reader is already gone), and any otherwise-unhandled exception — `KeyboardInterrupt` included |

**Every error path exits 2.** A top-level guard converts any escaping error to 2, and every statement *inside* that guard is itself non-raising. The round-2 hole was the guard's own cleanup step raising on a `None` stdout and taking the guard down with it. Delivery is part of the verdict: if the final flush cannot complete, the run exits 2 rather than report a verdict nobody received. One delivery failure keeps the computed code, and only one: a reader who hangs up *after* the write lands (`| head -1` at this output size). The verdict was already on the wire, so 0 stays 0 and 1 stays 1. A fourth number can still reach a CI consumer, and it is not one the scanner chooses. A signal that terminates the interpreter outright never runs the guard (`SIGTERM` → 143, `SIGKILL` → 137, as the shell reports them). `SIGINT` *is* caught, and becomes 2. Two independent rules follow, either one enough to alarm; exactly-at passes for both:

| Rule | Breach | What it catches |
|---|---|---|
| climb | `recent / base > --climb` | amplification arriving now — the tornado while it blows |
| ceiling | `recent > --ceiling` | amplification already at steady state — the wreckage it left |

**The defaults (`--window 5 --baseline 10 --climb 1.5 --ceiling 8`) are advisory placeholders, not findings.** Neither Ousterhout nor the conversation supplies a files-per-change number. These are starting points, sized so a fifteen-change history yields a verdict. Calibrate them against your own repo the way any threshold moves when the worker changes (C17), through the empirical loop [`threshold-port`](../threshold-port/SKILL.md) owns. And remember that an agent's opinion on the right number is a hypothesis: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18).

**Red/green proof.** The scanner earns its `enforced` line by having been watched failing, through the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Nine fixtures, eighteen runs, from this island's directory. Read the code with `rc=$?; echo "EXIT=$rc"` on its own line: after a pipe `$?` is the pipe's status, not the scanner's, which is why the two pipe runs end in `exit ${PIPESTATUS[0]}`. **Run the block in `bash`, and note the `bash -c` on those two runs is load-bearing, not decoration:** `PIPESTATUS` is a bash array, so in zsh 5.9 `${PIPESTATUS[0]}` reads as `0` and the alarm run below reports a clean pass, the reader's shell silently inverting the verdict. zsh's own spelling is `${pipestatus[1]}`. (`>&-` itself works in both shells; those runs are wrapped only to keep the block one shell wide.)

```bash
export LANG=en_US.UTF-8   # a strict-decode locale: the input channel must not change the verdict
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/dirty-climbing-trend.tsv    # exit 1 — climb 6.00/2.00 = 3.00x > 1.50x
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/dirty-flat-high.tsv         # exit 1 — ceiling 9.00 > 8.00
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/dirty-pr-ids.tsv            # exit 1 — '#1234' PR ids are rows, not comments
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/clean-rising-tolerated.tsv  # exit 0 — 1.33x climb, recent 4.00
python3 scripts/tornado-scan.py --order newest-first scripts/fixtures/dirty-climbing-reversed.tsv # exit 1 — same tornado, git's native order
python3 scripts/tornado-scan.py scripts/fixtures/dirty-climbing-reversed.tsv                      # exit 2 — order undeclared, never a silent pass
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/dirty-non-utf8.tsv          # exit 2 — undecodable bytes, distinct from ALARM
python3 scripts/tornado-scan.py --order oldest-first < scripts/fixtures/dirty-non-utf8.tsv        # exit 2 — the same bytes down the stdin channel
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/malformed-huge-count.tsv    # exit 2 — count past the bound; was an OverflowError at exit 1
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/malformed-duplicate-id.tsv  # exit 2 — one change listed twice under two spellings
python3 scripts/tornado-scan.py --order oldest-first --climb nan --ceiling nan \
        scripts/fixtures/dirty-climbing-trend.tsv                                                 # exit 2 — non-finite threshold, not a disabled gate
python3 scripts/tornado-scan.py --order oldest-first 0<&-                                         # exit 2 — stdin closed (sys.stdin is None)
printf 'a1\tnine\n' | python3 scripts/tornado-scan.py --order oldest-first                        # exit 2 — malformed
python3 scripts/tornado-scan.py --order oldest-first scripts/fixtures/malformed-bom.tsv           # exit 2 — leading BOM, named not stripped
bash -c 'python3 scripts/tornado-scan.py --order oldest-first \
        scripts/fixtures/clean-rising-tolerated.tsv >&-'                                          # exit 2 — stdout closed; was exit 1, a false tornado on the GREEN fixture
bash -c 'python3 scripts/tornado-scan.py --help >&-'                                              # exit 2 — same rule, checked before argparse; was exit 1
bash -c 'python3 scripts/tornado-scan.py --order oldest-first \
        scripts/fixtures/clean-rising-tolerated.tsv | true; exit ${PIPESTATUS[0]}'                # exit 2 — output pipe read by nobody, verdict undelivered
bash -c 'python3 scripts/tornado-scan.py --order oldest-first \
        scripts/fixtures/dirty-climbing-trend.tsv | head -1 >/dev/null; exit ${PIPESTATUS[0]}'    # exit 1 — reader hung up MID-stream; the verdict was already on the wire
```

Each dirty fixture isolates one failure. `dirty-climbing-trend` stays *under* the ceiling (recent 6.00), so only the climb rule can fail it; `dirty-flat-high` is *flat* (1.00x), so only the ceiling rule can. The clean fixture is a rising trend (3.00 → 4.00) that the gate must still pass, which is what proves it discriminates instead of rejecting every repo that breathes. `dirty-climbing-reversed` is that same tornado captured in git's native order: declared, it still alarms; undeclared, it exits 2 instead of reading the climb as a fall. `dirty-non-utf8` isolates the same way. It is `dirty-climbing-trend`'s exact 15 rows with a raw `0xff` byte in the last change id, so strip the byte and the history ALARMs at exit 1, while corrupted it exits 2. That is the discriminating fact behind *exit 1 meaning tornado and nothing else*: the decode error *preempts* an otherwise-alarming history rather than being read as one.

The remaining runs are holes a critic forged and this gate now closes, each kept as a captured run rather than a sentence. `dirty-pr-ids` is the false green that mattered most: fifteen quiet rows plus five twenty-file changes whose ids are written `#300`…`#304`. Under a `startswith("#")` skip those five rows vanished, the window slid back onto the quiet history, and identical data exited 0. One character of id format flipped a two-rule ALARM into a clean pass. `malformed-huge-count` carries a 400-digit count that used to reach `mean()` and raise `OverflowError`, exiting *1* on a history whose real verdict was 0: an error wearing the tornado code. `malformed-duplicate-id` lists one change as `a1b2c3d` and `A1B2C3D`. The `nan` run is the threshold guard: `nan <= 0` is False, so a bare guard passed it and then `nan` defeated both rules, printing "3.00x climb" beside a green verdict. `malformed-bom` applies that same discipline to the likeliest editor artefact there is. It is `dirty-climbing-trend`'s exact 15 rows behind a byte-order mark, so deleting three bytes returns the file to exit 1.

**The closed-stdout runs are the round-3 correction, and they are the reason this island counts three channels rather than two.** With fd 1 closed at exec, CPython sets `sys.stdout` to `None`. `print()` goes quiet, the top-level flush raises `AttributeError`, and, worse, the guard's own cleanup step called `sys.stdout.fileno()` on `None` and raised *inside* the handler. So `sys.exit(2)` was never reached, and the interpreter fell through to its default exit *1*. Every path collapsed onto the code reserved for tornado: the green fixture, the malformed fixture, an undeclared `--order`, even `--help`. The scanner now refuses at 2 the moment it has no channel to deliver a verdict on, checked before argparse so `--help` is covered by the same rule, and every statement inside the guard is non-raising. The explicit `LANG` and the channel arms are load-bearing, and **all three channels have to be watched separately or one of them ships unwatched**: `sys.stdin` decodes strictly under a normal locale, a *closed* stdin leaves `sys.stdin` `None`, and a *closed* stdout leaves `sys.stdout` `None`. Stdin was watched and stdout was not. That is exactly how a false tornado on this island's own green fixture survived two adversarial rounds. Deleting any fixture, or any channel, returns the gate to `unverified`.

## When the alarm fires

1. **Re-run with the noise filtered.** Exclude sweeps and generated paths, then re-scan. A filtered alarm is a real one.
2. **Name the smeared decision.** Open the widest recent change and say, in one sentence, which single decision required all those files. If no such sentence exists, the batch was just big. Say so and move on.
3. **Hand it over.** A confirmed alarm is a symptom with a location, not a refactor plan. It graduates to [`arch-survey`](../../COMPANION.md#arch-survey), which owns the discovery side entirely.
4. **Re-verify after the repair lands.** Re-extract, re-scan, and require exit 0 over a window that contains the post-repair changes. An alarm that was argued down instead of measured down stays `unverified`.

## Boundaries

- **[`arch-survey`](../../COMPANION.md#arch-survey) owns churn mining, the deep-module deletion test, and ranked before/after refactor reports.** This island raises **one trend alarm on one metric** and stops. It does not rank hot spots, score modules, propose splits, or estimate payback. The moment an alarm becomes actionable it goes there.
- **[`thrash-watch`](../thrash-watch/SKILL.md) is the sibling, and the line between them is sharp - a tornado ships successfully while spreading damage; thrash fails to ship at all.** Thrash-watch reads a *live agent's behavior* over turns: circling, break-one-fix-another, the give-up. This island reads *merged history* over changes, and its subject is green, passing work whose blast radius is growing. Green tests plus a climbing trend is this island. Red tests and a stuck agent is that one.
- **Detecting the duplicated decision itself is [`leak-scan`](../leak-scan/SKILL.md)'s concern** (roster line 28, [`02-ROSTER-50.md`](../../02-ROSTER-50.md)). Files-per-change is the cheap outer signal; the duplicate-knowledge report is a different instrument, and this island never grows one.
- **The captured scan enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format.** The scanner's stdout plus its exit code become one rung of that packet's ladder, never a second evidence format.

## Enforced vs advisory

- **`enforced`** (a mechanical check exists today and was run): the arithmetic and the verdict of `scripts/tornado-scan.py`. That covers window means, climb ratio, ceiling comparison, exit 1 on breach, and exit 2 fail-closed on malformed or undecodable input, an anchored comment rule under which no data row can vanish, a leading BOM, duplicate ids, an out-of-range count, a non-finite threshold, an undeclared row order, insufficient history, a closed stdin, a closed stdout, an output pipe whose reader is already gone, and any otherwise-unhandled exception including `KeyboardInterrupt`. So exit 1 is the only code the scanner exits with that means tornado, on the file channel, on stdin, and on the output channel alike. Codes 143/137 from a signal that kills the interpreter are outside the guard, and are named in the exit table above rather than claimed away. The printed comparison also widens its precision whenever two-decimal rounding would make an ALARM line read as `9.00 > 9.00`, so the message can never contradict the comparison the verdict used. Watched failing across the block above: five ALARM at exit 1, twelve fail-closed at exit 2, one clean green at exit 0. This island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- **`advisory`** (stated, judged, never auto-blocked): the change grain, the git extraction pipeline and its noise filters, the four look-alike exclusions, every default threshold, the agent-era reading of C25, and the handoff itself. No hook runs this scanner on merge yet, and nothing verifies that a row corresponds to one feature. Each is written so a later wave can mechanize it; claiming any of them as enforced would launder judgment into evidence ([CONTEXT.md](../../CONTEXT.md)).

## Done means

- [ ] Change rows extracted at a stated grain, their order declared to the scanner via `--order`, noise paths excluded, the scanner's own `parsed N rows, skipped M` reconciled against `git rev-list --count`
- [ ] Thresholds declared with their basis named: default placeholder or calibrated, never an agent's vote (C18)
- [ ] `tornado-scan.py` run and its full output plus exit code captured, not summarized
- [ ] Every alarm either handed to `arch-survey` with the smeared decision named, or dismissed in writing with the look-alike that explains it
- [ ] Post-repair re-scan exits 0 over a window containing the new changes

An open box means the verdict stays `unverified`: fix the extraction or the code, re-scan, re-check the boxes.

**A tornado passes every test on its way through. Measure the blast radius, or you will only find out when the agents start to spin (C2).**
