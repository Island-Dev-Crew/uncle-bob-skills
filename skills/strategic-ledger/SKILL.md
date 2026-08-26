---
name: strategic-ledger
description: A tactical/strategic effort ledger for a repo worked by agents. Every unit of work is tagged as shipping behaviour or improving shape, the evidenced strategic share is held inside a target band, and each strategic claim is backed by a captured before/after structural metric. Reach for it when a repo gets harder to work in cycle after cycle, when deciding how much of the next cycle to book against design, or on "strategic ledger", "tactical debt", "how much refactoring should we book", "the 10-20% investment". Differentiator - it accounts for the SPLIT of effort between behaviour and shape, where margin-ledger accounts for agent-versus-human productivity on a story and job-to-be-done decides whether a thing is worth building at all.
---

# Strategic Ledger: the shape is what the next agent reads

The conversation names the division of labour bluntly: *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* (C25). Tactical capacity is now effectively unbounded and nearly free. The strategic seat is the one the human still holds. That asymmetry is the whole reason this ledger exists: when shipping behaviour costs almost nothing, nothing *automatically* gets spent on shape, and a cycle can look productive while the repo gets worse underneath it.

Ousterhout's answer to that failure mode is a budget. Strategic programming treats design as the primary goal and books roughly **10–20% of development time** as investment that repays within months ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). This island turns that mindset into accounting. Tag each unit, hold the share, and make every strategic claim carry captured structural evidence. Quotes come only through the [concept ledger](../../docs/01-CONCEPT-LEDGER.md).

## Where this island sits

State these boundaries before opening a ledger; each names the neighbour that owns the adjacent concern.

