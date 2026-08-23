---
name: instruction-density-cap
description: A countable ceiling on how many directives one prompt may carry at once - instruction-following degrades with DENSITY as well as position, so this island defines what counts as a directive, caps the count per model class, and fails the prompt past it. Reach for it when a rules file has grown to dozens of simultaneous instructions, when an agent obeys some rules and silently skips others, or on "how many rules can I give it", "count the directives in my CLAUDE.md", "my agent ignores half its instructions". Differentiator - density only; the head-of-context position budget is priority-zone's seat and prompt-versus-gate sorting is steering-audit's.
---

# Instruction Density Cap: how many rules at once

Two different things degrade a rules file, and this pack splits them across two islands.
**Position** — where a rule sits in the context, the primacy/recency U-curve and the token
budget at the head — is [`priority-zone`](../priority-zone/SKILL.md)'s seat, and it stays
there. **Density** — how many directives are live *simultaneously*, regardless of where any
one of them sits — is this island. Both axes come out of the same body of findings; a prompt
can pass a position budget and still carry more instructions than the model tracks, and a
short prompt of forty terse rules is a density problem with no position problem at all.

The doctrine underneath is C3: steering decays, so long rule-documents get treated *"in the
Pirates of the Caribbean sense. They're more like guidelines"* — obeyed probabilistically.
C4 is the exit: a deterministic tool in a loop *"you must change the code until this tool
says that it's okay"* holds at rule 1 and rule 80 alike. This island makes the density half
of that argument countable, so "too many rules" stops being a feeling.

## The evidence

From [`research/lost-in-the-middle.md`](../../research/lost-in-the-middle.md), where the
citations live so the numbers cannot drift here:

- **IFScale** (Jaroslawicz et al., 2025) drives up to **500 simultaneous instructions**. Even
  frontier models fall to **~68%** at that density. Decay is **graded**, not a cliff.
- **Reasoning models hold to roughly 100-250 instructions.** That band is the only per-model
  number the brief supports; nothing in it assigns a cap to *your* model.
- **Primacy is universal** — earlier instructions are favoured. Order is not cosmetic.
- **Errors shift toward omission.** Past the density the model tracks, a rule is not
  mangled; it is silently skipped, which is exactly the failure that reads as "it ignored me".

The folk figure of a small handful of rules before comprehension collapses is marked
**UNVERIFIED** in that brief, and this island does not carry it.

## What counts as a directive

The counter is a deterministic proxy, not a semantic judge. One unit per line, at most:

- **D-a** — a list item outside a fenced code block at any indent: a bullet marker (`-`,
  `*`, `+`, and the non-markdown glyphs `•‣⁃▪▫○●◦·–—→➤»` that rules files use anyway) or an
  ordinal (`1.`, `1)`, `R1.`, `a)`, and a short word label in front of one — `Rule 1.`,
  `Step 3)`), followed by whitespace. Steering files spend their rules
  as list items; the sibling [`steering-audit`](../steering-audit/SKILL.md) extracts the same
  shape for the same reason.
- **D-b** — a markdown table row outside a fence, minus the single `|---|:--:|` delimiter
  row that immediately follows a table's header. A rules table spends one row per rule, and a
  rules-as-table prompt is a real format. The delimiter drop is **positional**, as markdown
  requires: a body row whose cells happen to hold only dashes or colons (`| - | -- |`) is a
  row and is counted, so a rules table cannot be emptied by what its cells contain.
- **D-c** — any other line outside a fence carrying a whole-word directive modal: *must,
  shall, should, never, always, required, mandatory, forbidden, prohibited, avoid, ensure,
  "do not", "don't"* (straight or curly apostrophe), matched case-insensitively.

