---
name: margin-ledger
description: Continuous productivity accounting for a gate stack. Keeps a per-story ledger of agent-with-gates wall clock against an honest human baseline, defends Bob's observed 2-4x margin, and cuts any gate that would push the margin below 1x. Reach for it when stacking or tuning quality gates over agent work, when a gated pipeline starts feeling slower than doing the work yourself, or on "margin ledger", "are the gates worth it", "productivity margin", "have we lost the game". Differentiator - it prices gates already in flight; whether to build at all is job-to-be-done's triage, and per-step model cost picks are model-routing's.
---

# Margin Ledger: the accounting unit is the margin

Every gate trades speed for quality. Each one is a loop the agent must satisfy before it may proceed (C4). The trade is bounded: *"eventually you will slow the agents down to the point where they're slower than humans. And at that point you've lost the game… as long as you can keep the margin of productivity higher than a human, you're still ahead of the game"* (C5). This island keeps the running ledger of that trade, story by story, so the bound stays a measured number instead of a feeling. Quotes come only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## Where this island sits

State these boundaries before opening a ledger. Each one names the neighbor that owns the adjacent concern.

- PRE-build triage belongs to [`job-to-be-done`](../../COMPANION.md#job-to-be-done). Whether this thing should be built or automated at all is that island's call. The ledger opens only after the build verdict; a story that never deserved building has no margin worth defending.
- Per-step model and tool cost picks belong to [`model-routing`](../../COMPANION.md#model-routing). When the ledger shows a gate bleeding time, cheapen that seat's model or swap inference for a deterministic tool over there. This island only names which gate is bleeding and by how much.
- This island owns the CONTINUOUS in-flight ledger only: per-story measurement while the gate stack runs. The gates themselves live on their own islands, the relay's seats on `seat-relay` and the CRAP ceiling on `crap-gate`. This island prices them; it never defines them.

## The unit and the band

**margin = honest human baseline wall clock ÷ agent-with-gates wall clock, per story.**

- **Band 2–4x.** Bob's observed range with the full gate stack: *"a factor of two or three or four"* (C5). A target, not a law of nature.
- **Floor 1x.** Below it the gated agent is slower than the human, and *"you've lost the game"* (C5).

The relay math is the worked example (C5). One ungated agent one-shots a story in ~5 minutes at questionable quality. The full five-seat relay (specifier → coder → cleaner → hardener → QA, C9) takes ~1 hour. A human takes ~half a day. Verdict: *"factor of four, factor of five improvement… and very high quality"* (C5). So the agent's raw 12x speed gives most of itself back to the gates and still books 4–5x. That is the game working as designed. The ledger exists to notice when it stops.

## Keeping the ledger

1. **Baseline honestly** (advisory). The human baseline is what a competent human would actually take end-to-end for this story: an estimate from someone who has done such work, or historical actuals. Record the source next to the number. A baseline inflated to flatter the margin launders `unverified` into `verified` ([repo law](../../CONTEXT.md)).
2. **Clock the gated run** (advisory). Wall clock starts when the story enters the gate stack and stops when the last gate consents. Append one TSV row per story: `story <TAB> gated_minutes <TAB> human_minutes`. Continuous means the row is written as each story ships, in flight. A one-time benchmark goes stale the moment the stack changes.
3. **Compute** (enforced arithmetic). [`scripts/margin-ledger.py`](scripts/margin-ledger.py) prints per-story margin with a band verdict, then the aggregate. It exits 1 on any margin below the floor, exits 2 fail-closed on empty or malformed input, and exits 3 when the ledger cannot be read or the invocation is wrong. Captured run:

```bash
$ printf 'checkout-flow\t60\t240\nlogin-audit\t300\t240\n' | python3 scripts/margin-ledger.py
IN-BAND    4.00x  gated=60m  human=240m  checkout-flow
LOST       0.80x  gated=300m  human=240m  login-audit
aggregate 1.33x THIN over 2 stories, floor 1
$ echo $?   # → 1
```

4. **Act on the band** (advisory):

| Band | Reading | Move |
|---|---|---|
| WIDE (>4x) | headroom | a gate you have been wanting can afford its cost |
| IN-BAND (2–4x) | Bob's observed range (C5) | the stack is earning its keep; hold |
| THIN (1–2x) | ahead but eroding | find the most expensive gate; cheapen it via model-routing or cut it |
| LOST (<1x) | *"you've lost the game"* (C5) | cut the most expensive gate, re-measure on the next story, repeat until the floor clears |

## Adding a gate: project before you pay

Every candidate gate gets a margin projection before it enters the stack: `projected margin = human_baseline ÷ (current gated minutes + the gate's added minutes)`. When the projection lands below 1x, cut the gate. The quality it would buy costs the whole game (C5). Record the projection next to the gate so the next ledger review can check it against actuals. This rule is advisory: the projection is an estimate, and no hook blocks an unprojected gate today.

## Enforced vs advisory (v0, stated honestly)

- **Enforced today**: the arithmetic and the floor verdict. [`scripts/margin-ledger.py`](scripts/margin-ledger.py) computes margins exactly, exits 1 on a floor breach, exits 2 fail-closed on an empty or malformed ledger, and exits 3 on an unreadable ledger or bad invocation. Codes 2 and 3 are deliberately distinct. While both were 2, running from the wrong directory produced a path error that read exactly like a legitimate fail-closed verdict. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
Red/green proof, run rather than asserted. The gate ships with the fixture pair that proves it can fail: [`scripts/fixtures/dirty-lost-margin.tsv`](scripts/fixtures/dirty-lost-margin.tsv) (one story at 0.80x, below the floor, hidden behind a 1.33x aggregate) and [`scripts/fixtures/clean-in-band.tsv`](scripts/fixtures/clean-in-band.tsv) (every story in band). Recompute the acceptance:

```bash
# Run from this island's directory (unclebob/skills/margin-ledger). Elsewhere the
# relative paths fail and the script exits 3 — an IO code, never confusable with
# the exit-2 fail-closed verdict.
python3 scripts/margin-ledger.py scripts/fixtures/dirty-lost-margin.tsv   # → exit 1 (RED, LOST 0.80x login-audit)
python3 scripts/margin-ledger.py scripts/fixtures/clean-in-band.tsv       # → exit 0 (GREEN, aggregate 3.20x IN-BAND)
```

Both exit codes above were observed on the shipped fixtures. The pair also passes the pack ritual ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)) in one run: `skills/known-dirty-fixture/scripts/prove-gate.sh skills/margin-ledger/scripts/fixtures/dirty-lost-margin.tsv skills/margin-ledger/scripts/fixtures/clean-in-band.tsv -- python3 skills/margin-ledger/scripts/margin-ledger.py` → ACCEPTED, exit 0 (from the pack root). Deleting either fixture returns this gate to `unverified`.

- **Advisory at v0**: everything feeding the script. That means the honesty of the human baseline, the wall-clock capture method, the 2–4x band reading, the pre-add projection, and the choice of which gate to cut on a breach. Each is stated so a later wave can mechanize capture; claiming more would launder advisory into enforced.

## Done means

- [ ] The ledger holds one row per story shipped through the stack, each baseline with its source named
- [ ] `margin-ledger.py` exits 0 over the current ledger at floor 1.0
- [ ] Every gate added since the last review carries its recorded pre-add projection
- [ ] The script's output is captured as evidence with the stack's current gate list

An open box means the margin claim stays `unverified`: cut or cheapen a gate, re-measure the next story, re-run the script, re-check the boxes.

**The gates may spend the agent's speed. They may never spend the margin: below 1x, cut the gate (C5).**
