---
name: plan-decay-detector
description: Mid-execution divergence check for an agent fleet - the plan writes its assumptions down in checkable form, and a gate compares them against the repo as it actually is, halting for a re-plan the moment one has stopped being true instead of letting agents keep running off a plan that is no longer accurate. Reach for it before a batch resumes work from a plan written earlier, after a parallel agent or a human has touched the tree, or when someone says "is this plan still valid", "the plan says X but the repo has Y", "re-check the plan before we continue", or "did the plan drift". Differentiator - this island detects decay and halts on it; how big a batch should be is story-cadence's doctrine, and ticket machinery is a Forge concern.
---

# Plan Decay Detector: halt when the plan stops describing the repo

Bob's failure mode, from inside it the week of the conversation: *"you make all these plans and then as the agents are running, you realize that they can't follow that plan because you didn't think of everything… they're running half-cocked off on some nonsense that you have to stop, back up, rewrite the plan"* (C19). And the seduction that keeps producing them: *"The agents love to write plans… the plans will be gorgeous and beautiful… And then they fall apart at the end"* (C19). Every quote here comes through [the ledger](../../01-CONCEPT-LEDGER.md), never from memory.

The word that matters is *end*. The plan does not announce its own death. It is discovered dead, at the end, after a batch of agents has already spent itself against it. This island moves that discovery to the front of the batch and makes it mechanical. A prose instruction to "check the plan is still valid" decays in the middle of a context exactly like every other prose rule ([`CONTEXT.md`](../../CONTEXT.md), law 2); a tool in a fix-until-green loop does not (C4).

## What actually decays

The plan is not wrong when it is written. The tree moves under it, from three directions:

1. **Execution reveals what planning could not.** The planner did not think of everything (C19): the interface is shaped differently than assumed, the module is already gone.
2. **A parallel agent lands first.** Three coders can run at once (C10); the file your plan was going to create already exists, written by a sibling.
3. **A human reorganised.** The cadence's manual sort-out step (C20) rewrites structure between batches, and every queued plan aged the moment it ran.

This is a tooling gap, not just a discipline gap. The spec-driven tooling that exists has the same hole: AWS Kiro does not auto-detect implementation/spec divergence, so its specs silently drift from the code ([atdd-gherkin-agile](../../research/atdd-gherkin-agile.md), citing a doit.com review of Kiro). The brief names Spec Kit and OpenSpec only for the separate "reinvented waterfall" critique, so this is one reviewer's report about one tool, not a measurement and not a survey of the category. Silent drift is the whole disease. A plan that cannot be checked cannot go stale *loudly*.

## The move: make the plan state its beliefs in checkable form

A plan is admitted to this gate only if it writes down what it believes about the tree. Five kinds, one per line, TAB-separated, in a file that travels with the plan:

| Kind | Fields | The belief it records |
|---|---|---|
| `exists` | PATH | "this is here, and my batch reads or edits it" |
| `absent` | PATH | "nothing is here yet, and my batch creates it" |
| `contains` | PATH, LITERAL | "this file still holds the symbol/marker I am extending" |
| `lacks` | PATH, LITERAL | "this file still does not hold the thing I am about to add" |
| `unchanged` | PATH, SHA256 | "this file is exactly the text I read when I planned" |

`unchanged` is the strong form and the one that catches a sibling agent's edit; `contains`/`lacks` are the cheap forms for a plan that only cares about one seam. Writing them is the work this island asks of the planner, and it is the reason the plan becomes falsifiable instead of gorgeous.

## The check

```bash
python3 scripts/plan-decay.py --root . docs/plan/batch-07.assumptions.tsv
python3 scripts/plan-decay.py --root . --digest src/payments.py    # to author an `unchanged` row
```

`--root` is **required and has no default**. It used to default to `.`, which aimed the whole plan at whatever directory the process happened to sit in, without saying so. A create-only plan, every row `absent`, then held vacuously against an unrelated tree and exited **0**. A CI step with the wrong working directory, or an agent shelling out from a subdirectory, is an ordinary condition rather than an attack. And an exit-code-consuming caller cannot see `against .` in the report. Omitting it is now argparse's usage error, exit 2.

