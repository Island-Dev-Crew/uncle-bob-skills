---
name: acceptance-surface-review
description: Fixes what a human actually reads once agents write the code - the Gherkin acceptance spec and the QA procedure, never the implementation, with the surface widened by blast radius until code itself enters it on genuinely dangerous paths. Reach for it when standing up human review over agent-generated work, when a reviewer has started walking generated diffs line by line, or when the user says "what am I supposed to review", "acceptance surface", "do I need to read this code", or "criticality tiers for review". Differentiator - this island owns the review SURFACE and its criticality scaling only; the artifacts are the specifier seat's, their red-green binding is the gherkin gate's, and the verdict ceremony belongs to the Forge.
---

# Acceptance Surface Review: read the spec, not the diff

The pack's core doctrine has a consequence that is easy to state and hard to hold. Bob's position is a division of labor by speed: *"They are fast with code. I am slow with code. So I'm going to let them have the code and I'm going to deal with the stuff around that to make sure it's all okay"* (C1). Pushed to its limit, that becomes *"I'm going to work very hard to get it into a situation where I don't have to look at the code at all"* (C1).

The consequence: **the human's review surface shrinks to the acceptance artifacts.** Not because generated code is trustworthy. Because a human reading generated code line by line re-imposes exactly the slowness the whole architecture was built to remove — *"it's interesting because it's fast, but it's frustrating because it makes me slow"* (C1). Every gate in this pack exists to buy that reading back. A reviewer who opens the diff anyway spends the margin the gates just earned.

This island owns one question: **what is on the surface, and how does criticality widen it.** Research ground for the non-transcript claims: [`martin-canon.md`](../../research/martin-canon.md). Quotes reach this page only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## The surface

Two artifacts, both written for a human to read (C9):

- **The Gherkin acceptance spec.** *"Gherkin is given-when-then stuff. A high level acceptance test"* (C9). The human reads it as the answer to *did we agree on this behavior*.
- **The QA procedure**, written in the second person to an operator: *"You are a human. You are operating this system at the UI. You must prove that the system works"* (C9). The human reads it as the answer to *would I believe this if I ran it myself*.

Alongside them the human reads **gate output, not gate subjects**: the CRAP report, the mutation log, the QA script's binary verdict. Bob's own stated remainder is narrow, the scores plus *spot checks* ([`martin-canon.md`](../../research/martin-canon.md)), never a full read.

The reading asymmetry is why the surface must stay small in absolute terms, not just in kind. Agents read everything they are sent, and *"the things that the agents write, the humans don't read"* (C24). An acceptance artifact that has swollen to three hundred lines has quietly left the surface: it is nominally reviewed and actually skimmed.

Size is therefore a gated property here, not a style note, and it is gated on two ceilings. Newlines alone are not a size. A numbered QA list with no blank lines between its items is ordinary markdown, and it packs tens of kilobytes under any line cap.

## Criticality scales the surface

The blast radius of the change decides how much surface the human buys. Three tiers. **The ladder is this island's construction, not a transcript claim:** its only ground in the source is that Bob keeps *spot checks* in the loop rather than reading everything (C1). So the tier definitions are `advisory`; only their consequences are checked.

| tier | blast radius | required surface | implementation |
|---|---|---|---|
| `routine` | reversible, contained, no money or identity | spec + QA procedure | **forbidden**: reading it here is the C1 loss |
| `elevated` | user-visible regression, data shape change, new dependency | spec + QA procedure | optional, named if read |
| `critical` | money, credentials, personal data, deletion, anything one-way | spec + QA procedure + code | **required**: at least one named path |

Two failures, and the tiers catch both. **Under-reading** is a money path signed off from prose alone. **Over-reading** is a reviewer walking the diff of a copy change; that one feels virtuous, which is what makes it expensive.

