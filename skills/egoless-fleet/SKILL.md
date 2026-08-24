---
name: egoless-fleet
description: Review posture for agent-written work - a review starts from the assumption that defects exist and goes hunting for them, and the record it leaves must be a found-or-falsified list rather than a bare approval. Reach for it when a diff an agent wrote is about to be approved, when a reviewer reports no issues at all, or when someone says 'looks good to me', 'LGTM, ship it', 'the agent says it is correct', 'nothing to flag'. Differentiator - this island owns the posture and what a review record must contain; who may review and what a verdict binds belongs to the cross-family-review ceremony, and durable findings graduate to a finding register.
---

# Egoless Fleet: the review still has to hunt

Weinberg named it in 1971: *egoless programming*, peer review whose goal is that defects get found, by anyone, the author included ([seventies-canon](../../research/seventies-canon.md), which summarizes the idea and cites the book rather than quoting it). The brief's own verdict is that it transfers cleanly to agent output. Review the work the way peers reviewed each other. Assume defects exist. Find them without attachment.

It transfers almost too neatly. What made egoless review hard was the author's ego: the defense, the flinch, the argument. An agent has none. Nobody in the room wrote the code, so nobody is wounded by a finding.

And that is where it inverts. Weinberg's failure mode was *the author refusing to hear defects*. The agent-era failure mode is *the reviewer refusing to look for them*. With no author to protect and no colleague to embarrass, reviewing agent output costs nothing socially. So it collapses into a glance, and the glance returns "looks good." The ego left the room and took the search with it.

This island is the counterweight. It carries the posture that keeps the hunt running when nothing personal is at stake, plus the one mechanical thing anyone can check about it: what the review record contains.

## Why the hunt is not optional here

**The agent's own assurance is not evidence.** Bob, on polling the agents: *"I've had a number of debates with the agents, and by the way, you can't trust any debate you have with an agent, but I still have them anyway"* (C18, via [the ledger](../../01-CONCEPT-LEDGER.md)). An agent asserting its diff is correct, a second agent agreeing, a summary that says "all tests pass": that is color, not a finding. Any of it may generate hypotheses for the hunt. None of it closes one.

**Unfound defects compound.** *"they are as subject as humans are to messy code… The code can get messy enough that the agents cannot deal with it any longer and then they'll just start to spin"* (C2). A defect waved through does not sit still. It becomes the substrate the next agent works on. A review that stops looking is not neutral; it is a deposit.

**Someone has to know what failure looks like.** *"the important part was the next step where I watched them thrash. I could see the agent struggle and I recognized the struggle since I have been through that struggle… the novice would come in and not recognize the struggle"* (C27). Hunting is a trained skill. The posture below is what a trained reviewer already does. It is not a form a novice fills in and thereby becomes one.

**The record has to survive a human's attention span.** *"the things that the agents write, the humans don't read"* (C24). So the record stays short, enumerated, skimmable: a list, not an essay.

## The posture

Five moves. All five are judgment, and all five are `advisory`, because no script here can tell whether you actually made them.

1. **Open with a defect budget, not a verdict.** Enter expecting to find `n` defects. Finding zero is a result you have to *earn*, not a default you arrive at by not looking.
2. **Hunt by hypothesis.** Name what you suspect before you go looking: a boundary that is probably unchecked, a test that probably asserts nothing, an error path that is probably untried. Then go check it. A hypothesis you check and rule out is a real review product. It is the *falsified* half of the list.
3. **Attack the tests as hard as the code.** Agent-written tests are agent-written work. A suite that passes because it asserts almost nothing is the most common thing a glance approves.
4. **Never let an agent close a hypothesis.** Ask an agent for hypotheses freely. Close them yourself against the artifact, or with a check that could have failed (the repo law, [CONTEXT.md](../../CONTEXT.md)).
5. **Say what you did not look at.** An unexamined region named out loud is a boundary. An unexamined region left silent reads as reviewed.

## The record: found-or-falsified

The review's output is a record, and its shape is the one part of all this that a machine can hold you to. Every line is blank, a `#` comment, or an entry:

```
# Review record - payments/refund story, seat: reviewer-2
FOUND      R1 refund.py:88 partial refund over the captured amount is accepted
FALSIFIED  R3 suspected double-refund on retry - replayed the key, second call no-ops
```

`FOUND` is a defect you can point at. `FALSIFIED` is a hypothesis you chased and ruled out, the evidence that the hunt happened when it turned up nothing. Starting `FOUND` text with `path:line` and `FALSIFIED` text with the hypothesis is convention: `advisory`, unchecked. A record with no entries is a bare approval, and the gate refuses it.

## The gate

[`scripts/review-record.py`](scripts/review-record.py) checks the record's shape and nothing else. It has no opinion about whether a finding is real, whether the hunt was thorough, or whether the record should be accepted. That judgment belongs to the reviewer and to the ceremony. Run it from this island's directory:

```bash
python3 scripts/review-record.py scripts/fixtures/bare-approval.md   # exit 1
python3 scripts/review-record.py scripts/fixtures/hunted.md          # exit 0
```

A *line* here is a run of characters between LF bytes. The record is split on `\n` alone, never with `str.splitlines()`, which also breaks on `\r`, `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e`, U+0085, U+2028 and U+2029. Under that looser split, one physical line reading `# … LGTM, ship it.` could carry counted entries behind a character no editor shows. So before any line is read, a record holding any control character but TAB, LF and the CR of a CRLF pair, or holding U+2028/U+2029, is refused with exit `2` and an `error:` line naming the byte offset. A line the parser splits and the reader does not is a line nobody reviewed, so it is not a verdict either way.

What it enforces on top of that:

- At least `--min` entries, default 1. `--min 0` is refused as a usage error, so the rule cannot be switched off.
- Ids distinct after NFKC + casefold + NFC normalization, the one documented key function. That is why `R2`, `r2`, fullwidth `Ｒ２` and NFD `café` collide rather than each counting.
- An id carrying a character that renders as nothing is refused at exit `2` rather than counted as a second id that looks like the first. Two sets qualify. Unicode categories Cf, Cc, Zl and Zp catch `R⟨U+200B⟩2`, which no normalization form removes. A fixed `DEFAULT_IGNORABLE` table in the script catches the joiners, fillers and variation selectors those categories miss, such as `R⟨U+034F⟩2`. The table is transcribed from Unicode 15 and does not grow when Unicode does. Category Mn is deliberately not folded in wholesale, because that would refuse a legitimate NFD `café`, a worse trade than the forged ids it would catch.
- Every line that is not blank and not a `#` comment is either counted as an entry or refused *by line number*. Nothing is dropped in silence.

Entries are matched end to end, so `FOUNDATION R1 …` is refused rather than read as a `FOUND`, and a `FOUND` written inside a `#` comment counts for nothing: only a line that *is* an entry is an entry. A UTF-8 BOM is stripped and CRLF is handled, because editors and Windows checkouts produce both.

Exit codes: `0` pass, and `--help`. `1` refused, for too few entries, a duplicate id, or a malformed line. `2` usage error, unreadable/non-regular/oversize/undecodable file, a record carrying an invisible character (a control character anywhere, a character that renders as nothing inside an id), or an exception escaping `main()`. Every error path reached in the hardening run exits `2`. The script's tail catches `BaseException`, `SystemExit` included, and maps it to `2` with an `error:` line, so a crash cannot arrive wearing a verdict's code. That mapping was watched, not assumed: the third probe below injects `raise SystemExit(1)` at the top of `main()` and reads what the process returns.

### Red/green proof

The gate earned its `enforced` line by being watched failing, the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. All commands run from this island's directory:

```bash
python3 scripts/review-record.py scripts/fixtures/bare-approval.md      # exit 1
python3 scripts/review-record.py scripts/fixtures/malformed-entry.md    # exit 1
python3 scripts/review-record.py scripts/fixtures/duplicate-id.md       # exit 1
python3 scripts/review-record.py scripts/fixtures/hunted.md             # exit 0
python3 scripts/review-record.py scripts/fixtures/bom-crlf.md           # exit 0
python3 scripts/review-record.py --min 6 scripts/fixtures/hunted.md     # exit 1
python3 scripts/review-record.py scripts/fixtures/smuggled-comment.md   # exit 2
python3 scripts/review-record.py scripts/fixtures/smuggled-cr.md        # exit 2
python3 scripts/review-record.py scripts/fixtures/invisible-id.md       # exit 2
python3 scripts/review-record.py scripts/fixtures/default-ignorable-id.md   # exit 2
bash ../known-dirty-fixture/scripts/prove-gate.sh scripts/fixtures/bare-approval.md scripts/fixtures/hunted.md -- python3 scripts/review-record.py   # exit 0
```

`bare-approval.md` is three `#` lines ending in "LGTM, ship it"; it fails on the count, not on a parse error. `malformed-entry.md` fails on a lowercase `found`, a keyword with no id, and a bare `LGTM otherwise`, each named by line. `duplicate-id.md` is CRLF-encoded and collides `café`/`café` (NFC vs NFD), `R2`/`r2`, and `R3`/fullwidth `Ｒ３`. `hunted.md` carries 2 FOUND and 3 FALSIFIED. `bom-crlf.md` is byte-identical ordinary editor output, BOM and CRLF, and it passes, so the encoding path is proven green as well as red.