| Exit | Meaning |
|---|---|
| 0 | every stated assumption still holds — and `--help`, which prints usage and computes no verdict, so a 0 is a verdict only when the report says `CHECKED n assumption(s)` |
| 1 | at least one assumption diverged — **HALT and re-plan** |
| 2 | usage, IO, or malformed input — never a verdict, always fail-closed |
| 3 | informational: `--digest` printed a digest and checked no plan |

**0, 1, 2 and 3 are the only codes this script produces, and every fault leaves through 2.** The faults: an unreadable directory; a target file that is not UTF-8 text; an assumptions file that is a directory or not UTF-8; a malformed row; a missing `--root`; argparse's usage exit; a `SystemExit` carrying a non-integer payload; a stdout closed before the run or broken during it, including the flush CPython performs at *shutdown*, where the status would otherwise become **120**; and any unexpected exception. On that non-integer payload the pack's stock tail returns **1**. This script raises no `SystemExit` of its own, so one arriving at the seal is a fault rather than a divergence, and it leaves through 2. The coercion covers 3 as well as 0 and 1: a `--digest` run whose flush fails printed no digest, so it must not leave claiming it did. None of them may borrow a verdict's code. A caller that reads 1 records a divergence this run never computed; a caller that reads 0 records a plan this run never checked.

## What the gate refuses to guess

- **One key function for every path.** Components are matched against real directory entries after NFC folding, the one fold that is genuinely the same file and routine on macOS. A name that matches only *case-folded* is reported as a **variant** and never treated as a match, in either direction: `absent src/refunds.py` diverges when the tree holds `src/Refunds.py`, and so does `lacks`. There is no lenient branch for a **case** respelling. Three further respelling classes never reach a branch at all, because they are refused when the row is read (exit 2). *Invisible* characters: U+FEFF, U+200B and the rest of Unicode Cf/Cs/Co. *Compatibility* forms: `ｒ` U+FF52 FULLWIDTH LATIN SMALL LETTER R, caught by `NFKC(s) != NFC(s)`, where NFKC is a refusal test and never the matching fold, because it is lossy for filenames. And a word that *mixes scripts*: `rеfunds` with U+0435 CYRILLIC SMALL LETTER IE. None of the three can ever equal the entry it imitates, so `locate` would report `missing` and every negative kind would hold vacuously. The mixture test runs per *word*, not per line, so a multilingual repo still checks normally: `Описание.md`, `コーヒー.py` and `src/test_日本語_helper.py` all pass, since a real line mixes scripts *between* words while a respelling mixes them *inside* one. Both fields are covered, because a confusable in a `lacks` **literal** is the same false green and is refused too. **What is not closed:** a *whole-word* confusable. Every letter of one word respelled into one other script, `асе` all-Cyrillic for `ace`, mixes nothing, keys as `missing`, and still holds for a negative kind; [`scripts/fixtures/blind-spot-confusable/`](scripts/fixtures/blind-spot-confusable/) ships that as a captured exit-0 run rather than a sentence. Absolute paths, drive letters, `..`, backslashes, control characters and whitespace-padded components are refused outright rather than rerouted. Two entries that normalise to one name is an ambiguity the gate refuses to resolve (exit 2).
- **A missing file never satisfies a negative.** `lacks` and `contains` both diverge when the named file is not present under that spelling, so deleting a file can never quietly make a `lacks` row pass.
- **No line with content is dropped in silence.** A blank line is skipped, including one holding only spaces or TABs, which carries no assumption. Every line that holds content is either a comment or a checked row, never a silent skip. A comment is a line whose first non-blank character is `#` *and that holds no TAB*; a `#` line that does hold a TAB is ambiguous and is refused out loud. A BOM is stripped (`utf-8-sig`) and CRLF is handled, because that is what an editor hands you. An unknown kind, a wrong field count, a non-hex digest, a blank literal, or a literal *padded* with whitespace is a refusal, not a skip. A single trailing space is the most ordinary editor artefact there is, CRLF stripping does not remove it, and it would silently turn a `lacks` row into one that can never be found and therefore holds forever.
- **An empty plan is not a passing plan.** An assumptions file with zero rows exits 2. "No assumptions, therefore no decay" is the laundering this gate exists to refuse.
- **Digests are over normalised text.** UTF-8 decoded (BOM stripped), line endings folded to `\n`, NFC applied, then SHA-256. A checkout's line-ending policy therefore cannot fake a divergence. `--digest` prints exactly what an `unchanged` row needs.