**A human sets the tier.** An agent's assessment of its own blast radius is a hypothesis, never authority: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18). Ask for the assessment, then decide. Tier is declared before review begins. A tier chosen after the reading describes what happened; it is not a bar.

## The manifest and the gate

Declare the surface in a manifest that sits beside the story. Four keys, one per line; paths are relative and resolve against the manifest's own directory, never the cwd:

```
tier: critical
spec: specs/checkout.feature
qa:   specs/checkout.qa.md
code: src/payments/charge.py
```

[`scripts/surface-check.py`](scripts/surface-check.py) renders the verdict on three rules:

- Every declared artifact (`spec`, `qa` and `code` alike) must exist and carry at least one character that is neither whitespace nor an invisible format character.
- Prose artifacts must also sit inside both halves of the human budget: `--max-lines`, default 120, and `--max-bytes`, defaulting to `max_lines × 80` for an 80-column line, so the two move together.
- Code entries must match the tier's policy in both directions.

One helper runs that substance test for all three keys, because a hollow artifact is the cheapest way to fake a surface. `touch src/charge.py` must not satisfy the `critical` tier, three blank lines are not a Gherkin spec, and neither is a screenful of invisible Unicode.

That last case is why the test decodes before it judges rather than calling `bytes.strip()`, which knows only the seven ASCII blanks. It rejects Unicode whitespace (U+00A0, U+2007, U+3000 …) and it rejects the format characters `str.isspace()` does not count: category `Cf`, the BOM and the zero-width spaces, joiners, soft hyphen and bidi marks. Non-breaking spaces are blank lines typed with a different key, and the three-byte BOM is what a Windows editor writes when it saves a file with nothing in it.

The rule is mechanical, so its edge is too, and that edge is **disclosed rather than papered over**. A character that is neither whitespace nor `Cf` counts as substance even when it happens to render blank: braille-blank U+2800 and the Hangul fillers do. A file built only of those still passes. That hole ships as a **passing limit fixture** below, not as a claim that no invisible file can clear the tier.

One resolver, [`declared_path()`](scripts/surface-check.py), is the only place a declared value becomes a path. An absolute value is refused as malformed rather than silently rerouted: it ignores the manifest's directory, and it would judge different files on different machines. Containment is not claimed. A relative value that climbs with `..` resolves as written.

Exit codes carry distinct meanings: `0` clean, `1` a surface breach, and `2` a malformed manifest, an IO failure, an undeliverable verdict or an unexpected internal error. A broken manifest can therefore never read as a pass, and CI branching on `1`-vs-`2` can never mistake an unreadable file for a real verdict. **There is no fourth code the script can return.** A death by signal is still the OS's status and not the gate's, which is the boundary rather than a hole.

The rest is a property of the seal at the foot of the script rather than an intention. It catches `BaseException`, so no unhandled error can wear `1`, the code reserved for a verdict. It also flushes both streams while a failure can still be caught, because CPython replaces the exit status with `120` when its own shutdown flush raises. `120` was live here until this round: `surface-check.py --nope` with a dead stderr pipe exited it. `err()` raised on the write, and an exception raised inside an `except` handler is not caught by that handler's siblings, so a usage error walked out past the seal wearing a code no table names. `err()` now swallows a vanished stderr and lets the exit code carry the refusal alone. Both probes are in the proof block below.

An unrecognised key is malformed, not ignored: a typo'd `cod:` must not smuggle a critical change through with no implementation on the surface. A manifest that is not valid UTF-8 is malformed on the same terms and exits `2`; nothing was judged. So is a path the OS cannot name. An embedded NUL is refused at parse as a control character, and `declared_path()` catches whatever still reaches `.resolve()` — that call raises `ValueError`, not `OSError`, so an earlier build's uncaught one exited `1`, the code reserved for a verdict. A budget flag outside `1..1000000000` is a usage error on the same terms, bounded explicitly so a 5000-digit argument refuses identically whatever `int_max_str_digits` a box is tuned to.