A blockquote prefix is stripped before classifying, so quoting a rule does not hide it. Text
is normalised **NFKC** and zero-width/bidi characters are removed first, so a marker followed
by an invisible space — NBSP, figure space, narrow NBSP, ideographic space — or split by a
zero-width space counts exactly like its ASCII twin.
A file holding a **NUL** is refused with exit **2**, never counted. UTF-16LE/BE and UTF-32
*without* a BOM are valid UTF-8 when the text is ASCII — a Windows "Codepage 1200 without
signature" Save-As, `iconv -t UTF-16LE`, or `new UnicodeEncoding(false,false)` all emit
exactly that — and every marker and modal in one arrives split by `U+0000`, so it would
otherwise count **0** in total silence. The NUL closes that class by definition rather than by
enumerating encodings, as NFKC + Zs-folding does for invisible spaces. (A UTF-16 file *with* a
BOM was already a decode failure, also exit 2.)

Fenced code blocks are excluded so example commands do not inflate the count — a deliberate
hole, evidenced below rather than glossed. An **unterminated** fence is not honoured: its
body counts as ordinary text, so the tail of a file after an unclosed fence is still counted.

## The cap, and what to do when you blow it

`--profile reasoning` = 150, `--profile standard` = 75, `--cap N` overrides both. The 150
sits inside IFScale's 100-250 band; the 75 is a conservative extrapolation for non-reasoning
classes that no source states. **Both defaults are `advisory` — pick your own number.** The
gate at whatever number you choose is mechanical.

Over the cap, three exits, in this order:

1. **Split the task.** Two prompts of forty rules beat one of eighty, because density is
   per-prompt and a fresh context resets it. This is the cheapest move and usually the right one.
2. **Gate the checkable rules.** Anything with a mechanical test leaves the prompt for a
   deterministic loop (C4) and stops spending density forever. *Which* rules those are is
   [`steering-audit`](../steering-audit/SKILL.md)'s classification, not this island's — this
   island only tells you how many have to go.
3. **Cut.** What survives neither move was sediment.

And because primacy is universal: **order the survivors so the rules you would least
tolerate being skipped come first.** That ordering is advisory — the counter does not judge it.

## Run the gate — verify, fix, re-verify

```bash
python3 <this-island>/scripts/density-cap.py CLAUDE.md                       # profile reasoning (150)
python3 <this-island>/scripts/density-cap.py AGENTS.md --profile standard    # 75
python3 <this-island>/scripts/density-cap.py CLAUDE.md --cap 40 --show       # your number, listed
```

Exit codes, the complete set this script emits: **0** within cap (also the code for `--help`
on a live stdout — `--help` into a dead pipe exits 2 like any unflushable stream), **1** over
cap — the verdict, **2** usage error, unreadable file, undecodable file, a file containing a
NUL, an output stream that could not be flushed, or any internal failure. Usage errors,
unreadable, undecodable and NUL-bearing files and internal failures exit 2, not the verdict's
1 — the probes below run each one. Loop until 0.

### Red/green proof, recomputable