The last four fixtures are the smuggling closure, each of them text the eye reads as harmless. `smuggled-comment.md` is a single physical line, a `#` comment ending in "LGTM, ship it.", with a FORM FEED before a `FOUND`; `str.splitlines()` would score it as a comment *plus* a counted entry and exit 0. `smuggled-cr.md` does the same with a bare CR. `invisible-id.md` enumerates `R2` and `R⟨U+200B⟩2` as two entries that render as one id. `default-ignorable-id.md` does that with U+034F, the combining grapheme joiner, which is category Mn and walked straight through the earlier category-only rule. All four now exit `2`, named by byte offset or by line.

Three probes cover the tail. The dead-pipe pair prints `2`; the SystemExit injection exits `2`:

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/review-record.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # prints 2
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/review-record.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # prints 2
python3 -c 'import pathlib,subprocess,sys,tempfile;s=pathlib.Path("scripts/review-record.py").read_text().replace("def main():","def main():"+chr(10)+"    raise SystemExit(1)",1);p=pathlib.Path(tempfile.mkdtemp(),"probe.py");p.write_text(s);sys.exit(subprocess.run([sys.executable,str(p),"scripts/fixtures/hunted.md"],capture_output=True).returncode)'   # exit 2
```

### The blind spots, captured

A record's shape cannot show who wrote it, whether the hunt behind it happened, or whether two ids that differ in bytes are the same id to a human eye. Both gaps ship as captured runs rather than as sentences:

```bash
python3 scripts/review-record.py scripts/fixtures/template-echo-blind-spot.md    # exit 0
python3 scripts/review-record.py scripts/fixtures/homoglyph-id-blind-spot.md     # exit 0
```

Paste this island's own format example into a record and the gate consents: two placeholder entries, `2 entries (1 FOUND, 1 FALSIFIED)`, exit 0. Swap the Latin `R` of a second id for a Cyrillic `Р` (U+0420) and it consents again. A confusable is a visible character, and the id rule covers characters that render as *nothing*, not characters that render as *something else*. Unicode confusable folding is not in this script, and this island does not claim it. Both greens mean "this record is a found-or-falsified list", never "this review happened". Only a human reading the entries catches a copied template or a lookalike id, which is why the ceremony below, not this script, is what accepts a review.

## Enforced vs advisory

- `enforced`, the record's shape: entry grammar, the minimum entry count, distinct ids, the refusal of any line that is neither blank, comment, nor entry, and the refusal of any record whose invisible characters would make the parser and the reader see different lines. Exit-code gated, proven red and green above.
- `enforced`, this island's own structure, via the pack validator `../../scripts/validate-island.py`.
- `advisory`, and it covers everything that matters most: the five posture moves, the defect budget, whether a `FALSIFIED` line was actually checked, whether the `FOUND` list is complete, and the `path:line` convention. No tool on this island judges any of them, and none pretends to. Under the pack's second law that is stated, not implied: this island's rules are mostly values, and the gate holds only the record.
- `advisory`, the wiring: putting the gate into a hook or CI is [`agent-guardrails`](../../COMPANION.md#agent-guardrails)' plumbing. Nothing here installs itself.

## Boundaries

- **The verdict ceremony and who may review** belong to [`cross-family-review`](../../COMPANION.md#cross-family-review): an independent reviewer from a different model family, a verdict bound to an exact head, voided when the head moves, and the law that the seat which wrote the code never reviews it. This island never defines a verdict format, a reviewer eligibility rule, or a binding. It says what posture the reviewer holds, and what the record must contain when they invoke that ceremony.
- **Durable findings graduate** to [`finding-register`](../../COMPANION.md#finding-register): enumeration at an exact SHA, provenance marks, collision-free ids across reviews. A `FOUND` line here is a live entry in one record. The moment it has to outlive that record it belongs in the register, and the ids this gate checks are distinct *within one file*, nothing more.
- **Detecting an agent thrashing** (circling, change-one-break-another, giving up) is [`thrash-watch`](../thrash-watch/SKILL.md)'s seat, watched live during a run. This island acts after the work exists, on the artifact.
- **The evidence format** a review's captured runs travel in is [`evidence-packet`](../../COMPANION.md#evidence-packet)'s. A record is a rung inside it, not a second format.

## Done when

- [ ] The reviewer entered expecting defects, and can name the hypotheses they went in with.
- [ ] The record has entries, `FOUND` or `FALSIFIED` or both, and `review-record.py` exits 0 on it.
- [ ] Zero findings, if that is the result, is backed by `FALSIFIED` lines rather than by silence.
- [ ] No hypothesis was closed on an agent's say-so (C18).
- [ ] Unexamined regions are named in the record as `#` lines, not left implied.
- [ ] Anything that must outlive this review has been handed to the finding register.

**No authority without evidence. An approval with nothing found and nothing falsified is not a review; it is a reviewer who stopped looking.**