**And a line is what a human sees as a line.** The manifest's bytes are decoded here rather than read in text mode, because Python's universal-newline translation rewrites a bare `\r` into `\n` *during decode*: that splits a line the reader sees as one, and it hides the CR from the control check entirely. The decoded text is then split on `\n` alone.

TAB is the one control character a line may carry anywhere in it, and a single trailing CR is the one other tolerance, stripped as a CRLF ending before the check runs, so a CR anywhere else in the line is refused like the rest. Every other control character is refused: the whole C0 and C1 range plus U+007F, which covers every separator `str.splitlines()` would also break on (U+000B, U+000C, U+000D, U+001C–U+001E, U+0085), and the Unicode separators U+2028/U+2029.

Two earlier builds lost this class one separator at a time, U+2028 first and then a bare `\r`. Each time, an invisible character inside a `#` comment hid a whole `code:` declaration from the reader while still satisfying the `critical` tier, exit `0`. Both are fixtures now, because the class is what is claimed, not the instance. The lenient direction is fixtured too, and it is why the rule is not simply *no CR ever*: a leading BOM with CRLF endings is what a Windows editor writes, and that manifest still passes.

Delivery is held to the same bar. If the verdict cannot be printed at all (stdout closed, pipe broken) the gate exits `2` with an `ERROR` on stderr, rather than returning a code no one can read the report for. And when fd 2 is itself gone — closed, or a pipe whose reader has left — the exit code carries the refusal alone, since `print(file=sys.stderr)` would otherwise reroute that `ERROR` onto the verdict stream or raise straight out through the seal.

**Red/green proof.** The gate earns its `enforced` claim by having been watched failing: the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. All ten fixtures ship beside it, nine gates and one **disclosed limit** — the fixture that ships passing on purpose. Then come the two seal probes, which are runs rather than fixtures because no file can carry a dead pipe. Recompute from this island's directory, and read each exit code with `rc=$?` on the line after the run, never through a pipe. The seal probes print the child's own return code instead, for that same reason:

```bash
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/dirty-critical.manifest    # exit 1 - 2 breaches
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/hollow-critical.manifest   # exit 1 - 2 breaches
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/packed-critical.manifest   # exit 1 - 1 breach (3834 bytes on 21 lines)
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/invisible-hollow-critical.manifest  # exit 1 - 1 breach, no VISIBLE content
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/unusable-path-critical.manifest  # exit 2 - ERROR, not a verdict
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/smuggled-code-critical.manifest  # exit 2 - ERROR, not a verdict
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/cr-smuggled-code-critical.manifest  # exit 2 - ERROR, not a verdict
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/windows-clean-critical.manifest  # exit 0 - BOM + CRLF still passes
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/clean-critical.manifest    # exit 0 - surface complete
python3 scripts/surface-check.py --max-lines 24 scripts/fixtures/limit-blank-glyph-critical.manifest  # exit 0 - DISCLOSED LIMIT, not a pass to trust

# The seal - no run may exit anything but 0, 1 or 2. Both printed 120 before this round.
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/surface-check.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # 2 - usage error, dead stderr pipe
python3 -c 'import os,subprocess,sys;r1,w1=os.pipe();os.close(r1);r2,w2=os.pipe();os.close(r2);print(subprocess.run([sys.executable,"scripts/surface-check.py","--max-lines","24","scripts/fixtures/clean-critical.manifest"],stdout=w1,stderr=w2).returncode)'  # 2 - both streams dead
```

The dirty manifest is a realistic near-miss, not garbage. The tier is honestly declared `critical`, the Gherkin is real, and it still fails: no `code:` path on a payment capture, and a QA doc that grew to 31 lines against a 24-line budget.

The hollow manifest is the harder one, because nothing about it looks wrong. Every key is present and every path resolves, yet the `spec` is three blank lines and the declared money path is a zero-byte file. It was run against an earlier build of this script and **passed** — `ok … surface complete for its tier`, exit 0 — which is why the substance test is now one shared helper rather than a prose-only check.

