---
name: measurement-humility
description: Standing review obligation for every enforced metric - each one must name the behaviour it might corrupt and carry a date on which its threshold is re-examined, so a coverage number with no named way to game it, and a threshold nobody has revisited in years, both surface as breaches instead of as a green build. Reach for it when adding or inheriting a metric gate, when auditing the gates a repo already runs, or when someone says "is this threshold still right", "what could this gate corrupt", "nobody has looked at that number in years", "metric review date", "our coverage gate is theatre". Differentiator - this island owns a metric's own review obligation and nothing else; the CRAP formula belongs to crap-gate, retuning a number by experiment to threshold-port, and catching gamed coverage to coverage-gaming-audit.
---

# Measurement Humility: the metric that reviews itself

Tom DeMarco opened *Controlling Software Projects* (1982) with the line that became a management proverb: **"You can't control what you can't measure."** He softened it publicly in 2009, decades after the industry had built its habits on it ([seventies-canon](../../research/seventies-canon.md)). That retraction is the artifact this island is made from. A doctrine updated itself when the evidence turned, and that is what a metric owner owes their own numbers.

This pack ships numbers. It ships a per-function CRAP ceiling (C6), a mutation gate (C7) the hardener runs *"absolutely merciless"* (C9), and the loop that makes them bite: *"you must change the code until this tool says that it's okay"* (C4), all quoted through the [ledger](../../docs/01-CONCEPT-LEDGER.md). A pack that hands out that much enforcement is exactly the pack that owes the guard. Bob supplies both halves of the reason. **Thresholds move**: *"there may be thresholds that we need to change"* (C17). A number is a working hypothesis, not a constant, and a hypothesis nobody revisits has quietly become a constant. **The number's defence is not evidence**: he polled agents on the CRAP threshold and then refused to bank the answer, because *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18).

The failure mode is documented, not a worry. Coverage measures execution, not assertion quality, so assertion-free tests game it and teams optimise the number without reducing risk ([crap-metric](../../research/crap-metric.md)). That is what an unguarded metric does. It does not stop working; it starts *paying* for the wrong behaviour, and the dashboard stays green the whole way.

## The two declarations

Every metric this repo enforces carries two sentences that are not about the metric's value:

1. **The corruption clause.** Name the behaviour a rational person would adopt to move this number without improving the thing the number stands for. Not "it might be gamed": the specific move. *Assertion-free tests drive `cov(m)` to 100 and collapse CRAP to plain cyclomatic complexity.* *Awkward mutants get excused into the ledger instead of killed.* Writing it down is most of the work. A metric whose owner cannot name its corruption has not been thought about; one whose corruption is named is one you can watch for.
2. **The review date.** The date the threshold is next re-examined against evidence. Not "periodically". A date, because a date can pass, and a thing that can pass can go red. When it arrives, the honest outcomes are: keep the number with fresh evidence, move it, or delete the gate. Re-stamping the date without one of those is the theatre this island exists to catch, and no tool can tell the difference (advisory, stated again below).

A metric with both is under review. A metric with neither is a habit wearing a gate's uniform.

## The register

One TSV, one row per enforced metric, four TAB-separated fields:

```
metric <TAB> threshold <TAB> corrupts <TAB> review
```

Only enforced metrics belong here. A rule that no tool measures is not a metric at all; that inventory, and the honest `advisory` label it deserves, is [`values-not-disciplines`](../values-not-disciplines/SKILL.md)'s. This register starts where that one ends. For every row it ruled `MEASURED`: what might that measurement corrupt, and when is it looked at again?

## Running it

```
python3 scripts/metric-register.py [--today YYYY-MM-DD] REGISTER.tsv
```

One verdict per row. `REVIEWED` is clean, and three verdicts are breaches:

- `UNGUARDED`: the row names no metric (empty, or a name that is only spacing and punctuation, which would otherwise fold to an empty join key and skip the duplicate check); or it names no enforced threshold (empty, punctuation, or an evasion like `TBD` or `tbd (see JIRA-12)`); or it names no corruptible behaviour (`none`, `- none -`, `none yet`, since an evasion trailed only by hedge words is still that evasion).
- `DUE`: the review date has arrived or passed.
- `DUPLICATE`: a second row under the same metric key. Case, Unicode form, spacing, dashes, connectors, math symbols and trailing sentence punctuation are all folded away before the join, so one twin gets updated and the other goes stale unseen.

