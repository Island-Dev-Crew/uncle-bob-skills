---
name: strategy-shelf
description: The old-books curriculum for engineers who direct agents - the eight-entry 1968-1999 shelf behind Bob Martin's old-books prescription - the three he names, plus the five the research brief sources around them, each entry cut down to the handful of ideas that still carry weight when a model writes the code, plus what to leave on the page in a book written in 1979. Reach for it when someone asks where strategic judgment comes from now that agents hold the tactical seat, when assembling a reading path behind the general's job, or when someone says "what should I read to get better at architecture", "are the old software books still worth it", "how do I learn design if I never write the code myself". Differentiator - curriculum content only, every entry traceable to one research brief; the teaching engine, the drills, and the argument for why fundamentals persist all live elsewhere.
---

# Strategy Shelf: the old books, filtered

Bob's answer to how a novice learns the strategic half is not a course. It is a shelf: *"the works by Tom DeMarco or the works by Ed Yourdon… the Pragmatic Programmer… a lot of these older books, they're very good… you'll have to filter out some of the archaic stuff because a lot of these books were written in the 70s or the 80s… but that's when these lessons were learned"* (C27, quoted via [the ledger](../../01-CONCEPT-LEDGER.md)).

This island is that shelf written out, in eight entries. Three are the ones Bob names in C27: DeMarco, Yourdon, *The Pragmatic Programmer*. Five more come from the research brief, which sources them as the same canon. Each entry is cut to the ideas that still carry when the coding is delegated, plus the filter that gets you past the era's surface. Parnas, Brooks, Dijkstra, Weinberg and Royce are the brief's expansion of the shelf, not names Bob puts on it, and this island does not hand them his authority.

The problem it answers sits one concept earlier: the agents took the sergeant's job. *"tactical is the sergeant on the ground… strategic stuff is the general… agents are really good at tactical, really bad at strategic"* (C25, MP proposing the frame and RCM agreeing; the research brief notes the tactical/strategic vocabulary is commonly attributed to Ousterhout and does not verify that attribution, [seventies-canon](../../research/seventies-canon.md)). Grinding through the tactical loop is how strategy used to be learned. Delegate the loop and the learning has to arrive some other way. This is Bob's other way.

## The filter

The instruction in C27 is two-sided. The books are good **and** much of their surface is dead. Reading them without a filter wastes the good half defending the dead one.

1. **Read for the decision, not the notation.** Data-flow diagrams, structure charts, and the rest of the 1979 drawing kit are the era's surface. The criterion behind the drawing is the cargo.
2. **Assume the constraint has inverted.** These works were written when compute was scarce and every design decision had to be settled before code got cheap. A 2026 director is the mirror image: the code is nearly free, and the design errors compound ([seventies-canon](../../research/seventies-canon.md)).
3. **A retracted claim is data, not an embarrassment.** DeMarco publicly softened his own 1982 opening line in 2009 (brief). Watching an author update on evidence is part of the lesson.
4. **Check what the paper says against what the industry says it says.** At least one of these documents is famous for the opposite of its own argument (Royce, below).
5. **An entry earns its place from the brief, not from memory.** Every book here is sourced in [seventies-canon](../../research/seventies-canon.md). Recommending one that is not is an unbacked claim under the pack's first law ([CONTEXT.md](../../CONTEXT.md)).

Below, lines tagged **(brief)** are grounded in that research file. Lines tagged **(editorial)** are this island's judgment about what to skip. They are advisory, and they carry no more authority than that.

## The shelf

### Parnas — *On the Criteria To Be Used in Decomposing Systems into Modules* (CACM, 1972)
- **Load-bearing (brief)**: decompose a system by what each module *hides*, not by the processing steps it performs; the hidden design decision is the module's reason to exist.
- **Transfers (brief)**: a module whose internals are hidden is exactly the module an agent can regenerate without cascading breakage, and that boundary is the natural context-window boundary.
- **Filter (editorial)**: the worked example and its 1972 cost arithmetic are illustration. The criterion is the paper.

### Stevens, Myers & Constantine — *Structured Design* (IBM Systems Journal, 1974; the Yourdon & Constantine book, 1979)
- **Load-bearing (brief)**: coupling and cohesion as an objective vocabulary for judging a decomposition. It is the journal's most-reprinted paper, developed by Constantine from the mid-60s.
- **Transfers (brief)**: that vocabulary is how a director judges agent output without reading every line, and low coupling is the safety condition for running agents in parallel: one writer per module.
- **Filter (editorial)**: structure charts and transform/transaction analysis are notation. Yourdon's *Decline and Fall of the American Programmer* (1992) is on the shelf as a forecast to check against what actually happened. The brief records its thesis, not its verdict. Read it as a caution about confident industry prediction, not as design guidance.

