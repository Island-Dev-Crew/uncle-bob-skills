---
name: change-cost-probe
description: Measure what a change actually costs in your repo - minutes or tokens per story through the pipeline - and gate the trend, because a rising cost curve is what accumulating mess looks like from outside the code, and because the measured price is what sets planning depth honestly. Reach for it before asserting that change is cheap, when stories that used to take an hour keep taking three, or on "is our cost of change rising", "measure cost per story", "how expensive is change here", "how much should we plan upfront". Differentiator - it trends one absolute cost in the agent lane across finished stories; the agent-versus-human ratio belongs to margin-ledger and live struggle to thrash-watch.
---

# Change Cost Probe: test the $1 house against your own repo

The doctrine this island serves is an economic claim: *"the cost of change has plummeted to as close to zero as I think we're ever going to get it… why would you do this upfront planning because that's expensive. Why wouldn't you just fiddle fiddle fiddle fiddle until it looks right?"* ([C21](../../01-CONCEPT-LEDGER.md)). It is a good argument. It is also, in your repo, an unverified one — and the pack's first law does not exempt arguments it likes ([CONTEXT.md](../../CONTEXT.md)). So measure the price of a change here, watch which way it moves, and let the number decide instead of the parable.

Two questions come back from one measurement:

1. **Is the price rising?** Mess compounds and agents degrade on it exactly as humans do — *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). Before the spin, the stories still ship; they just cost more each time. A climbing cost curve is that bill arriving early.
2. **How deep should the plan be?** Where change is genuinely near-free, fiddling beats planning (C21). Where it is expensive, that is **data about the codebase**, not an argument for more upfront design — the honest reading of a high price is "changes here are dear", and the reply is to find out why, not to write a longer plan.