## What a halt means

Exit 1 is not a warning to note and continue. It is *"stop, back up, rewrite the plan"* (C19), and the re-plan is budgeted as the normal cost of a cycle, not logged as failure. That budgeting is [`story-cadence`](../story-cadence/SKILL.md)'s doctrine. Two things follow immediately:

- **Re-plan from the repo as it now is**, not by patching the old plan. The old plan's remaining assumptions were written against a tree that no longer exists.
- **The context that was already steered by the stale plan is contaminated.** A window has momentum: *"the only way to clear the trajectory is to clear the context window"* (C11). An agent that has been working from the dead plan therefore does not get corrected, it gets replaced. Deciding that is [`trajectory-hygiene`](../trajectory-hygiene/SKILL.md)'s seat, not this island's; this island only rings the bell.

And when the halt is contested, an agent's argument that the divergence is harmless is a hypothesis: *"you can't trust any debate you have with an agent"* (C18). The digest is the evidence; the opinion is not.

## Enforced vs advisory

- `enforced` — the divergence verdict. [`scripts/plan-decay.py`](scripts/plan-decay.py) computes every stated assumption against the tree under `--root`. It exits 1 if any diverged, 0 only if all held, and 2 fail-closed on every non-verdict outcome except argparse's `--help`, which exits 0 and prints no `CHECKED` line (see the exit table); a `--digest` that printed leaves through 3. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — **whether the assumptions are the ones the plan actually rests on.** The gate checks the beliefs that were written down; it cannot check the beliefs that were not. A plan can pass with vacuous rows, and `scripts/fixtures/blind-spot-vacuous/` ships that as a captured exit-0 run rather than a sentence. Also advisory: a **whole-word confusable** path, one word respelled entirely into a single other script, is not refused and keys as missing, so it holds vacuously for `absent`/`lacks` (`scripts/fixtures/blind-spot-confusable/`, the second captured exit 0). Mixed-script and compatibility respellings inside a word *are* refused, and a whole-word one is reachable only by an author deliberately writing one. Also advisory: `contains`/`lacks` are literal substring tests over the whole file, so a match inside a comment or a string literal counts; reach for `unchanged` when that matters. `exists` asks whether a directory *entry* of that name is there, so a broken symlink holds. A symlinked component leads where it links, so an assumption can reach outside `--root` through a link in the tree. And *when* to run the check (every batch boundary, every resume, after every merge) is discipline: no hook wires it into a fleet today.

### Red/green proof

The gate earns its `enforced` line by having been watched failing: the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. That island's "the pair is necessary, not sufficient" clause is why the fault block below is longer than the pair. **One assumptions file, two trees**: the same input goes green on the tree the plan was written against and red on the tree that moved. Recompute from this island's directory:

```bash
python3 scripts/plan-decay.py --root scripts/fixtures/plan-decayed scripts/fixtures/batch-plan.assumptions.tsv     # exit 1
# HALT: refunds.py already created by someone else; `def charge(` renamed away; `def refund(` appeared; digest moved
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/batch-plan.assumptions.tsv       # exit 0
# PLAN HOLDS: 6 held, 0 diverged

python3 scripts/plan-decay.py --root scripts/fixtures/variant-spelling scripts/fixtures/batch-plan.assumptions.tsv # exit 1
# the tree respelled two paths: `absent src/refunds.py` must NOT pass because the tree holds src/Refunds.py
python3 scripts/plan-decay.py --root scripts/fixtures/unicode-nfd scripts/fixtures/unicode-nfd/assumptions.tsv     # exit 0
# the NFD name on disk and the NFC path in the plan are one file, not a divergence
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/bom-crlf.assumptions.tsv         # exit 0
# a BOM'd, CRLF assumptions file still parses; unstripped, the BOM makes row 1 an unknown kind

python3 scripts/plan-decay.py scripts/fixtures/create-only.assumptions.tsv                                     # exit 2
# --root omitted. Every row is `absent` - the create-only shape - so with the old
# default of '.' this printed `against . - 3 held` and exited 0 from any unrelated
# cwd, a false green on the island's own verdict. It is now argparse's usage exit.
python3 scripts/plan-decay.py --root scripts/fixtures/plan-decayed scripts/fixtures/create-only.assumptions.tsv # exit 1
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds   scripts/fixtures/create-only.assumptions.tsv # exit 0
# the same create-only plan, aimed: red on the tree that already holds src/refunds.py,
# green on the one that does not. The root is now the thing the caller must state.

python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/empty.tsv          # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/hash-tab.tsv       # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/empty-literal.tsv  # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/unknown-kind.tsv   # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/field-count.tsv    # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/bad-digest.tsv     # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/absolute-path.tsv  # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/dotdot.tsv         # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/backslash.tsv      # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/padded-path.tsv    # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/non-utf8.tsv       # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/padded-literal.tsv # exit 2
# `lacks src/payments.py 'def refund( '` - one trailing space. Before the fix this exited 0
# on the plan-decayed tree with `def refund():` sitting in the file: a false green on this
# island's own load-bearing row. Leading space, trailing TAB and the CRLF variant too.
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/format-char-path.tsv    # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/malformed/format-char-literal.tsv # exit 2
# an invisible respelling: U+FEFF inside a path, U+200B inside a literal. Both used to
# match nothing and hold forever; now neither can be written at all.
python3 scripts/plan-decay.py --root scripts/fixtures/plan-decayed scripts/fixtures/malformed/confusable-path.tsv    # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-decayed scripts/fixtures/malformed/fullwidth-path.tsv     # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-decayed scripts/fixtures/malformed/confusable-literal.tsv # exit 2
# a VISIBLE respelling - the invisible one's twin. `absent src/rеfunds.py` with U+0435
# CYRILLIC SMALL LETTER IE, `absent src/ｒefunds.py` with U+FF52 FULLWIDTH r, and the
# same Cyrillic letter inside a `lacks` literal. All three returned `PLAN HOLDS` and
# exit 0 against this decayed tree before the fix - the third against a file that
# holds `def refund(` right there. Aimed at plan-decayed so the refusal cannot be
# mistaken for the tree simply not having the file.
python3 scripts/plan-decay.py --root scripts/fixtures/binary-target scripts/fixtures/binary-target/assumptions.tsv  # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/nope scripts/fixtures/batch-plan.assumptions.tsv         # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds                                               # exit 2
python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds scripts/fixtures/batch-plan.assumptions.tsv >&-  # exit 2
bash scripts/fault-probes.sh                                                                                   # exit 0

python3 scripts/plan-decay.py --root scripts/fixtures/plan-holds --digest src/payments.py                      # exit 3
python3 scripts/plan-decay.py --root scripts/fixtures/blind-spot-vacuous scripts/fixtures/blind-spot-vacuous/assumptions.tsv  # exit 0
# LIMIT, not a pass. Both rows are true and neither names src/payments.py, the module the batch
# was written to edit, which is gone. The gate sees only what the plan chose to write down.
python3 scripts/plan-decay.py --root scripts/fixtures/blind-spot-confusable scripts/fixtures/blind-spot-confusable/assumptions.tsv  # exit 0
# The second LIMIT. `absent src/асе.py` is 'ace' with every letter respelled into
# Cyrillic - one word, one script, so the mixed-script refusal has nothing to catch -
# while src/ace.py sits in the tree. Captured as a run rather than named as closed.

# The interpreter's 120 - a std-stream flush failing at SHUTDOWN - never reaches an in-run
# handler, because argparse exits before them. Both of these are 120 when the same file is
# given a plain `sys.exit(main())` tail instead; that counterfactual was run, not assumed.
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run(
  [sys.executable,"scripts/plan-decay.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # 2
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run(
  [sys.executable,"scripts/plan-decay.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'   # 2
# And the informational code, which asserts a digest was PRINTED: with stdout dead it used
# to leave through 3 with nothing written. It leaves through 2.
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run(
  [sys.executable,"scripts/plan-decay.py","--root","scripts/fixtures/plan-holds",
   "--digest","src/payments.py"],stdout=w,stderr=subprocess.DEVNULL).returncode)'                     # 2
```

Thirty-six runs, each proving one thing the others cannot. The pair is `plan-decayed` versus `plan-holds` on *one* assumptions file, so a green cannot come from a friendlier input. `variant-spelling` is the input a plain `Path.exists()` answer would wave straight through. On a case-sensitive filesystem it reports `src/refunds.py` as still absent while a sibling agent's `src/Refunds.py` sits right there, and the plan proceeds to create a second module. Here it halts. `bom-crlf` and `unicode-nfd` are the two inputs an ordinary editor and an ordinary macOS checkout produce; decoded as plain UTF-8, the BOM'd file's first field is `'﻿# saved by a Window…'`, an unknown kind.

The seventeen malformed rows are refusals, not skips: each is a shape a line-oriented parser plausibly swallows in silence. Three of them were **watched consenting before the fix**: a `lacks` literal with one trailing space, and the same row respelled with U+FEFF in the path or U+200B in the literal. Each returned `PLAN HOLDS` and exit 0 against a tree that had already diverged. Three more were **forged and watched consenting in the session that closed them**, the *visible* respellings, which have the invisible one's mechanics exactly. `absent src/rеfunds.py` (U+0435), `absent src/ｒefunds.py` (U+FF52) and `lacks src/payments.py 'def rеfund('` each printed `PLAN HOLDS` and exited 0 against `plan-decayed`, the last of them while `def refund(` sat in the named file.

`create-only.assumptions.tsv` is the same discipline applied to the *root*. Run with no `--root`, it was watched printing `against . - 3 held, 0 diverged` and exiting **0** from an unrelated cwd; it now leaves through argparse at 2. Four faults were **watched taking a consenting code on this script before the fix**: the three padded/invisible rows above, plus a run whose stdout was closed before it started. That one exited **0** with the whole report silently discarded, because CPython sets `sys.stdout` to `None` and `print` then does nothing at all. The 120 pair is the measured counterfactual above, not a remembered one. `fault-probes.sh` captures what a repo cannot store: an unreadable subdirectory, an un-encodable report proving the `BaseException` seal is live, an assumptions path that is a directory, and a normalisation collision that skips out loud on a filesystem that folds NFC and NFD. Deleting any fixture returns the gate to `unverified`.

## Boundaries — who owns what

- **How big a batch should be** — the small-batch argument and its $1-house economics are [`story-cadence`](../story-cadence/SKILL.md)'s doctrine (C20, C21). This island says nothing about batch size; it only detects that the batch's plan stopped being true.
- **Ticket machinery** — turning a plan into specs, tickets with blocking edges, and implementation passes is [`spec-pipeline`](../../COMPANION.md#spec-pipeline)'s seat. This island reads an assumptions file; it never issues, orders, or closes a ticket.
- **Killing a contaminated context** — an agent already steered by the dead plan carries that trajectory (C11), and whether to continue or kill and respawn is [`trajectory-hygiene`](../trajectory-hygiene/SKILL.md)'s seat.
- **Gate acceptance** — the red/green ritual this island submitted to belongs to [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md); the fixtures above are that island's rule applied here.

## Done when

- [ ] The plan ships an assumptions file naming every file the batch reads, edits, or creates: `unchanged` for anything a sibling agent could touch.
- [ ] `plan-decay.py` exits 0 immediately before the batch starts and again before any agent resumes from that plan.
- [ ] Every exit 1 was answered with a re-plan written from the current tree, never with a patched old plan.
- [ ] Any exit 0 that later proved wrong was answered by adding the assumption that would have caught it. The blind spot above is closed one row at a time, by hand.

**A plan that cannot be checked cannot go stale loudly. Write the assumptions down, and halt the fleet the moment one of them stops being true.**