Exit `0` clean, `1` breach, `2` for `--help`, usage, an unreadable or non-UTF-8 file, a row without exactly four fields, an unparseable date, an empty register, an internal failure of any kind, or a stream that could not be flushed. Every error path reachable in this script exits `2`, never `1`, probed across fifteen malformed invocations. No line carrying TABs is ever skipped as blank or as a comment.

**Red/green proof.** All six fixtures ship beside the script. Recompute from this island's directory rather than trusting these lines:

```bash
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/theatre.tsv       # exit 1
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/punctuation-evasion.tsv  # exit 1
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/pack-metrics.tsv  # exit 0
```

Red, full stdout, nothing elided:

```
REVIEWED   per-function CRAP ceiling (naïve pass)  [corrupts: assertion-free tests inflating the coverage term | review 2026-11-20, 91 days out]
UNGUARDED  branch coverage floor  [names no behaviour it might corrupt: 'none' is an evasion, not a behaviour]
UNGUARDED  lines of code per file  [names no behaviour it might corrupt: 'tbd' is an evasion, not a behaviour]
UNGUARDED  cyclomatic complexity cap  [names no behaviour it might corrupt: the field is empty]
UNGUARDED  test count per story  [names no behaviour it might corrupt: it restates the metric]
UNGUARDED  doc coverage  [names no behaviour it might corrupt: 'x' carries fewer than 3 letters]
DUE        build time budget  [review 2019-04-01 came due 2699 days ago]
DUE        bundle size ceiling  [review 2026-08-21 came due today]
UNGUARDED  #-of-functions-over-30  [names no behaviour it might corrupt: 'none' is an evasion, not a behaviour]
UNGUARDED  stale threshold gate  [names no enforced threshold - 'tbd' is an evasion, not a threshold]
UNGUARDED  mutation score floor  [names no behaviour it might corrupt: 'none' is an evasion, not a behaviour]
DUPLICATE  Per-Function CRAP Ceiling (Naïve Pass)  [same metric key as line 4; one twin goes stale unnoticed]
12 enforced metrics, 1 reviewed, 8 unguarded, 2 due, 1 duplicate
```

Eleven intended failures, covering every verdict class the gate rules on. Two evasion phrases. An evasion in the `threshold` field (`TBD`), because a metric whose enforced number is still provisional is the definitive un-thought-about one, and it is refused on the same list that guards `corrupts`. A bracket-wrapped evasion (`(none)`), because punctuation and symbol marks are peeled until the string stops shrinking, so `"none"`, `(none)`, `[none]` and `(NONE).` are one evasion rather than four ways past one. A field holding only zero-width spaces. A corruption clause that restates its own metric. A one-letter placeholder. A date long past, and a date landing *exactly* on `--today`, the boundary, where due is due. A duplicate spelled with different letter case, doubled spacing, and NFD combining marks. And the `#-of-functions-over-30` row, which is the comment-rule probe: a `#` line carrying TABs is data and is ruled on, so a legitimate metric name cannot be silently dropped. One row still reads `REVIEWED`, so the red is discrimination and not a parse error.

**The peel is a category test, not a hand-written list.** `punctuation-evasion.tsv` is the second red fixture above, and it is where that claim is run rather than asserted. Five rows, every one `UNGUARDED`, exit 1: corruption clauses of `none?`, `-none-` and `none-`, and thresholds of `tbd?` and `###`. A trailing `?` peels exactly as a trailing `.` does, and a dash glued to a word peels exactly as a spaced one does, because `peelable()` asks Unicode for each character's category rather than consulting a list someone typed. Widen the input by one unlisted mark and a typed list is past; a category test is not.

