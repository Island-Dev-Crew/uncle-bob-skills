---
name: values-not-disciplines
description: Rule-inventory gate over a harness's quality rules - each rule must name the tool that measures it or carry an explicit advisory label, so a prose-only rule like be clean, write good tests, or keep it simple is ruled a breach instead of passing as a standard. Reach for it when checking whether a harness's quality bar is real, before trusting a rules file you inherited, or when someone says "every rule needs a tool", "is this rule actually enforced", or "we told the agent to write clean code". Differentiator - it asks of every rule, wherever that rule lives, whether a measuring tool is named at all; which side of the prompt-versus-gate line a rule belongs on is steering-audit's seat, and retuning a threshold's number is threshold-port's.
---

# Values Not Disciplines: name the tool or say advisory

The pack's second law, in Bob's own words: *"it's probably a mistake to impose a human discipline on an agent. It is not a mistake to impose human values on the agent, but there may be thresholds that we need to change"* (C17, [ledger](../../01-CONCEPT-LEDGER.md)). The value survives the port. The ritual does not. The number moves. This island makes that law checkable by attacking the one place it fails silently: a value nobody ever turned into a measurement, still sitting in the rules file as a sentence.

His corollary is the whole argument: **"You can't tell an agent to be clean. You have to measure the cleanliness that they produce and have them correct failures."** That line is from X, not the conversation, and it is sourced in [`martin-canon.md`](../../research/martin-canon.md). The same file records that agents treat a rules file *"in the Pirates of the Caribbean sense. They're more like guidelines"* (C3). The reason is positional, and no rewording fixes it: *"the 50th and the 80th sentence in there, they're gone"* (C3). A tool has no middle: *"you're putting them into a loop"* and it holds *"until this tool says that it's okay"* (C4).

So a quality rule in an agent harness has exactly two honest shapes. Either a tool measures it, or you admit out loud that nothing does.

## The one question

Walk every quality rule the agent works under. The standing prompt, the CI config, the review checklist, the README's "we always…" paragraph, the rule a senior keeps repeating in review: each one gets the same question. **What tool measures this?** Three answers are possible, and only two are legal.

| answer | verdict | meaning |
|---|---|---|
| a command that runs and can exit non-zero | `MEASURED` | the rule survives the middle of a context |
| the literal label `advisory` (plus a reason) | `ADVISORY` | honest - the rule asks, it cannot make |
| a sentence | breach | a wish wearing the costume of a standard |

The advisory answer is not a failure state. Some rules are generative by nature: architecture intent, style direction, what to reach for when. No artifact check substitutes for those, so labeling one `advisory` is the correct outcome. What the gate forbids is the third answer passing itself off as the first.

## The inventory

The deliverable is one table, every rule a row, no exceptions carved out:

| rule | measured by | verdict |
|---|---|---|
| per-function CRAP ceiling at 6 | `python3 tools/crap-score.py --threshold 6` | `MEASURED` |
| no outward dependency across the layer fence | `tools/dep-check.sh` | `MEASURED` |
| prefer editorial layout over template grids | `advisory: generative - no artifact check can substitute` | `ADVISORY` |
| keep the code clean | *(nothing)* | breach - repair or label |

Count the columns when you are done. **An inventory where advisory outnumbers measured is a finding, not a pass** — it says the quality bar is mostly hope. That ratio is a judgment call, with no mechanical floor here (advisory).

## What the gate refuses

Five laundering moves each get their own verdict, because someone has tried every one of them to make an unmeasured rule look measured:

- **Prose in the measure column.** `be clean`, `manual review`, `code review`, `TBD`. A word list rejects these *before* PATH resolution, so an installed editor CLI named `code` cannot rescue the phrase "code review".
- **A sentence whose first word happens to be a binary.** `sort out the layering`, `look at complexity in review`, `head off long functions early`. Resolving on PATH is not sufficient. The measure must also carry command shape: a tool path that resolves under `--root`, at least one flag, a path operand that resolves, or a single bare tool name. `find . -name '*.py'`, `tools/dep-check.sh`, and bare `pytest` keep passing; the sentences do not. This is a strong filter, not a proof of non-Englishness. *Enforced vs advisory* names the residue it leaves.
- **A no-op executable, bare or wrapped.** The always-exit-0 list is exactly `true`, `:`, `echo`, `yes`, `pwd`, plus `env true`, `nice true`, `timeout 60 true`. Its mirror image `false` is ruled the same way for the opposite reason: always non-zero, so the fix-until-green loop never ends. Nothing else is on either list. `test -f coverage.xml` and `cat report.txt` **can** exit non-zero, so they count as honest measures, judged on shape and never told they cannot fail. Wrappers (`env`, `nice`, `command`, `timeout`, `sudo`, `xargs`, `nohup`, …) get peeled off *before* the no-op test runs, along with their own flags, `VAR=VALUE` assignments, and durations. A four-character prefix therefore cannot launder the same no-op. When the peel budget runs out with a wrapper still at the head, the row reads `PROSE-ONLY`, so nine `env`s cannot buy what one cannot. A gate that cannot go red is not a gate (that acceptance rule belongs to [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)).
- **A tool that does not exist, or cannot execute.** `python3 tools/simplicity-check.py`, where no such file is there. Every path-shaped token must resolve under `--root`. There is no fallback to the auditor's working directory, and `../` cannot walk out of the root. For the command token itself, existing is not enough: it must carry its exec bit or a script extension (`.py .sh .js .ts .rb .pl`). So pointing a rule at the style guide that states it (`./GUIDELINES.md`) gets refused, because a document cannot run, let alone go red. Path *operands* are held to existence only, so `python3 -m pytest tests/test_a.py` and data-file arguments keep passing. One consequence to know: an absolute path to a system binary reads `PROSE-ONLY`; name it bare (`ruff`) and let PATH resolve it.
- **An interpreter naming nothing.** A bare `python3`, or inline code (`python3 -c …`, `sh -c …`, `node -e …`) that names no auditable tool. An interpreter must name a script that exists under `--root`, or an `-m` module that resolves: a module file under `--root` (`python3 -m covgate`), or an importable top-level module on this host (`python3 -m pytest --cov=src`, host-dependent exactly like PATH). `python3 -m cleanliness_checker`, which is nowhere, reads `PROSE-ONLY`.

## Running it

```
python3 scripts/rule-inventory.py [--root DIR] INVENTORY.tsv
```

Rows are TSV: `rule <TAB> measure`. Exit codes carry distinct meanings: `0` clean, `1` a real breach, `2` usage/IO/malformed. A broken pipe therefore can never read as a clean rule set. An empty inventory exits 2, because a rule set with no rules does not pass.

**Red/green proof.** Both fixtures ship beside the script; recompute from this island's directory:

```bash
$ python3 scripts/rule-inventory.py --root scripts/fixtures/harness scripts/fixtures/harness-dirty.tsv
MEASURED   per-function CRAP ceiling at 6  [python3 tools/crap-score.py --threshold 6]
PROSE-ONLY keep the code clean  [prose, not a tool: be]
PROSE-ONLY write good tests  [prose, not a tool: manual]
NO-OP      no hardcoded secrets  ['true' always exits 0 — a gate that cannot go red is not a gate]
PROSE-ONLY keep it simple  [named tool does not resolve under --root: tools/simplicity-check.py]
PROSE-ONLY architecture stays layered  [sentence shape, not a command: sort out the layering]
PROSE-ONLY complexity stays low  [sentence shape, not a command: look at complexity in review]
PROSE-ONLY long functions caught early  [sentence shape, not a command: head off long functions early]
NO-OP      secrets scanned in CI  ['true' always exits 0 — a gate that cannot go red is not a gate]
NO-OP      dependencies audited  ['true' always exits 0 — a gate that cannot go red is not a gate]
PROSE-ONLY nothing reaches outside the harness  [named tool does not resolve under --root: ../../../../../../../etc/hosts]
PROSE-ONLY rules are inventoried  [named tool does not resolve under --root: scripts/rule-inventory.py]
PROSE-ONLY simplicity checked by a module  [-m module does not resolve: simplicity_check]
PROSE-ONLY quality bar documented  [named tool is not executable: ./GUIDELINES.md]
PROSE-ONLY secrets scanned, deeply wrapped  [wrapper chain names no command: env env env env env env env env env true]
15 rules, 1 measured, 0 advisory, 14 unmeasured-and-unlabeled
$ echo $?   # → 1

$ python3 scripts/rule-inventory.py --root scripts/fixtures/harness scripts/fixtures/harness-clean.tsv
MEASURED   per-function CRAP ceiling at 6  [python3 tools/crap-score.py --threshold 6]
MEASURED   no outward dependencies across the layer fence  [tools/dep-check.sh]
MEASURED   tests pass under coverage  [python3 -m covgate --cov=src]
ADVISORY   prefer editorial layout over template grids  [labeled advisory]
ADVISORY   module boundaries read well to a human reviewer  [labeled advisory]
5 rules, 3 measured, 2 advisory, 0 unmeasured-and-unlabeled
$ echo $?   # → 0
```

Both blocks are the full stdout, nothing elided. The dirty fixture fails for fourteen intended reasons, spread across all five laundering moves: bare prose; sentences whose first word resolves on PATH (`sort`, `look`, `head`); a bare no-op and two wrapped ones (`env true`, `nice true`); a tool that does not exist; a `../` escape from the root; a path that exists in the auditor's working directory but not under `--root`; an `-m` module that resolves nowhere; an existing-but-unexecutable `.md` named as the tool; and a nine-deep wrapper chain that names no command. Its one properly measured row still reads `MEASURED`, so the red is discrimination and not a parse error.

