# Wave 2 — fusion and gauntlet record

**Built:** 2026-08-20/21 · **Islands:** 15 (pack total 35) · **Status:** all 35 mechanically green (420/420 checks); every realistic-input false green found across four adversarial rounds is closed; remaining limits are disclosed in the islands that carry them.

Wave 2 is the canon-mechanics layer — where the conversation's claims meet the books behind them. It went through a harder gauntlet than Wave 1, and it needed one.

## What changed in the method

Wave 1 shipped twelve gates and only one red/green proof, which cost an extra round to close. So Wave 2 required a fixture pair in the same pass as the script. More importantly, the critics were told to **forge inputs** rather than re-run the author's fixtures — because Wave 1 ended with three gates that separated their own fixtures perfectly and were still walked past by inputs those fixtures never tried.

That change produced a striking first result: **all 15 islands failed round 1**, against 13-of-20 passing first time in Wave 1. Nothing had gotten worse; the test had gotten honest.

## The four rounds

| round | what it did | result |
|---|---|---|
| 1 — build + blind critic | author, then a critic that never saw the brief | 0/15 passed |
| 2 — harden + verify | close every named bypass, verifier re-forges each | named bypasses closed; **39 new findings** |
| 3 — converge (tiered) | fix realistic-input holes, make every sentence true | 3 accepted; tier-A down to 2 |
| 4 — final | close the last blockers | 6/8 accepted; one new tier-A surfaced |

Rounds 2 and 3 are the interesting part. Each one genuinely closed what it was handed — verifiers re-forged the named inputs and confirmed — and each then found subtler holes. Round 2's findings were BOM smuggling, NFC/NFD spellings, broken pipes; round 3's were argparse edge cases and idiom swaps. Left alone this never terminates.

## The convergence criteria — how the loop was stopped

An adversarial loop that never ends is its own failure, and this pack has a doctrine for it: [`margin-ledger`](../skills/margin-ledger/SKILL.md) says a gate may cost you until, never past, the point of value. So round 3 replaced "find nothing" with a tiered standard:

- **Tier A — must fix in code.** A false green reachable by input a real user, editor, filesystem, or CI would plausibly produce: a UTF-8 BOM, CRLF, NFC vs NFD (macOS hands you NFD routinely), a case-variant path, an ordinary idiom swap in the scanned language. A gate that misses these is broken for real users.
- **Tier B — fix if cheap, else disclose as a fixture.** A hole reachable only by deliberately hostile input. The precedent is [`stability-order`](../skills/stability-order/SKILL.md), which passed by shipping `cycle-blind-spot.json`: a captured exit-0 run documenting a blind spot it chose not to close. An evidenced boundary beats a silent one.
- **Tier C — make the sentence true.** Not a false green at all: an IO path exiting the wrong code, a docstring naming a flag that does not exist, an absolute word ("every", "never", "refuses") broader than the code. The code may stay; the claim may not. Narrowing it is a legitimate fix, and this tier always terminates.

Tier C is what makes the loop finite, and it is also where this pack's first law bites hardest: a sentence the implementation cannot back is laundering, whether or not any input exploits it.

## The six bypass classes

Every bypass found across both waves falls into one of six shapes. They are now written into [`known-dirty-fixture`](../skills/known-dirty-fixture/SKILL.md) under *the pair is necessary, not sufficient* — the island's own thesis, corrected by what Wave 2 proved: a red/green pair shows a gate **can** fail, never that it cannot be **fooled**, because a fixture only tries the input its author already imagined.

1. **An error path wearing a verdict's exit code** — a crash, unreadable file, decode error, closed stdin, or overflow exiting the code that means "real violation", so a caller records a verdict the gate never computed.
2. **Key normalization** — the same entity under a different spelling missing its join and falling to the lenient branch.
3. **Silent row drops** — a `#` comment rule applied to a field whose legitimate values can begin with `#`.
4. **Unanchored matching** — a marker satisfied by a superstring, by text inside an `echo`, or by a one-token idiom swap.
5. **Prose broader than the check.**
6. **Numeric edges** — a rounded message disagreeing with the integer basis, an unbounded int conversion, `NaN` slipping past a `<= 0` guard and disabling a rule.

## What the critics actually caught

- **A binding gate that did not bind.** `qa-bind-check.sh` (Wave 1, re-verified here) anchored its STORY check but not the others, so a script whose only "headers" sat inside an `echo` passed — as did one bound to `<doc>.OLD-REVISION`, and one whose hash was the real hash plus a suffix.
- **The most ordinary refactor in Python turning a verdict green.** `comment-as-spec` walked only a class body, never its bases — so moving methods into a base class hid the entire inherited surface, undocumented members and leaking comments alike. Now resolved transitively through same-module bases, with two fixtures pinning it.
- **A scan reporting clean over tests it never read.** `coverage-gaming-audit` matched test filenames with an ASCII-only pattern and refused to descend into symlinked directories — while pytest collects and runs both. `test_café.py` and a symlinked suite were invisible. Fixed, with a real-path visited set so a symlink cycle terminates instead of spinning.
- **Regex injection in a story filter.** `spec-mulch` interpolated the id raw into a pattern, so `story-1.2` silently matched a `story-142` spec — the exact false positive its own comment promised to prevent.
- **One bug wearing five hats.** Five islands' exit-code tables denied a fourth code their scripts could emit: CPython replaces your exit status with **120** when its shutdown flush hits a dead pipe, and the leak arrives either through `except SystemExit: raise` re-raising past the seal (argparse's usage-exit and `--help` skip it) or through no seal at all. Every island claiming a closed set now emits 2 — verified by probing each one with a bad flag against a dead stderr pipe and `--help` against a dead stdout pipe.

## Verification

```bash
python3 scripts/validate-island.py skills/*/     # 420 checks, 35 islands
python3 scripts/verify-proofs.py                 # re-runs every documented command
```

[`verify-proofs.py`](../scripts/verify-proofs.py) is new in this wave and exists because of a mistake made repeatedly during it: **the verification method was the broken thing more often than the artifact.** Reading `$?` after a pipe gives the pipe's status. Reading it after `$(basename f)` gives the substitution's. `timeout` is not on macOS. A `grep -P` search returned zero on a pattern that was demonstrably present. Each of those produced a confident, wrong report about a working gate. The tool re-runs each island's own documented commands and compares exit codes, and its own limits — heredocs, `printf` setup, `cd` — are stated in its docstring rather than left to be discovered.

## Honest state

- **Enforced:** 420 mechanical checks across 35 islands; every gate script ships a red/green fixture pair; every island claiming a closed exit-code set emits only the codes it names.
- **Disclosed limits:** `stability-order` cannot see a pure dependency cycle (fixture-proven); `coverage-gaming-audit` cannot see a suite reached only through a `conftest.py` hook, and its fold has a size cap that lets one tautology class pass (fixture-proven); `comment-as-spec` cannot resolve an imported or dotted base class. Each is on the page with its command beside it.
- **Non-blocking, noted by acceptance:** `gate-toolchain` carries three claim-precision items its acceptance seat judged non-blocking.
- **Not done:** islands 36–50 remain specified in [02-ROSTER-50.md](02-ROSTER-50.md) and unbuilt.

**No authority without evidence. A gate that has not been watched failing is a claim wearing a uniform — and a fixture only tries the input its author imagined.**