**The join key's blind spot, captured.** The duplicate key folds case, Unicode form, spacing, every separator in the dash family (hyphen, en dash, non-breaking hyphen, soft hyphen, the `_` connector, the U+2212 minus sign) and a trailing footnote asterisk. So `crap-ceiling`, `crap_ceiling`, `crap ceiling` and `crap ceiling.` are one metric and cannot drift apart unseen. What the key does not fold is *meaning*, and that hole is a run rather than a sentence:

```bash
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/duplicate-blind-spot.tsv  # exit 0
```

Six well-formed rows, `6 enforced metrics, 6 reviewed`, exit 0. They are three metrics each named twice: `LOC per file` / `lines of code per file`, `CRAP ceiling (v2)` / `CRAP ceiling v2`, `branch coverage floor` / `branch coverage floors`. Read that green as "no duplicate *spelling* found", never as "each metric appears once".

**The evasion filter's residue, captured.** The filter refuses the exact-phrase list after folding away case and Unicode form and peeling every punctuation and symbol mark. It also refuses an evasion wearing a bracketed aside (`tbd (see JIRA-12)`), dash decoration whether spaced or glued (`– none –`, `-none-`), or a one-word hedge tail (`none yet`, `n/a for now`, `none that I can think of`), because otherwise one token past the list buys a green. What it cannot refuse is a sentence that is merely *empty of content*, and that hole is a run rather than a sentence:

```bash
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/evasion-residue.tsv  # exit 0
```

Six well-formed rows, `6 enforced metrics, 6 reviewed`, exit 0. Not one of them names a behaviour anyone could watch for: `probably nothing much`, `nothing I would bet on`, `hard to say honestly`, `see JIRA-4471`, `whatever the last audit said`, `it depends on the team`, plus a *threshold* of `see the platform wiki`. Each dodges the list by a single non-hedge word. Read that green as "this field is not on the evasion list", never as "the corruption clause is real".

**The register holds the pack to its own law.** `pack-metrics.tsv` is not a toy. It is this pack's own enforced metrics: the CRAP ceiling, zero mutants on the diff, the dependency direction, and the validator's F10 and F6 limits, each with its corruption clause and a real date. Two more captured runs, same script, exit codes recomputed the same way:

```bash
python3 scripts/metric-register.py --today 2026-08-21 scripts/fixtures/pack-metrics-bom-crlf-nfd.tsv  # exit 0
python3 scripts/metric-register.py --today 2027-06-01 scripts/fixtures/pack-metrics.tsv               # exit 1
```

The first is `pack-metrics.tsv` re-encoded with a UTF-8 BOM, CRLF endings, and NFD normalization, which is what an editor, a Windows checkout, or macOS hands you unasked. Its stdout is byte-identical to the clean run. The second is the clean register read on a later day: all five rows go `DUE`, exit 1. **The pack's own thresholds are on a clock, and the clock is proven to bite.**

## Boundaries