The clean fixture carries both advisory forms (`advisory` bare and `advisory: reason`), a tool invoked through an interpreter, and a `-m` module that resolves under `--root`. The green therefore proves two things: the gate accepts an honest label, and it accepts a real Python module invocation rather than demanding a script path everywhere. It also stays green on a bare host, since nothing in it depends on an installed package. Delete either fixture and this island's `enforced` claim reverts to `unverified`.

## Boundaries

**Against [`steering-audit`](../steering-audit/SKILL.md), the adjacent island, where the line is sharp.** That island sorts rules by where they live. It takes one standing prompt and classifies each rule *generative* (stays in the priority zone) or *checkable* (has a mechanical test). Then it executes the migration and deletes the prompt line in the same change that lands the gate. Its axis is location, and its extractor harvests rules out of a prompt file. This island never re-implements that extractor, so feed its output in here. This island instead asks of every rule, wherever it already lives (prompt, CI config, README, a reviewer's habit), whether it names a measuring tool at all, and forces an honest `advisory` label when it does not. The two compose in one direction: steering-audit decides the destination, this certifies the claim. A rule steering-audit already marked `checkable + enforced` still fails here if the gate it names does not exist. A rule that stays generative in the prompt passes here the moment it is labeled honestly.

**Retuning a threshold's number is [`threshold-port`](../threshold-port/SKILL.md).** This gate reads `--threshold 6` as evidence that a tool is named and stops there. A controlled experiment on that island settles whether 6 beats 4 or 8 (C17), never this gate.

**Whether a named tool can actually fail is [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md).** This gate proves a tool *exists*; that island proves it goes red on a known-bad input before it may guard anything. The deepest limit of this island is exactly there: it verifies the naming, not the measuring.

What each gate measures belongs to the gate islands: [`crap-gate`](../crap-gate/SKILL.md) owns the CRAP metric's content, [`dependency-fence`](../dependency-fence/SKILL.md) the layering direction. This island stays agnostic about which tools are good ones.

Two Forge concerns stay off this island. How a named tool gets wired into a hook, pre-commit step, or denylist belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails). Which format the finished inventory lands in belongs to [`evidence-packet`](../../COMPANION.md#evidence-packet): the table plus the exit code become one rung of its ladder, never a second evidence format. Where a "measuring tool" would itself be a model call, whether that clears a cost floor is [`model-routing`](../../COMPANION.md#model-routing)'s call.

## Enforced vs advisory

- `enforced`: the per-row verdict and the exit code. [`scripts/rule-inventory.py`](scripts/rule-inventory.py) rules `MEASURED` / `ADVISORY` / `PROSE-ONLY` / `NO-OP` on every row, exits 1 on any breach, and exits 2 (never 1) on usage, IO, malformed, or empty input. Run in both directions above. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: **completeness of the inventory.** The gate rules on the rows it is given. A rule you never wrote down is invisible to it, so sweeping every rule out of prompt, CI, checklist, and habit stays judgment work.
- `advisory`: **fitness of the named tool.** `MEASURED` means a non-no-op tool was named and every part of the naming resolves: the command token exists and can execute, its path operands exist under `--root`, and an `-m` module is found. Whether the tool measures *that particular rule*, and whether it actually goes red on bad input, is not checked here (see Boundaries).
- `advisory`: **the prose filter is a filter, not a proof.** The word list plus command shape rejects every prose form this island has been attacked with, but it asks "does this look like a command", not "is this English". Residue, captured: `sort alphabetically` and a bare `head` both read `MEASURED`, because a PATH binary followed by at most one bare operand is also the shape of every real subcommand invocation. Resolution is host-dependent in two places, PATH membership for bare tool names and installed packages for an `-m` module, so a measure absent here may resolve on a Linux runner, and the reverse. Read a `MEASURED` row as *shaped like a command that exists here*, never as *this rule is measured*.
- `advisory`: **honesty of an advisory label.** Labeling a checkable rule `advisory` to dodge building its gate passes this gate and fails the pack's first law. The advisory-to-measured ratio has no enforced floor.

Claiming more than this would launder advisory into enforced, which is the exact failure the island exists to catch.

## Done means

- [ ] Every quality rule the agent works under appears as a row: prompt, CI config, review checklist, README, unwritten habit (advisory: completeness is judgment)
- [ ] `rule-inventory.py` exits 0 over the inventory (enforced)
- [ ] Every `MEASURED` row's tool has been watched going red on a known-bad input (advisory here; the ritual is [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s)
- [ ] Every `ADVISORY` row carries its reason, and the report states the advisory-to-measured ratio rather than burying it

An open box keeps the verdict `unverified`. The loop: sweep the rules → run the gate → repair each breach by naming a real tool or accepting the `advisory` label → re-run until exit 0, then re-check the boxes.

**Name the tool or say advisory — a rule with neither is a wish, and agents do not grant wishes (C3).**
