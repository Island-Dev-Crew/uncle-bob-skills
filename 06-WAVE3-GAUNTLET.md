# Wave 3 — fusion and gauntlet record

**Built:** 2026-08-21/23 · **Islands:** 15 (pack total **50 — the roster is complete**) · **Status:** 600/600 mechanical checks green; every realistic-input false green found is closed; remaining limits are disclosed in the islands that carry them.

Wave 3 is the strategy, economics and education layer — the conversation's answers to *who holds the design*, *how many agents is too many*, and *how does anyone learn this now*.

## What changed in the method

Wave 2 needed four adversarial rounds largely because the tiering standard only arrived at round three. So Wave 3 gave builders the whole standard **upfront**: the tier A/B/C criteria, the six bypass classes found empirically across both earlier waves, and the verbatim exit-code seal that closes the 120 leak.

It helped, but less than hoped. Two islands passed round one; the rest still failed a blind critic that forged inputs. Front-loading the standard raised the floor — islands arrived with fixtures, honest advisory labels and sealed exit codes — without making the critics redundant. That is roughly the right result: a bar you can clear by being told about it is not a bar.

## The honest-script result

Wave 2 shipped a script on all fifteen islands, and some of those were thin gates wrapped around judgment. Wave 3 named the expectation per island, and the split came out where it should:

- **Nine shipped a gate** with fixtures — `instruction-density-cap`, `parnas-partition`, `coupling-budget`, `mythical-agent-month`, `egoless-fleet`, `do-it-twice`, `measurement-humility`, `plan-decay-detector`, `change-cost-probe`.
- **Six shipped none and said so** — `conceptual-integrity-owner`, `no-silver-bullet-triage`, `manageability-review`, `human-subagent`, `strategy-shelf`, `abstraction-ladder`. Who holds a design, whether complexity is essential, whether a human can restate a change, how to drill a junior: none of that is arithmetic, and a gate around it would be theatre.

An island that admits it is advisory is the correct outcome under this pack's second law, not a weaker one.

## The four false greens, and what closed them

Every one was reachable by input a real editor, filesystem, or CI produces — tier A by definition.

- **`instruction-density-cap` counted zero directives in a plainly numbered rules file.** Its marker test was a fixed 16-character enumeration, so a bolded `**1.**`, an emoji bullet, and `■` U+25A0 were all invisible — while `■`'s level-1 and level-2 siblings were on the list, meaning a three-level list pasted from Google Docs counted its top two levels and silently dropped the third. A twelve-rule file consented against a cap of five. The enumeration is now a **Unicode property test** (Pd, Po, Sm, Sk, So), with a leading emphasis run stripped so `**1.**` reaches the ordinal branch. All twenty existing documented counts were unchanged by the fix.
- **`measurement-humility` was defeated by one punctuation mark.** `bare()` peeled a hand-listed set, so `none?` and `-none-` read as substance and the row passed REVIEWED — 192 leaking spellings in total, in exactly the vocabulary the script parses, since `none?` is how an unsure author actually fills a corruption clause. Peeling is now by Unicode category, with the unpeeled spelling kept as a candidate so a bare `?` or `--` still registers as the evasion it is, plus a letter-or-digit floor so a threshold of `###` cannot be green.
- **`plan-decay-detector` aimed a whole plan at the wrong tree in silence.** `--root` defaulted to `.`, so an all-`absent` plan run from an unrelated directory reported `PLAN HOLDS` and exited 0 while the real tree already held the files. A wrong working directory is among the most ordinary CI conditions there is. `--root` is now required, so an omitted one is a usage exit — which is what the island's own exit-code paragraph had promised all along.
- **`strategy-shelf` was fully defeated by an HTML comment.** Its anchor probe stripped backtick and tilde fences but not `<!-- -->`, so commenting out all four Forge anchors still exited 0 — while GitHub emits no anchor for a commented heading, meaning every one of its links would be dead with its own proof block reporting green. Commenting a section out instead of deleting it is ordinary Markdown editing, and the pack's own bypass class 4 names "text inside a comment" explicitly.

## Verification

```bash
python3 scripts/validate-island.py skills/*/     # 600 checks, 50 islands
python3 scripts/verify-proofs.py                 # re-runs every documented command
```

`verify-proofs.py` reports five mismatches across the pack, all traced to its own documented limits — a heredoc, a block that builds fixtures with `printf` into a temp dir, and a block that `cd`s first. Each was confirmed by running the block whole. A mismatch there is a prompt to go look, never a verdict.

One note worth keeping: `__pycache__` appeared under two islands during this wave and was **not** produced by anything the pack ships. It came from gauntlet agents importing scripts to probe them; forty-five documented commands regenerate none of it.

## Honest state

- **Enforced:** 600 mechanical checks across 50 islands; every island shipping a gate ships a red/green fixture pair; every island claiming a closed exit-code set emits only the codes it names.
- **Disclosed limits:** `instruction-density-cap` under-counts a rule wearing a marker outside the classes it recognises and one written as bare imperative prose; `stability-order` cannot see a pure dependency cycle; `coverage-gaming-audit` cannot see a `conftest.py`-hooked suite; `comment-as-spec` cannot resolve an imported base class. Each is on the page with its command beside it.
- **The roster is complete.** All 50 islands specified in [02-ROSTER-50.md](02-ROSTER-50.md) are built. What remains is the hardening pass — cross-model verification, supply-chain and tamper-evidence work — which is reserved for 2.0 rather than folded in here.

**No authority without evidence. A bar you can clear by being told about it is not a bar.**