The pair ritual is [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s; these are its
outputs, run from this island's directory. Recompute them instead of trusting these lines.

```bash
python3 scripts/density-cap.py scripts/fixtures/dense-prompt.md  --cap 12   # exit 1
python3 scripts/density-cap.py scripts/fixtures/capped-prompt.md --cap 12   # exit 0
```

RED: `FAIL D1 33 directives exceeds cap 12` — one grown rules file, 33 units.
GREEN: `OK D1 4 directives within cap 12` — the same repo's rules after the checkables became
gates. The red fails for density, not for malformed input; the two fixtures are the same
repo's prompt before and after.

### Hardening probes, run and captured

Every input below was executed. All are things ordinary editors, filesystems and CI produce,
except the zero-width-space markers inside `glyph-bullet-prompt.md` — deliberate, and closed
anyway.

```bash
python3 scripts/density-cap.py scripts/fixtures/dense-prompt-bom-crlf.md --cap 12    # exit 1
python3 scripts/density-cap.py scripts/fixtures/unterminated-fence.md    --cap 5     # exit 1
python3 scripts/density-cap.py scripts/fixtures/latin1-prompt.md         --cap 12    # exit 2
python3 scripts/density-cap.py scripts/fixtures/utf16le-nobom.md         --cap 12    # exit 2
python3 scripts/density-cap.py scripts/fixtures/utf16be-nobom.md         --cap 12    # exit 2
python3 scripts/density-cap.py scripts/fixtures                          --cap 12    # exit 2
python3 scripts/density-cap.py scripts/fixtures/nope.md                  --cap 12    # exit 2
python3 scripts/density-cap.py scripts/fixtures/capped-prompt.md --profile turbo     # exit 2
python3 scripts/density-cap.py scripts/fixtures/capped-prompt.md --cap 0             # exit 2
python3 scripts/density-cap.py scripts/fixtures/capped-prompt.md --profile ReAsOnInG # exit 0
python3 scripts/density-cap.py scripts/fixtures/table-prompt.md          --cap 3     # exit 1
python3 scripts/density-cap.py scripts/fixtures/invisible-space-marker.md --cap 12   # exit 1
python3 scripts/density-cap.py scripts/fixtures/glyph-bullet-prompt.md   --cap 12    # exit 1
python3 scripts/density-cap.py scripts/fixtures/ruleN.md                 --cap 12    # exit 1
python3 scripts/density-cap.py scripts/fixtures/dashy-table.md           --cap 12    # exit 1
```

`dense-prompt-bom-crlf.md` is `dense-prompt.md` with a UTF-8 BOM, CRLF endings and an NFD
accent — macOS routine — and it counts **33**, identical to the LF/NFC original, so none of
those variants buys leniency. `unterminated-fence.md` parks twelve rules after an unclosed
` ``` `; a naive fence tracker would swallow them and consent, and this one counts them and
refuses. A Latin-1 file, a directory, a missing path, an unknown profile and a zero cap all
exit **2**, not **1**. `table-prompt.md` keeps its rules in a table instead of a list, and
D-b counts the rows.

`invisible-space-marker.md` is the one that used to produce a **false green**: forty rules
whose markers carry NBSP, figure space, narrow NBSP or ideographic space instead of `U+0020`
(line 7 begins `2d c2 a0`, where its ASCII twin begins `2d 20`). NFC left those separators
alone, so the file counted **0** and consented at a cap of 12; under NFKC it counts **40**,
identical to the twin, and refuses. Pasting from Word, Google Docs, Notion or a web page emits
them routinely, no editor or diff renders them, and `CLAUDE.md` is fed to a model raw so no
downstream renderer catches them either. `glyph-bullet-prompt.md` is the same shape one step
out: ten `•`, ten `–`, ten hyphens split by a zero-width space, and ten `R1.`-style ordinals —
forty units now, zero before.

`utf16le-nobom.md` / `utf16be-nobom.md` are those same forty rules in UTF-16 with **no BOM**.
Both are valid UTF-8 and both used to print `OK D1 0 directives within cap 12` at rc **0** —
the worst false-green shape here, total silence rather than an under-count; the NUL refusal
makes both exit **2**. `ruleN.md` is forty modal-free rules labelled `Rule 1.`–`Rule 40.`: the
narrow ordinal branch took `R1.` but not `Rule 1.`, so it counted **0** and consented, and now
counts **40**. `dashy-table.md` is a header, a real delimiter, then forty rows shaped
`| - | -- |`, every one of which matched the delimiter pattern and was dropped wherever it sat
— it counted **1**, and the positional rule counts **41**. A dead stdout on a *passing* run
exits 2 rather than 0:

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run([sys.executable,"scripts/density-cap.py","scripts/fixtures/capped-prompt.md","--cap","12"],stdout=w,stderr=subprocess.DEVNULL).returncode)'
```

### The limits this island did not close

All three are captured as runs, not described. Each is a real under-count: a reviewer reading
these files sees rules the counter does not.

```bash
python3 scripts/density-cap.py scripts/fixtures/fence-blind-spot.md      --cap 5   # exit 0
python3 scripts/density-cap.py scripts/fixtures/imperative-blind-spot.md --cap 5   # exit 0
python3 scripts/density-cap.py scripts/fixtures/prose-fence.md           --cap 12  # exit 0
python3 scripts/density-cap.py scripts/fixtures/marker-shaped-blind-spot.md --cap 5   # exit 1
```

**Fenced code blocks are excluded**, so a rules list moved *inside* a fence is invisible.
[`fence-blind-spot.md`](scripts/fixtures/fence-blind-spot.md) is that hole: twenty directives
inside a fence, four outside, consenting at a cap of five. Closing it would count every
example command in every prompt and make the gate a nuisance.

**And a fence need not be deliberate.** Any line that begins, after up to three spaces or
tabs, with three or more backticks or tildes opens one — so *prose about fencing* silences
every rule after it up to the next closer, with nobody having moved anything.
[`prose-fence.md`](scripts/fixtures/prose-fence.md) is that shape: a line reading
`` ```bash is how you open a fence ``, forty rules under it, then an ordinary closing fence.
It counts **0** and consents at a cap of 12. A `CLAUDE.md` documenting markdown or shell
fencing produces it without anyone trying.

**Modal-free imperative prose counts near zero.** A rule written as a bare imperative
sentence — no list marker, no table pipe, no modal verb — is not a D-a, D-b or D-c unit.
[`imperative-blind-spot.md`](scripts/fixtures/imperative-blind-spot.md) is forty rules of
which three wear a marker: it counts **3** and consents at a cap of five. Closing it needs a
semantic judge, and this counter is a deterministic proxy on purpose. Hand-count a rules file
written in prose; the gate will not do it for you.

## Boundaries

- **Position and the head-of-context token budget** — how much may stand at the head of the
  context and where hard directives may sit — belong to [`priority-zone`](../priority-zone/SKILL.md).
  Same paper set, different axis. This island counts directives wherever they are; it says
  nothing about where they sit or how big the file is.
- **Sorting a rule into prompt-worthy versus gate-worthy** is [`steering-audit`](../steering-audit/SKILL.md)'s
  seat. This island reports the overage; that island decides which rules migrate.
- **Document-level writing levers** — context pointers, the two loads, information hierarchy,
  pruning — stay with [`writing-for-agents`](../../COMPANION.md#writing-for-agents). How to
  word the survivors is that island's craft, not restated here.

## Enforced vs advisory

- `enforced` — the count and the cap in [`scripts/density-cap.py`](scripts/density-cap.py):
  D-a/D-b counting is deterministic (same file, same number), and the script exits 1 when the
  count exceeds the cap **and its output reaches a live stream** — an unflushable stream is a
  2, per the exit-code table above, so the verdict never rides on a dead pipe. Error paths
  exit 2, proven by the probes above.
- `enforced` — this island's own shape, gated by `../../scripts/validate-island.py`.
- `advisory` — the cap numbers (150 / 75), the counting rule's *fidelity*, ordering survivors
  by importance, and wiring the script into a hook or CI. Fidelity cuts both ways and the
  under-counts matter more: it **over**-counts a list of file paths, a table header, an
  em-dash aside at the start of a line, and a word-labelled cross-reference such as
  "Section 3." or "Figure 2)", and counts a compound sentence carrying three obligations as
  one; it **under**-counts a rule written as a bare imperative with no modal and no list
  marker — that rule is not counted at all — any rule parked inside a fence, and any rule
  after a prose line that begins with three backticks or tildes, which opens a fence whether
  or not one was meant, and a rule whose marker falls outside the classes D-a recognises. Those four are captured as fixtures above. Until a hook
  runs it, running it is on you. What the counter says is mechanical; what the number should
  be is a judgment this island refuses to fake.

## Done when

- [ ] `density-cap.py` exits 0 on the prompt at the cap you chose, and the cap is written down.
- [ ] Every unit removed to get there was split into another prompt, migrated to a named gate,
      or cut — none reworded in place to dodge D-a/D-b.
- [ ] The survivors are ordered with the least-skippable first.
- [ ] Any rules parked inside a code fence — including one opened by accident by a prose line
      starting with three backticks — or written as modal-free imperative prose, were counted
      by a human, since the gate will not.

**Density is a budget with a number on it - past the count your model tracks, a rule is not broken, it is silently skipped (C3).**