- **The CRAP formula, its thresholds, and the input contract are [`crap-gate`](../crap-gate/SKILL.md)'s.** That island decides what `6` means and how the score is computed. This island never reads a score. It asks whether whoever set that `6` wrote down what chasing it would corrupt, and when they will look at it again.
- **Retuning a threshold empirically is [`threshold-port`](../threshold-port/SKILL.md)'s.** When a review date arrives, the controlled experiment that moves 6 to 8, or refuses to, happens there (C17). This island only guarantees the date arrives and cannot be ignored quietly; it has no opinion on the new number.
- **Detecting gamed coverage is [`coverage-gaming-audit`](../coverage-gaming-audit/SKILL.md)'s.** That island finds the assertion-free tests actually sitting in a suite and routes them to [`mutant-hunt`](../mutant-hunt/SKILL.md). This island only requires that the corruption be *declared in advance*, before anyone has an interest in denying it. Declaration is cheap and prospective; detection is expensive and retrospective. Do both.
- **Requiring each rule to name a measuring tool is [`values-not-disciplines`](../values-not-disciplines/SKILL.md)'s.** It rules `MEASURED` / `ADVISORY` / `PROSE-ONLY` on the naming. Its `MEASURED` rows are this register's input; a rule it ruled `ADVISORY` has no threshold and does not belong here.
- Whether this gate can itself go red is [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s ritual, obeyed above, in both directions, with the fixtures kept in the repo.
- Two Forge concerns stay off the island. Where the check executes (pre-commit, PostToolUse, CI) is [`agent-guardrails`](../../COMPANION.md#agent-guardrails)'s. The format the captured report travels in is [`evidence-packet`](../../COMPANION.md#evidence-packet)'s: this stdout plus its exit code become one rung of that ladder, never a second evidence format.

## Enforced vs advisory

- `enforced` — **declaration completeness and review currency of the rows you supply.** [`scripts/metric-register.py`](scripts/metric-register.py) rules every row, exits 1 on any `UNGUARDED` / `DUE` / `DUPLICATE`, and exits 2, never 1, on usage, IO, decode, malformed, empty, internal-exception, or unflushable-stream conditions. Proven in both directions above, and fifteen malformed invocations were probed with every one exiting 2. One branch of the pack's shared exit seal is unreachable from here rather than removed: a `SystemExit` carrying a non-integer payload would map to 1, but `argparse` runs with `add_help=False` and raises only `SystemExit(2)`, and `main` never calls `sys.exit`, so nothing in this script raises one. That mapping line is byte-identical in thirteen of this pack's thirty-one island scripts, so it is kept here rather than forked. The count drifts as scripts are added; recompute it with `grep -rlF '_code = _exc.code if isinstance' skills/*/scripts/*.py | wc -l` from the pack root. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — **completeness of the register.** The gate rules on rows it is given. A metric enforced somewhere in CI but never written down here is invisible to it, and sweeping every enforced number into the register is judgment work. `pack-metrics.tsv` covers five of this pack's enforced metrics and does not claim to be exhaustive.
- `advisory` — **truth of the corruption clause.** The gate checks that a behaviour is *named*, not that it is the right one, or the worst one, or that anyone watches for it. A plausible-sounding sentence passes. Naming the wrong corruption is a failure this island cannot see.
- `advisory` — **the evasion filter is a filter, not a proof of substance.** It refuses empty, punctuation-only and zero-width-only fields; an exact-phrase evasion list (`none`, `nil`, `null`, `no`, `nope`, `n/a`, `tbd`, `unknown`, …) tested whole-token once wrappers, bracketed asides and dash decoration are peeled; that same list trailed only by hedge words (`none yet`, `n/a for now`); a clause that restates its own metric; and anything under three letters. Everything else passes on shape. The residue is captured as a run in `evasion-residue.tsv` above rather than only stated: `probably nothing much` reads `REVIEWED`, because the gate asks "is a behaviour written here", never "is this English, and is it true".
- `advisory` — **duplicate detection is spelling, not meaning.** Interior punctuation, abbreviations, plurals and synonyms do not join, so one metric entered under two names sits in the register twice and both rows exit 0, captured above as `duplicate-blind-spot.tsv`. Semantic dedup is judgment work.
- `advisory` — **that the review actually happened.** A `REVIEWED` row means the date has not arrived. Re-stamping a date forward without evidence, the exact theatre named at the top, passes this gate and fails the pack's first law. No mechanical check can separate a real review from a bumped date. The ledger of *what* the review concluded belongs in [`evidence-packet`](../../COMPANION.md#evidence-packet) format alongside the run.
- `advisory` — **choosing the review interval.** Quarterly is the convention this island's research seed suggested ([seventies-canon](../../research/seventies-canon.md)); nothing enforces a maximum gap, so a date five years out passes.

## Done means

- [ ] Every enforced metric in the repo is a row in the register (advisory, completeness is judgment)
- [ ] `metric-register.py` exits 0 over it, on today's real date, with no `--today` pin (enforced)
- [ ] Each corruption clause names a concrete move, not the word "gaming" (advisory)
- [ ] When a date arrives, the review ends in keep-with-evidence, move, or delete, and the conclusion is captured, not just the new date (advisory)

An open box keeps the verdict `unverified`. The loop: register every enforced number → run the gate → repair each breach by naming the real corruption or booking the real review → re-run until exit 0.

**A number with no named corruption and no date on the calendar is not a standard — it is a habit that learned to exit zero.**