- **[`margin-ledger`](../margin-ledger/SKILL.md) is a different ledger. Read the unit to tell them apart.** Its unit is *honest human baseline ÷ agent-with-gates wall clock, per story*: it prices what the gate stack costs in productivity, and asks whether agents plus gates are still faster than a human (C5). This island's unit is *evidenced strategic minutes ÷ total minutes, per cycle*: it prices what the effort bought, behaviour or shape, and asks whether any of the cycle went into shape at all. Reach for margin-ledger when the pipeline feels slow. Reach for this one when the repo feels worse. The two can disagree in a way that matters: a stack humming at 4x margin can book 0% strategic, productivity healthy and shape rotting, and no single number would show it.
- **Pre-build triage is [`job-to-be-done`](../../COMPANION.md#job-to-be-done)'s seat.** Whether the thing should be built or automated at all is settled there. This ledger opens after that verdict and only tags work already sanctioned; it never argues a story out of existence.
- **Finding and ranking *which* structural problem to attack is [`arch-survey`](../../COMPANION.md#arch-survey)'s.** This island books and prices the investment; it never picks the target or builds a refactor backlog.
- **The before/after numbers come from the metric islands, not from here.** A CRAP ceiling comes from [`crap-gate`](../crap-gate/SKILL.md), a layering violation count from [`dependency-fence`](../dependency-fence/SKILL.md). This ledger records the pair and checks it moved; it defines no metric of its own.

## The two tags

One row per unit of work, tagged by what the unit exists to do:

| Tag | The unit exists to | Reversion test |
|---|---|---|
| `tactical` | make the behaviour work: a feature, a fix, a migration | reverting it changes what the system does |
| `strategic` | make the shape better: a split, an extracted port, an inverted dependency | reverting it leaves observable behaviour identical |

The reversion test is the tie-breaker: **strategic work is work you could undo without a user noticing.** A unit that does both gets split into two rows with the minutes divided, never one row tagged half-and-half. A fractional tag is unfalsifiable, and the ledger's whole value is that each row can be argued with. Tagging is `advisory`: no tool reads intent, so the tag is a call made at merge and open to challenge in review.

## The band, and why you must re-derive it

The default floor 10% / ceiling 20% is Ousterhout's human-era number ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). It enters this pack as a **threshold, not a law** — *"It is not a mistake to impose human values on the agent, but there may be thresholds that we need to change"* (C17). Two forces push the number in opposite directions, and this island refuses to pretend it knows the net:

- **What pushes it down.** The cost of change has collapsed: the $1 house (C21). When *"the cost of change has plummeted to as close to zero as I think we're ever going to get it"*, some shape you would once have bought upfront is now cheaper to fix later, on demand.
- **What pushes it up.** Mess compounds against agents exactly as it does against humans: *"The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). Repo shape is read by every future agent session, so the investment pays into every later task rather than only the next human maintainer ([`ousterhout-debate.md`](../../research/ousterhout-debate.md), assessment section).

Which force wins is **`unverified` in this pack: no captured run here sets the agent-era number.** Move it the way any threshold moves, empirically. Run a cycle at a candidate band, capture the outcome, let the evidence pick; that is the discipline on [`threshold-port`](../threshold-port/SKILL.md). An agent's opinion on the right percentage is a hypothesis, never authority (C18).

## The evidence rule

A tag alone is a claim. **A strategic row counts only when it carries a captured before/after structural metric** in the form `metric=before->after`, from a run that could have come out otherwise. The script checks the *form* and the *delta*; that the run happened at all is `advisory` and rides the pairing remedy below. Rows that fail that test are discounted as `UNEVIDENCED`: their minutes stay in the denominator and leave the numerator, so an unbacked strategic claim *lowers* the share instead of flattering it. That is the pack's first law applied to the ledger's own grain — [no authority without evidence](../../CONTEXT.md).

Three things fail the check, all mechanically: no evidence field, evidence not in `metric=before->after` form, and a no-delta pair like `crap_max=6->6`. A metric that did not move is not evidence that the shape changed.

## Keeping the ledger

1. **Tag at merge** (advisory). One TSV row per unit as it lands: `item <TAB> tag <TAB> minutes [<TAB> evidence]`. Tagging in flight beats reconstructing intent a month later. Only blank lines and narrow comments are skipped, where a comment is a raw `#` in column 1 with *no tab* on the line. So an issue-numbered item (`#482-checkout-flow <TAB> tactical <TAB> 540`) stays a data row rather than quietly leaving both sides of the fraction, an indented `# note` is malformed (exit 2), and the report prints the count of lines skipped.
2. **Attach the pair** (advisory input, enforced form). For each strategic row, capture the metric before the work and after it, from the metric's own gate, and record `metric=before->after`.
3. **Score the cycle** (enforced). [`scripts/strategic-share.py`](scripts/strategic-share.py) prints per-row status and the evidenced share against the band, exits 1 on a floor breach or any unevidenced strategic row, exits 2 fail-closed on an empty or malformed ledger and on unwritable output, exits 3 on an unreadable input path or bad invocation (captured run):

```bash
$ printf 'checkout-flow\ttactical\t300\nsplit-billing\tstrategic\t60\tcrap_max=14->5\n' | python3 scripts/strategic-share.py
tactical       300m                                      checkout-flow
STRATEGIC       60m  crap_max 14 -> 5                    split-billing
strategic share 16.67% IN-BAND (band 10-20%); 60m evidenced of 360m
$ echo $?   # → 0
```

4. **Repair on a breach** (advisory). `UNDER` has exactly two honest repairs: book strategic work into the next cycle, or attach the missing evidence to work already done. Then re-run. Faking the share by re-tagging tactical rows is the failure this gate exists to catch, and the evidence rule is what makes it expensive.

`OVER` the ceiling prints and exits 0. Over-investment is a judgment call, and a deliberate paydown cycle after a structural collapse is correct rather than a defect. So the ceiling is a reading and the floor is the gate.

## Enforced vs advisory (v0, stated honestly)

- **Enforced today.** The arithmetic and the verdict. [`scripts/strategic-share.py`](scripts/strategic-share.py) computes the evidenced share by cross-multiplication (no division, so the floor is exact at the boundary). It rejects any tag outside `tactical|strategic` on a fully anchored match, enforces the `metric=before->after` form and the no-delta discount, and keeps `#`-leading work items in the accounting while counting every line it skips. File and stdin input both decode as strict UTF-8. Every per-row minute, aggregate sum, and scaled percentage product must remain finite; two `1e308` rows and one `1e308` row both refuse at exit 2 instead of producing `nan% IN-BAND`. It exits 1 on a breach, 2 fail-closed on ledger content, invalid aggregate arithmetic or an unwritable report, and 3 on input-path IO, decode failure or usage. Input-path/usage 3 stays distinct from malformed-content 2: a mistyped path exiting 2 would read exactly like malformed ledger content, while dead output always uses the pack-wide exit-2 IO seal. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- **Advisory at v0.** Every judgment feeding the script: which tag a unit gets, the minutes booked to it, the 10–20% band, the choice of structural metric, **the provenance of the numbers inside it**, and the cadence you score on. Provenance is the one that reads mechanical and is not. The script checks that a pair is well-formed and moved, never that it came from a run that could have come out otherwise, so an invented `vibes=1->2` passes the form check. It rides the same pairing remedy as direction below: a metric name with no gate behind it has nothing to sit beside. Each is stated so a later wave can mechanize it; claiming more would launder advisory into enforced.
- **The known hole: name it, pair it.** The script checks that a metric moved, never that it moved the *right way*, so `crap_max=5->14` is a real delta and counts. Direction is metric-specific (complexity down, coverage up), so the reviewer owns it. The cheap pairing is to run the metric's own gate in the same cycle, where [`crap-gate`](../crap-gate/SKILL.md) exits non-zero on a ceiling breach and a regressed row cannot sit green beside it. A ledger scored without its metric gate must say so in its evidence.

**Red/green proof (run, not asserted).** The gate ships the fixture pair that proves it can fail. [`scripts/fixtures/dirty-tactical-drift.tsv`](scripts/fixtures/dirty-tactical-drift.tsv) books 120m of 840m as *claimed* strategic, a plausible-looking 14.3%, but one claim carries `crap_max=6->6`, so the evidenced share falls to 7.14%. [`scripts/fixtures/clean-at-floor.tsv`](scripts/fixtures/clean-at-floor.tsv) books 100m of 1000m, all of it evidenced. Run both from this island's directory:

```bash
python3 scripts/strategic-share.py scripts/fixtures/dirty-tactical-drift.tsv   # → exit 1 (RED, UNEVIDENCED tidy-naming-pass + 7.14% UNDER)
python3 scripts/strategic-share.py scripts/fixtures/clean-at-floor.tsv         # → exit 0 (GREEN, 10.00% IN-BAND)
python3 scripts/strategic-share.py scripts/fixtures/dirty-aggregate-overflow.tsv # → exit 2 (aggregate arithmetic is not a verdict)
python3 scripts/strategic-share.py scripts/fixtures/dirty-comparison-overflow.tsv # → exit 2 (percentage arithmetic is not a verdict)
printf 'bad\377name\tstrategic\t100\tcrap_max=14->5\n' | python3 scripts/strategic-share.py # → exit 3 (stdin is not UTF-8)
```

The verdict pair's exit codes were observed on the shipped fixtures. The dirty fixture parses cleanly and fails on the *claim*, not on syntax. The clean fixture lands exactly on the 10% floor, so the pair proves discrimination at the boundary. The two overflow fixtures and invalid-stdin proof are refusal controls: aggregate-sum overflow, cross-product overflow, and non-UTF-8 stdin must never wear a green verdict. The pack ritual ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)) agrees on the verdict pair, from the pack root: `skills/known-dirty-fixture/scripts/prove-gate.sh skills/strategic-ledger/scripts/fixtures/dirty-tactical-drift.tsv skills/strategic-ledger/scripts/fixtures/clean-at-floor.tsv -- python3 skills/strategic-ledger/scripts/strategic-share.py` → `ACCEPTED`, exit 0. Deleting the pair returns this gate to `unverified`.

## Done means

- [ ] Every unit shipped this cycle appears exactly once, tagged `tactical` or `strategic`, minutes booked
- [ ] Every strategic row carries `metric=before->after` from a captured run of that metric's own gate
- [ ] `strategic-share.py` exits 0 over the cycle's ledger at the declared floor
- [ ] The declared band is either the 10–20% default with its human-era provenance named, or a moved number backed by captured cycles (C18)
- [ ] The script's output is captured as evidence, with the status of the paired metric gate stated

An open box means the cycle's strategic claim stays `unverified`: book the work or attach the evidence, re-run the script, re-check the boxes.

**Tactical work ships the behaviour. Strategic work ships the shape every later session reads. Book both, and let only the evidenced half count (C25).**