The cost-curve history the argument rests on is in [`atdd-gherkin-agile.md`](../../research/atdd-gherkin-agile.md): Boehm's TRW/IBM data put late fixes at up to ~100x, which made front-loading rational, and XP's premise was that flattening the curve makes small batches rational instead (the brief flags Beck's exact wording as `unverified`, secondary-sourced). Bob's 2026 claim is that agents flatten it further. This island is the check on that claim in one repo at a time.

**The leading-indicator reading is this island's inference, not Bob's** — C2 gives the spin, not its price signature. It is `advisory`, and the gate below is what makes it checkable.

## What to measure

One row per **story** that went end to end through your pipeline, in one unit:

```
story <TAB> cost
```

- **`cost` is wall-clock minutes or total tokens** for that story from intake to the last gate consenting — the relay's whole run, not one seat's. Whichever you pick, keep it for the life of the file; the scanner cannot see that row 11 switched from minutes to tokens, and says so.
- **Grain is one story** (advisory). Rows per commit measure your commit habit; rows per release hide everything. Keep batch size roughly constant, or the curve measures your planning rather than your codebase.
- **No extractor ships here** (advisory). Minutes come from wall clock around the run, tokens from your harness's own usage log. The row format is the contract; how you fill it is yours.
- **Confounders to name before believing a climb** (advisory, judgment): stories that got bigger, a model or harness swap, a newly added gate (that one is [`margin-ledger`](../margin-ledger/SKILL.md)'s question, not this one), and infrastructure flakiness. A climb with a confounder attached is a hypothesis; a climb without one is a finding.

## The rules the scanner enforces on that file

Violating any of these **refuses at exit 2** rather than dropping data, because a vanished row is a false green — and the first rule exists so that a legitimate row cannot be read as a comment in the first place, whichever separator survived the editor, while the last is a reporting behaviour with no exit path of its own:

- **The comment rule and the `#` id rule are disjoint by shape, in both directions.** A line is a comment only if it holds **no TAB** and its first non-space character is `#`; a story id that leads with `#` must be `#` followed by **digits** — the ticket-number idiom. So `#312` is a *row*, counted (the naive `startswith("#")` skip is a live false green, evidenced below), and `#note1<TAB>20` is **refused at 2** rather than counted as a story. The mirror direction is closed the same way: a no-TAB line whose first whitespace-separated token is a `#`-digit id **and which carries a second token** — `#301    60`, a row whose TAB an editor's `expandtab` (or a copy-paste, or a markdown round-trip) turned into spaces — is **refused at 2** rather than skipped as an annotation. Both directions were watched failing on a real 3.00x climb: five TAB-carrying annotations dragged it to an exit-0 `0.50x` (`dirty-tabbed-comment`), and five space-mangled rows `#301`…`#305` dropped out of the file entirely for an exit-0 `1.00x` (`dirty-spaced-hashid`). The second one is the worse of the two, because the line-count reconcile in the Done-means box still balances over it.
- **One row per story, ids joined under one key** (NFC + casefold, so `CHK-01` and `chk-01` are one story and the duplicate is refused). Ids are one ASCII token, `[A-Za-z0-9._@/:+#-]{1,64}`; a non-ASCII id is **refused, never normalized**, so an NFC/NFD pair (routine on macOS) cannot split one story into two rows behind your back.
- **Cost is a positive finite number in `(0, 1e9]`.** Zero is not a free change, it is an unrecorded one, and a 400-digit cost is a corrupt capture rather than a repo.
- **Line endings do not change the verdict.** CRLF is normalized; a leading byte-order mark is **named and refused**, not stripped — silently editing the capture it is auditing is the same move as silently dropping a row.
- **Row order is declared, never guessed.** `--order` has no default: git's native order is newest-first, and a reversed climb reads as a fall.
- **No line that could carry a story's cost is dropped, and every line is counted.** A `#`-digit-led line holding a second token is refused at 2 whether its separator is a TAB or spaces, so the only lines the scanner skips are annotations that could never have been a valid row. Every verdict prints `parsed N rows, skipped M comment lines, B blank`. Blank lines carry no cost, so they are not a false green — but they were previously invisible to both counters, which made the reconcile below impossible to complete by counting. Rows + comments + blanks now equals the capture's own line count exactly (a trailing newline is a terminator, not a line).

## The gate

[`scripts/cost-trend.py`](scripts/cost-trend.py) compares the mean of the last `--window` stories against the `--baseline` stories immediately before them, on one rule: `recent / base > --climb` is RISING. Exactly-at passes.

| Exit | Meaning |
|---|---|
| 0 | STEADY — the price is flat or falling, or rising within tolerance. `--help` on a live stdout also exits 0, printing usage and computing nothing; that is a help screen, not a STEADY reading |
| 1 | RISING — the only code this scanner *computes*. One latent path can also reach 1 without computing a verdict: the mandated exit seal maps a `SystemExit` carrying a **string** payload to 1. No call path in this file reaches it — every `sys.exit` here passes an `int` and argparse always does, probed below with `--nope`, `--help`, dead stdout, dead stderr and `SIGINT` (all 0 or 2) — so it is latent, not live. It is disclosed rather than patched because the seal is prescribed verbatim by the pack; a future `sys.exit("message")` added to this file would land on it |
| 2 | everything else, fail closed: usage (a missing `--order` or `--unit`, a non-finite threshold, a window below 1), unreadable or undecodable input, a leading BOM, a malformed row, a `#word` story id, a `#`-digit line carrying a second token but no TAB, a duplicate story, a non-positive or out-of-range cost, insufficient history, a closed stdin, a closed or dead output channel, and any otherwise-unhandled exception including `KeyboardInterrupt` |

A **fourth number** can still reach a CI consumer and it is not one the scanner chooses: a signal that kills the interpreter never runs the guard (`SIGTERM` → 143, `SIGKILL` → 137, as the shell reports them). `SIGINT` *is* caught — it becomes `KeyboardInterrupt` inside the guard and exits 2, probed below.

**`--window 5 --baseline 10 --climb 1.5` are advisory placeholders, not findings.** Neither the conversation nor the research supplies a climb ratio, a window size, or a cost-per-story number **for your repo**. C5's pipeline math — a full relay at roughly an hour per story against about half a day for a human — is Bob's stack on his machine, an anchor for [`margin-ledger`](../margin-ledger/SKILL.md)'s ratio rather than a threshold you can adopt here. Calibrate them the way any threshold moves when the worker changes (C17), through the empirical loop [`threshold-port`](../threshold-port/SKILL.md) owns — and remember that an agent's opinion on the right number is a hypothesis: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18).

**`--cheap` is advisory by construction.** It labels the recent mean `CHEAP (fiddle beats plan)` or `PRICEY`, answering question 2 above, and it is **not part of the verdict**: no value of it turns STEADY into RISING or back. The one way it can touch an exit code is by being refused — a non-finite or non-positive `--cheap` is a usage error at 2, like any other. There is no universal price at which planning becomes rational, so this island ships no default for it.

### Red/green proof — run, not asserted

The gate earns its `enforced` line by having been watched failing, per the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual — and that island's own sharpening applies: the pair shows the gate *can* fail, not that it cannot be fooled, so the forged inputs below are kept as captured runs. Sixteen fixtures, thirty-four runs, from this island's directory. Read codes with the command's own status; after a pipe `$?` is the pipe's, which is why the piped runs end in `exit ${PIPESTATUS[0]}` inside `bash -c` (`PIPESTATUS` is a bash array — in zsh it reads as `0` and inverts the verdict).

```bash
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-rising-cost.tsv        # exit 1 — 40.00/20.00 = 2.00x climb
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-hashid-stories.tsv     # exit 1 — the expensive stories are numbered 301..305
python3 scripts/cost-trend.py --order newest-first --unit minutes scripts/fixtures/dirty-rising-reversed.tsv    # exit 1 — same climb, git's native order
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-rising-crlf.tsv        # exit 1 — same file saved by a Windows editor
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/clean-rising-tolerated.tsv   # exit 0 — 1.25x climb, under tolerance
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/clean-blank-gaps.tsv          # exit 0 — 'parsed 15 rows, skipped 2 comment lines, 3 blank' = 20 lines
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-tabbed-comment.tsv      # exit 2 — '#note1<TAB>20'; was exit 0 at 0.50x over a real 3.00x climb
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-spaced-hashid.tsv       # exit 2 — '#301    60', TAB expanded to spaces; was exit 0 at 1.00x over the same real 3.00x
python3 scripts/cost-trend.py --order oldest-first --unit minutes < scripts/fixtures/dirty-spaced-hashid.tsv     # exit 2 — the same mangling down the stdin channel
python3 scripts/cost-trend.py --order newest-first --unit minutes scripts/fixtures/dirty-spaced-hashid.tsv       # exit 2 — refused before --order can matter
bash -c 'printf "#9001 900\n" | python3 scripts/cost-trend.py --order oldest-first --unit minutes; exit ${PIPESTATUS[1]}'                                       # exit 2 — one hand-typed row is enough
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/limit-subunit-rounding.tsv    # exit 1 — LIMIT: correct verdict, means both print 0.00 (see advisory)
python3 scripts/cost-trend.py --order oldest-first --unit minutes --cheap 30 scripts/fixtures/clean-rising-tolerated.tsv  # exit 0 — CHEAP label, verdict unchanged
python3 scripts/cost-trend.py --unit minutes scripts/fixtures/dirty-rising-cost.tsv                             # exit 2 — order undeclared, never a silent pass
python3 scripts/cost-trend.py --order oldest-first scripts/fixtures/dirty-rising-cost.tsv                       # exit 2 — unit undeclared, no unlabeled evidence
python3 scripts/cost-trend.py --order oldest-first --unit minutes --climb nan scripts/fixtures/dirty-rising-cost.tsv     # exit 2 — non-finite threshold, not a disabled rule
python3 scripts/cost-trend.py --order oldest-first --unit minutes --window 0 scripts/fixtures/dirty-rising-cost.tsv      # exit 2 — empty window
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-bom.tsv            # exit 2 — leading BOM, named not stripped
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-nfd-id.tsv         # exit 2 — non-ASCII id refused, not normalized
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-duplicate-id.tsv   # exit 2 — one story under two spellings
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-huge-cost.tsv      # exit 2 — 400-digit cost; was inf, exiting 1
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-zero-cost.tsv      # exit 2 — a story logged at 0 hid a real climb
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-short-history.tsv  # exit 2 — 9 stories, need 15
python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/malformed-non-utf8.tsv       # exit 2 — undecodable bytes, distinct from RISING
python3 scripts/cost-trend.py --order oldest-first --unit minutes < scripts/fixtures/malformed-non-utf8.tsv     # exit 2 — the same bytes down the stdin channel
python3 scripts/cost-trend.py --order oldest-first --unit minutes 0<&-                                          # exit 2 — stdin closed (sys.stdin is None)
bash -c 'printf "a1\tnine\n" | python3 scripts/cost-trend.py --order oldest-first --unit minutes; exit ${PIPESTATUS[1]}'                                       # exit 2 — malformed cost on stdin
bash -c 'python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/clean-rising-tolerated.tsv >&-'                                    # exit 2 — stdout closed at exec
bash -c 'python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/clean-rising-tolerated.tsv | true; exit ${PIPESTATUS[0]}'          # exit 2 — nobody read the verdict
bash -c 'python3 scripts/cost-trend.py --order oldest-first --unit minutes scripts/fixtures/dirty-rising-cost.tsv | head -1 >/dev/null; exit ${PIPESTATUS[0]}' # exit 1 — reader hung up AFTER the verdict landed
bash -c 'python3 scripts/cost-trend.py --help >&-'                                                              # exit 2 — checked before argparse
```

Three more probes reach codes a shell cannot easily produce. The first two matter because a dead pipe at interpreter shutdown replaces the status with **120**, and `except SystemExit: raise` would let argparse's usage exit leak past a seal; the third is the interrupt. All three printed `2`:

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/cost-trend.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # prints 2, not 120
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/cost-trend.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # prints 2, not 120
python3 -c 'import os,signal,subprocess,sys,time;r,w=os.pipe();p=subprocess.Popen([sys.executable,"scripts/cost-trend.py","--order","oldest-first","--unit","minutes"],stdin=r,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);os.close(r);time.sleep(0.6);os.kill(p.pid,signal.SIGINT);print(p.wait())'  # prints 2 - SIGINT while blocked on stdin
```

Each dirty fixture isolates one hole. Five are reproducible by removing the named guard(s) from the script — **four false greens and one false alarm** — and one more (`limit-subunit-rounding`) is a boundary this island discloses rather than closes:

- **`dirty-hashid-stories`** — twenty quiet stories at 20 minutes, then five at 60 whose ids are ticket numbers written `#301`…`#305`. Under a `startswith("#")` comment rule those five rows vanish, the window slides back onto the quiet history, and identical data exits **0** at a computed ratio of 1.00 instead of 3.00. One character of id format flipping an alarm into a clean pass.
- **`malformed-huge-cost`** — the *clean* history with a 400-digit cost on its last row. This one is a false **alarm**, not a false green, and it needs **both** guards removed: with only the finite check deleted the range guard still catches it (`cost must be in (0, 1000000000], got inf`, exit 2). With the finite check **and** the `(0, 1e9]` range guard removed, `float()` yields `inf`, the recent mean is `inf`, and the run prints `RISING recent(5)=inf climb infx > 1.50x` and exits **1** on a history whose real verdict is 0 — an error path wearing the alarm's code.
- **`dirty-tabbed-comment`** — an honest 3.00x climb followed by five `#noteN<TAB>20` annotation lines. Remove the `#`-leading-id digit rule and those five parse as stories: the baseline climbs to 40, the window falls to 20, and the file exits **0** at `0.50x` over an unchanged set of real stories. The ordinary human comment form (`# re-baselined here<TAB>20`) always failed closed at 2 — an id cannot hold spaces — so *that direction* of the hole was only ever reachable by a comment written as one bare token plus a TAB plus a number. The mirror direction, a row read as a comment, is reachable by one bare token plus a **space** plus a number, and ships as its own fixture below.
- **`dirty-spaced-hashid`** — the mirror, and the reason the bullet above no longer says "only". Twenty quiet stories at 20 plus five hand-typed ticket rows `#301    60`…`#305    60` whose TAB became spaces the ordinary way an editor with `expandtab`, a terminal copy-paste, or a markdown round-trip does it. Remove the no-TAB half of the `#`-id rule and the comment branch eats all five: the window slides back onto the quiet history and a real **3.00x** climb exits **0** at `1.00x`, the same false green `dirty-hashid-stories` documents, reached from the other side of the same rule. The aggravator is that the island's own human safety net passes over it — `parsed 20 rows, skipped 6 comment lines, 0 blank` sums to 26, which is the file's `wc -l`, so the Done-means reconcile balances on a ledger with five data rows missing. The control is `CHK-16 900`: the identical mangling on a non-`#` id has always exited 2 at the field parser, which is what makes the asymmetry the comment rule's and not the parser's.
- **`malformed-zero-cost`** — four stories at 35 against a baseline of 20 (a real 1.75x climb) plus one story logged at 0 because nobody recorded it. Without the positivity guard the recent mean falls to 28 and the file exits **0**, hiding the climb behind a missing measurement.
- **`limit-subunit-rounding`** — a **disclosed limit, not a closed hole**, and the only fixture here that no guard removal is needed to reach. Ten stories at 0.001 then five at 0.004: the run prints `baseline(10)=0.00  recent(5)=0.00  climb 4.00x > 1.50x` at exit **1**. The verdict is correct — this is not a false green — but the two printed means cannot reproduce the printed ratio, because they round to two decimals while the ratio widens its precision on demand. Nothing enforced bounds cost magnitude: `--unit` is a label the script's own help calls out as not validating anything, and the only bound is `0 < cost <= 1e9`. Kept as a captured run rather than scored.

The clean fixture is itself a *rising* trend (20 → 25) that the gate must still pass, which is what proves it discriminates rather than alarming at every repo that breathes. `dirty-rising-crlf` is `dirty-rising-cost` byte-for-byte with CRLF endings and returns the identical verdict; `malformed-non-utf8` is the same file with one raw `0xff` byte in the last id, so removing the byte returns it to exit 1 while corrupted it exits 2 — the decode error *preempts* an otherwise-alarming history instead of being read as one. Deleting any fixture, or any channel, returns the gate to `unverified`.

## Reading the verdict

1. **RISING with a confounder named** → the confounder is the finding; re-measure after it settles.
2. **RISING with no confounder** → the price of change is going up in this repo. Turn on the live watch — [`thrash-watch`](../thrash-watch/SKILL.md) — on the next story, and clean before you plan. The probe says the bill is growing; it never says which module is billing you.
3. **STEADY and cheap** → the $1 premise holds *here*, and [`story-cadence`](../story-cadence/SKILL.md)'s small batches are the rational move on measured ground rather than argued ground.
4. **STEADY and expensive** → change is dear at a stable price. That is data about the codebase; the reply is to find out why it is dear, not to write a longer plan.
5. **Re-probe after the repair.** A cost curve argued down instead of measured down stays `unverified`.

## Boundaries — who owns what

- **[`story-cadence`](../story-cadence/SKILL.md) owns the doctrine; this island owns its verification.** That island argued the $1 collapse and, until this one landed, said so in its own boundary line — "the collapse is an argument, not a measurement". That forward reference has been rewritten to point here as part of shipping this island, and its validator re-run. The doctrine still lives there; nothing about batch size is decided on this island.
- **[`margin-ledger`](../margin-ledger/SKILL.md) keeps a different ratio, and the two can disagree.** It divides an honest *human baseline* by the gated agent's wall clock, per story, and fires on a **floor breach** (below 1x, *"you've lost the game"*, C5). This island never looks at a human at all: it divides the agent lane by **its own past** and fires on a **trend**. So a stack whose cost per story doubles can still book 2x and pass that floor, because its numerator is an independent estimate rather than a measurement of the same lane — and a stack at a flat price fails that floor the moment the human baseline is re-estimated downward. Rising cost is this island. Losing to a human is that one. Neither number substitutes for the other.
- **[`thrash-watch`](../thrash-watch/SKILL.md) sees the struggle live; this island prices it afterward.** That island reads a *running* agent's behavior over turns — circling, break-one-fix-another, the give-up — and needs a supervisor watching. This island reads *finished* stories that all shipped, and needs only the ledger. It cannot see a live session, and it fires while work still succeeds. A RISING verdict is the reason to go turn that watch on.
- **[`tornado-detector`](../tornado-detector/SKILL.md) trends a different number.** Files touched per change measures how far one decision smears across the code; cost per story measures what a change costs to make. They move independently: a repo can hold its file count flat while retries, failed gates, and re-reads make every story dearer. This island never counts files or opines on architecture.
- **Ranking what to fix is [`arch-survey`](../../COMPANION.md#arch-survey)'s seat**, and a captured probe enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format as one rung — this island defines no second evidence format and no repair plan.

## Enforced vs advisory

- **`enforced`** (a mechanical check exists and was run above): the arithmetic and the verdict of `scripts/cost-trend.py` — window means, the climb ratio, exit 1 on breach only, and exit 2 fail-closed on every other path, including a comment rule and a `#`-id rule that are disjoint by shape in both directions — an annotation carrying a TAB is refused rather than counted as a story, and a `#`-digit row that lost its TAB to spaces is refused rather than skipped as an annotation, so neither can be silently read as the other — a leading BOM, a non-ASCII or duplicate id, a non-positive / non-finite / out-of-range cost, an undeclared order or unit, insufficient history, a non-finite threshold, a closed stdin, a closed or dead output channel, and any otherwise-unhandled exception. Watched failing across the blocks above **in this session**: six at exit 1, twenty-five at exit 2, three clean greens at exit 0. The printed ratio also widens its precision whenever two-decimal rounding would make an alarm read as `1.50x > 1.50x`, so the message cannot contradict the comparison the verdict used; the cost refusal prints the rejected value at full precision for the same reason — `1e9:g` rendered a refused 1000000001 as `got 1e+09`, naming the rejected value as the permitted limit. This island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- **`advisory`** (stated, judged, never auto-blocked): the row grain, how you capture minutes or tokens, whether all rows share a unit, every default threshold, the `--cheap` planning-depth label (accepted or refused, it never moves the STEADY/RISING verdict), the confounder list, the leading-indicator reading of C2, and the handoffs above. No hook runs this probe per merge yet, and nothing verifies that a row is one story. Two boundaries are disclosed rather than closed: the exit seal's non-int `SystemExit` branch maps to 1 (latent, unreachable from this file, seal prescribed verbatim), and the printed window means round to two decimals, so a ledger of sub-0.005 costs prints means that cannot reproduce the printed ratio. Nothing enforced prevents it: `--unit` is a label, not a bound, and cost is constrained only to `(0, 1e9]`. It is **implausible at the scale of a real minute or token capture, but not prevented by any check** — and rather than being asserted out of reach it ships as a captured run at exit 1, `limit-subunit-rounding`, where the verdict is right and only the printed means are unhelpful. Claiming any of these as enforced would launder judgment into evidence ([CONTEXT.md](../../CONTEXT.md)).

## Done means

- [ ] A cost ledger exists with one row per story at a stated grain and one stated unit, and `parsed N rows, skipped M comment lines, B blank` sums to the capture's line count **as an editor shows it** — `wc -l` counts terminators, so it undercounts by one on a file with no final newline and reports `0` for a CR-only classic-Mac capture; both were run, and in both the scanner reports 15 rows against `wc -l` of 14 and 0. A mismatch against `wc -l` alone is not yet a finding; a mismatch against the editor's own line count is
- [ ] `--order` declared, thresholds declared with their basis named — placeholder or calibrated, never an agent's vote (C18)
- [ ] `cost-trend.py` run and its full output plus exit code captured, not summarized
- [ ] Every RISING verdict either has a named confounder or is handed to the live watch with the next story
- [ ] The planning-depth call for the next batch cites the measured recent mean, not the parable

An open box means the verdict stays `unverified`: fix the capture, re-probe, re-check the boxes.

**The $1 house is a claim about your repo — measure the price of a change, or you are quoting an argument as if it were evidence.**