### DeMarco — *Structured Analysis and System Specification* (1979) · *Controlling Software Projects* (1982) · *Peopleware*, with Lister (1987)
- **Load-bearing (brief)**: specification before construction; measurement with humility, from the 1982 opening *"You can't control what you can't measure"*, which he softened in 2009; and *Peopleware*'s thesis that *"The major problems of our work are not so much technological as sociological in nature"*.
- **Transfers (brief)**: the DFD-era spec-first instinct is today's spec-first agent workflow; the retraction models updating a doctrine when evidence turns; the sociological framing now has to cover human-plus-agent teams.
- **Filter (editorial)**: the data-dictionary mechanics and diagram conventions. Keep the discipline of writing the specification down before the machine starts.

### Brooks — *The Mythical Man-Month* (1975) · *No Silver Bullet* (1986/87)
- **Load-bearing (brief)**: Brooks's law; conceptual integrity, meaning one mind owns the design; the surgical team; and the essential/accidental split, with no single technique yielding a tenfold gain in a decade.
- **Transfers (brief)**: adding agents to a late project adds coordination surface, not progress. The surgical team — one surgeon, many force-multipliers — is the human-plus-agents org chart fifty years early. Agents shrink *accidental* complexity, and deciding what the system means stays human.
- **Filter (editorial)**: the OS/360 hardware anecdotes and the tooling chapters. The two named ideas survive the anecdotes intact.

### Dijkstra — *Go To Statement Considered Harmful* (CACM, 1968) · *The Humble Programmer* (EWD340, 1972 Turing lecture)
- **Load-bearing (brief)**: intellectual manageability as the limiting resource in software.
- **Transfers (brief)**: when generation is free, intellectual manageability *is* the review-gate criterion. Accept only code a human can still reason about.
- **Filter (editorial)**: the goto argument is settled. Read the 1968 note for the argument's shape rather than its target: a construct is condemned because it defeats the reader's model. Its famous title was the editor's retitling of EWD215 (brief), which is itself a small lesson in how a claim travels.

### Weinberg — *The Psychology of Computer Programming* (1971)
- **Load-bearing (brief)**: egoless programming, meaning review whose goal is that everyone finds defects, the author included.
- **Transfers (brief)**: review agent output the same way. Assume defects exist and go find them without attachment; "looks good" is not a review.
- **Filter (editorial)**: the keypunch-and-batch-terminal ethnography around the principle.

### Royce — *Managing the Development of Large Software Systems* (1970)
- **Load-bearing (brief)**: he drew the single-pass model and then wrote that it *"is risky and invites failure"*, demanding iteration and a do-it-twice pass.
- **Transfers (brief)**: the standing warning against process cargo-culting, and do-it-twice as the ancestor of evidence-gated pipelines over single-pass agent runs.
- **Filter (editorial)**: nothing here is skippable — it is short, and it is the highest-correction-per-page item I would hand a new director. The brief sources no page counts, so read that as judgment, not measurement. Read the paper, not the diagram that got extracted from it.

### Hunt & Thomas — *The Pragmatic Programmer* (1999)
- **Load-bearing (brief)**: DRY, orthogonality, tracer bullets.
- **Transfers (brief)**: agents duplicate readily, so DRY becomes a directive you enforce rather than a habit you have; a tracer bullet is the thin end-to-end slice you walk before fanning out.
- **Filter (editorial)**: the tooling chapters — editors, source control, shells — date fastest. Reach for the 20th-anniversary edition if you want them less dated.

## Where these ideas already have a seat in this pack

The shelf is reading, not enforcement. Several of its ideas have already been ported into a sibling island, and the reading lands better beside the island. Eleven of the fourteen below ship a script whose exit code decides. Three ship none, deliberately, and say so on their own pages; those three are marked inline, and a bullet that reads like a verdict there is a human's verdict, not a gate's.