The packed manifest is the third: complete, honest, and under the line budget at 21 lines, because its QA steps sit one per line with no blank lines between them. It passed a line-counting build of this script at both the fixture budget and the shipped default: 3,834 bytes waved through on 21 lines as "surface complete", and nothing in a line count bounds how much larger that number can get. That is why the byte ceiling exists, and why it is the only leg that fails here. (Re-run it as `--max-lines 24 --max-bytes 100000` to watch the line-only build wave it through again: exit 0.)

The last two are not verdicts at all, and that is the point. The unusable-path manifest declares a `spec:` whose path carries an embedded NUL, which an earlier build followed into `.resolve()` and crashed on with an uncaught `ValueError` — **exit 1, the code reserved for a breach**. The smuggled-code manifest hides a `code:` declaration behind an invisible U+2028 inside a `#` comment, which an earlier build read as a second line and scored as `ok … surface complete`: **exit 0 on a critical change with no code on the human's surface**. Both now exit `2` with an `ERROR` line.

Three fixtures were added when a third adversarial round found the first two rules had each been closed for one instance rather than as a class. The **cr-smuggled** manifest is the U+2028 fixture with a bare `\r` in place of the separator, and it passed the build that shipped the U+2028 fixture: exit 0 on the same money path, because `read_text()` had already turned the CR into a newline before the control check could see it. The **invisible-hollow** manifest declares a money path holding 101 bytes of BOM, non-breaking spaces and zero-width spaces; the byte-strip build called that content and passed it, and the substance test that catches `touch` was left claiming more than it did.

The **windows-clean** manifest is the guard on the other side: byte-for-byte what a Windows editor writes, a leading BOM and CRLF endings, and it must keep exiting 0. A defence against invisible separators that costs an ordinary Windows author their pass has taken the margin the gate exists to buy. The clean manifest sits exactly at the budget (24 lines), so the set proves the gate discriminates at the boundary rather than rejecting everything long.

The tenth is not a gate at all. **limit-blank-glyph ships passing**, and it is here so the substance test's edge is a run with a recorded exit code instead of a sentence nobody checked: braille blanks and Hangul fillers are neither whitespace nor format characters, so the gate calls them content, exit 0. Close that and the fixture becomes a tenth gate; leave it and the claim above stays honest.

The two runs after them are not fixtures, because a dead pipe cannot be checked into a directory. Each hands the gate a stream whose reader is gone, and each exited `120` against the build that shipped the ten fixtures: a usage error and a clean verdict both wearing a code this island's table never named. Deleting any fixture, or either probe, returns the gate to `unverified`.

## Boundaries

- **The verdict ceremony is not mine.** Who may review (never the author), what a verdict binds, when a verdict voids on a moved head: that is the Forge's [`cross-family-review`](../../COMPANION.md#cross-family-review), and this island **invokes it, never redefines it**. The ruling is recorded as audit line 3 of [`03-FORGE50-AUDIT.md`](../../03-FORGE50-AUDIT.md). This island decides what lands in front of the reviewer; that island decides what the reviewer's "yes" is worth.
- **The artifacts are produced upstream.** The Gherkin spec and the QA procedure are the output contract of [`specifier-seat`](../specifier-seat/SKILL.md). What a well-formed scenario or QA step looks like is settled there, and is not restated here. This island never authors the surface; it rules on whether the right surface was put in front of a human.
- **Their red-green binding is gated elsewhere.** That the scenarios fail before implementation and pass after is [`gherkin-gate`](../gherkin-gate/SKILL.md)'s enforcement. Review reads the passing spec; it does not re-derive that the spec was ever red.
- **The executable QA run is [`qa-script-seat`](../qa-script-seat/SKILL.md)'s.** The human reads the procedure and the script's binary verdict; determinizing procedure into script belongs to that seat.
- **What this island owns, entirely:** the composition of the review surface, the criticality ladder that widens it, and the check that the declared surface matches the declared tier.

## Enforced vs advisory

- `enforced` — everything [`scripts/surface-check.py`](scripts/surface-check.py) decides and nothing more: existence and visible-character substance for all three artifact keys, both prose size ceilings (lines and bytes, so packing prose onto long lines evades neither), the tier's code policy in both directions (`critical` without code fails; `routine` with code fails), and fail-closed handling of a malformed or tier-less manifest. All ten fixtures and both seal probes were run above. The adversarial cases (typo'd key, duplicate `tier:`, uppercase tier, indented key, absent manifest, directory-as-manifest, FIFO-as-manifest, unreadable manifest and unreadable artifact, declared-but-missing path, symlink loop, `touch`ed zero-byte code path, whitespace-only spec, invisible-Unicode-only artifact, non-UTF-8 manifest, absolute path, embedded NUL, U+2028 and bare-`\r` line smuggles, C1 controls, mid-file BOM, `--max-lines 0|abc|9…9|missing`, a 5000-digit budget, closed stdout, closed stderr, **dead stderr pipe on a usage error, both streams dead**, broken pipe mid-report over 4000 manifests, an **injected internal error** on a patched copy, and **SIGINT mid-report**) were run too, and each lands on the exit code that matches its meaning: verdicts on `1`, unjudgeable input, undeliverable output and unexpected errors on `2`, never shared. Across every one of those runs only `0`, `1` and `2` were observed, and the seal is what turns that survey into a property: two of them exited `120` before it, and no survey can promise what a missing `except` clause would have let through next. The lenient direction was run as well: `./p`, `p//q`, `p/../p`, a leading BOM, CRLF endings and a TAB after a key all still pass. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — every judgment the script cannot make: which tier a change deserves, whether the scenarios actually cover the behavior, whether the human read what they declared, and the tier definitions themselves. **The manifest is a declaration, not a witness.** It proves the right surface was assembled, never that a person read it. Claiming otherwise would launder advisory into enforced, and the boxes below are where that judgment is recorded by the human who made it.
- `advisory` — **the budget's two defaults (120 lines, 80 bytes per line) are `unverified`**: starting numbers, not calibrated ones. Tune them the pack's way: run the gate, capture outcomes, let the evidence pick the values, and never let an agent vote them up (C18). Name the remaining hole rather than leave it implied. **The ceilings measure bulk, never density.** A short, dense spec can still be unreadable, and no count catches that; reading load is judged by the human at the boxes below, not by the gate. The substance test's hole is named on the same terms: it rejects whitespace and format characters, not every codepoint that renders blank, and `limit-blank-glyph-critical.manifest` is that hole as a run with an exit code rather than a caveat nobody measured.

## Done means

- [ ] Tier declared **before** reading, by a human, with the blast radius named in one line
- [ ] `surface-check.py` exits 0 on the story's manifest at the declared budgets (lines and bytes)
- [ ] Spec and QA procedure read end to end; any scenario the reviewer cannot restate in a sentence bounces upstream to [`specifier-seat`](../specifier-seat/SKILL.md) rather than being resolved by reading the code
- [ ] Gate output read (CRAP report, mutation log, QA script verdict): reports, not their subjects
- [ ] At `critical`, each declared code path opened and the reading recorded; at `routine`, the diff stayed closed
- [ ] Verdict issued through [`cross-family-review`](../../COMPANION.md#cross-family-review), by someone who did not author the change

An open box means the review stays `unverified`. Repair the surface (widen it, shrink an artifact, correct the tier), then re-run the check and re-walk the boxes. A verdict issued over an unchecked surface is a claim, and claims are not evidence.

**The human reads the specification and the proof, never the transcript of the machine's work. The only thing that widens that surface is blast radius.**