- **Parnas's criterion, gated.** [`parnas-partition`](../parnas-partition/SKILL.md): every proposed module must name its secret or the split is rejected.
- **Parnas's boundary, priced.** [`interface-budget`](../interface-budget/SKILL.md) costs a deep module's interface in tokens. The design vocabulary and entry-point rules are the Forge's [`deep-modules`](../../COMPANION.md#deep-modules).
- **Cohesion, measured.** [`stability-order`](../stability-order/SKILL.md) and [`component-cohesion`](../component-cohesion/SKILL.md).
- **Coupling, budgeted.** [`coupling-budget`](../coupling-budget/SKILL.md) makes each cross-module edge a change adds spend against a declared budget.
- **Brooks, three ways.** [`conceptual-integrity-owner`](../conceptual-integrity-owner/SKILL.md) names the mind that owns the design (advisory, ships no gate by design); [`mythical-agent-month`](../mythical-agent-month/SKILL.md) prices the coordination surface of adding agents; and [`no-silver-bullet-triage`](../no-silver-bullet-triage/SKILL.md) routes work by the essential/accidental split (advisory, ships no gate by design).
- **Dijkstra's manageability, as an acceptance criterion.** [`manageability-review`](../manageability-review/SKILL.md) (advisory, ships no gate by design): restate the change's control flow in a fixed number of sentences from one reading, or a human bounces it.
- **DRY, measured.** [`leak-scan`](../leak-scan/SKILL.md) finds one design decision expressed twice.
- **The strategic seat, held near a band.** [`strategic-ledger`](../strategic-ledger/SKILL.md) keeps the tactical/strategic split honest with structural evidence (C25).
- **Weinberg's egoless review, as posture.** [`egoless-fleet`](../egoless-fleet/SKILL.md) owns the posture and the found-or-falsified record. The Forge's [`cross-family-review`](../../COMPANION.md#cross-family-review) makes it structural, owning who may review and when a verdict voids.
- **Royce's do-it-twice, staged.** [`do-it-twice`](../do-it-twice/SKILL.md) owns the pilot pass and the thin end-to-end slice that is also Hunt & Thomas's tracer bullet. The Forge's [`spec-pipeline`](../../COMPANION.md#spec-pipeline) owns spec-to-tickets-to-implement.
- **DeMarco's measurement humility.** [`measurement-humility`](../measurement-humility/SKILL.md) makes it a standing obligation on every enforced metric; this shelf does not implement it.

## If you only read four

Editorial, advisory, and ordered for someone directing agents this quarter rather than for a history course:

1. **Brooks, *No Silver Bullet*.** The essential/accidental sort is the question you will use most days.
2. **Parnas 1972.** The boundary rule, which is also your context-window rule.
3. **Royce 1970.** A short paper that inoculates you against cargo-cult process for the rest of your career.
4. **Hunt & Thomas.** The only one written in a world that looks anything like yours.

## Done when

Advisory, and checkable by a human without a script. This is what consuming the shelf looks like, not what adding to it does:

- [ ] For a diff actually in front of you, the review criterion you applied can be named back to one shelf idea and its author.
- [ ] Each of the four priority reads has one written transfer sentence, bound to a named gate in this pack.
- [ ] Every entry above resolved to a citation in [seventies-canon](../../research/seventies-canon.md) in a single pass.
- [ ] Nothing was added to the shelf from memory.

## Enforced vs advisory

- Every rule on this island is **advisory**. It ships **no script, by design**. What to read, what still carries, and what to skip is judgment, and a checker that confirmed a reading list had been consumed would be a gate with nothing behind it. [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) is explicit that a red/green pair proving a gate *can* fail is necessary and not sufficient; a gate wrapped around judgment fails that bar before it is written.
- The **enforced** checks touching this island are two, both exit-code gated: the pack validator (`scripts/validate-island.py`, F1–F11 on this file's own shape) and `scripts/verify-proofs.py`, which re-runs the two annotated `python3` commands in the block below and compares their exit codes. Neither says anything about whether the shelf improved anyone's judgment.
- Sourcing is **auditable but not enforced**: no tool checks it, and a reader can verify every entry above against [seventies-canon](../../research/seventies-canon.md) in a single pass. That is the standard an added entry has to meet.

```bash
$ python3 ../../scripts/validate-island.py ../strategy-shelf   # exit 0
$ python3 -c 'import re,sys,pathlib; t=pathlib.Path("../../COMPANION.md").read_text(encoding="utf-8-sig"); f=chr(96); t=re.sub("(?ms)^[ \t]{0,3}"+f*3+"+.*?(?:^[ \t]{0,3}"+f*3+r"+[ \t]*$|\Z)","",t); t=re.sub(r"(?ms)^[ \t]{0,3}~~~+.*?(?:^[ \t]{0,3}~~~+[ \t]*$|\Z)","",t); t=re.sub(r"(?s)<!--.*?(?:-->|\Z)","",t); need=["deep-modules","cross-family-review","spec-pipeline","skill-supply-chain-review"]; sys.exit(1 if [a for a in need if not re.search(r"(?m)^\x23{3}[ \t]+"+re.escape(a)+r"[ \t]*$", t)] else 0)'   # exit 0
$ ls ../../01-CONCEPT-LEDGER.md ../../research/seventies-canon.md ../../CONTEXT.md ../../COMPANION.md ../interface-budget/SKILL.md ../parnas-partition/SKILL.md ../stability-order/SKILL.md ../component-cohesion/SKILL.md ../coupling-budget/SKILL.md ../conceptual-integrity-owner/SKILL.md ../mythical-agent-month/SKILL.md ../no-silver-bullet-triage/SKILL.md ../manageability-review/SKILL.md ../leak-scan/SKILL.md ../strategic-ledger/SKILL.md ../egoless-fleet/SKILL.md ../do-it-twice/SKILL.md ../measurement-humility/SKILL.md ../thrash-watch/SKILL.md ../essence-pointer/SKILL.md ../known-dirty-fixture/SKILL.md ../human-subagent/SKILL.md ../abstraction-ladder/SKILL.md   # exit 0
```

All three run from this island's own directory. Between them they cover this file's shape, the four Forge anchors it points into, and every relative link it contains.

The middle one is a real check, not a formality. Swap any anchor name for one COMPANION.md does not carry and it exits `1`. It matches a literal `###` heading line rather than any three non-word characters, so a horizontal-rule idiom of the shape `--- deep-modules` does not satisfy it. That heading pattern is written `\x23{3}` because the pack's proof extractor truncates a documented command at the first `#`. The check also deletes fenced code blocks before searching, so an anchor name that survives only inside a fence does not satisfy it either. The strip covers backtick and tilde fences, three or more delimiters, up to three spaces of indent, and an opener with no closer, which is stripped to end of file. Both hardenings were reproduced against a forged COMPANION.md in both directions before being written here.

Exit `1` carries less meaning than "an anchor is absent". It is the one code for everything that is not a clean pass, and three of those states never reach the anchor search: COMPANION.md missing, COMPANION.md replaced by a directory, and COMPANION.md holding bytes that are not valid UTF-8. Each raises an uncaught exception, and Python leaves `1` behind on the way out. All five paths were run here against a scratch tree, and each returned the code named: missing `1`, directory `1`, undecodable `1`, all four anchors present `0`, one anchor removed `1`. So `0` means the four anchors resolved, and `1` means an anchor is absent *or* COMPANION.md could not be read as text. This fails **closed**, and it never turns a red into a green; a caller that reports only the first reading is reporting further than the command went.

What the check still does not do is resolve anchors the way GitHub does. A heading differing from the anchor in case or punctuation reads as absent, and nothing here says the anchor's section still means what this island cites it for. One trap worth inheriting: `validate-island.py .` is **not** the same command, because `Path(".").name` is the empty string and the folder-name check F4 goes red on it.

## Boundaries — who owns what

- **The teaching engine.** Lessons, learning records, session state across sittings: that engine is a Forge concern, not this island's. It lives in the Forge repository as `teach`. [COMPANION.md](../../COMPANION.md) records the twenty-two Forge boundaries this pack's earlier islands named, and `teach` is not among them, so it is named here rather than linked to an anchor. This island is curriculum **content** delivered through such an engine: it ships no lesson runner, no progress record, and no session state.
- **Drill design and scoring.** Running a junior *as an agent*, under the same task briefs and the same deterministic gates (C26), is [`human-subagent`](../human-subagent/SKILL.md)'s seat. The shelf supplies reading; it designs no drills and grades nobody.
- **Why fundamentals persist at all.** The binary → assembly → compiler → models ladder, and the closing law about the rules you throw away (C28), is [`abstraction-ladder`](../abstraction-ladder/SKILL.md)'s argument. This island assumes it and does not re-make it. (RCM attributes *"software is the most complicated thing that humans have ever attempted"* to Dijkstra; the ledger flags that attribution for verification, C28.)
- **Recognising the struggle.** The diagnostic half of C27, seeing an agent thrash and knowing what it means, is [`thrash-watch`](../thrash-watch/SKILL.md)'s. The shelf is what Bob prescribes for the novice who cannot yet recognise it.
- **Studying an artifact instead of adopting it.** [`essence-pointer`](../essence-pointer/SKILL.md) covers building your own from an exemplar, and vetting a third-party artifact before use is the Forge's [`skill-supply-chain-review`](../../COMPANION.md#skill-supply-chain-review). A book is neither: it is read, not installed.

**No authority without evidence. The archaic part is the surface and the lesson is the load: read for the decision, skip the notation, and never shelve a book the brief cannot source.**
