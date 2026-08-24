# Hardening plan toward 2.0 — scoped by threat model, not by precedent

**Status:** plan, not work. v1.2 is shipped and unchanged. Written 2026-08-23 after reading the full IDC Skills Forge 2.0.x chain (Codex rounds, Kimi K3 203/204, the 28edb94 candidate audit) and measuring this pack's own surface.

The Forge chain is the most useful thing available to this pack — not as a template to copy, but as a record of **which parts of that journey were essential and which were the Forge's specific problem.** Copying it wholesale would be the single most expensive mistake available here.

## What was measured, before deciding anything

| surface | Forge 2.0.x | Uncle Bob v1.2 |
|---|---|---|
| Install path | installer writing to 4 fleet roots, signed POSIX modes, loader handoff | `cp -R skills/<name> ~/.claude/skills/` |
| Shipped executable code | installer, console, integrity verifier, freshness launcher | 41 gate scripts, each reading files and returning an exit code |
| Network calls in shipped code | present (release/index fetch) | **zero** — no `urllib`, `requests`, `curl`, `wget` in any shipped script |
| Arbitrary execution | present (loader, hooks) | **zero** — no `os.system`, no `shell=True`, no `exec()`; the one `eval(` is `ast.literal_eval` |
| Filesystem writes outside own tree | installer, by design | **zero** — every `rm -rf` targets a quoted `mktemp -d` under a trap |
| Fetch-and-run instructions in skill prose | n/a | **zero** across all 50 `SKILL.md` |
| Signed manifest / threshold root / freshness gate | yes, load-bearing | none, and none required by the install path |

**The conclusion that saves months:** the Forge needed TUF-style first-contact trust because a compromised release *executes an installer* against four roots. Uncle Bob's worst case is a user copying a markdown file and some read-only scripts. The apparatus that took the Forge three adversarial rounds and two model families to get right is defending against an attack this pack's distribution model does not have.

## The seven pitfalls, and the choice each one forces here

Each is drawn from something that actually cost time in the Forge chain.

**1. Building trust infrastructure the threat model doesn't justify.** The Forge's 2-of-3 root ceremony, two independent digest channels, `releaseSequence` checkpoints and freshness launcher are correct *for the Forge*. → **Uncle Bob ships signed tags, published digests, and a documented one-command verify. Nothing more, unless the install path changes.** If it ever grows an installer, this decision is revisited, not inherited.

**2. Spending the expensive reviewer before the head is frozen.** Kimi burned its quota on `28edb94`; Codex then repaired the tree, and the receipt is void-on-move. → **Fix everything already known, freeze one head, *then* buy the cross-family review.** Never the reverse.

**3. The builder cannot verify itself.** Codex built the candidate and correctly refused to be its own acceptance seat. → **I authored all 50 islands, so I cannot be the acceptance seat.** Every blind critic in this build was still a Claude family member; that is construction QA, not independent acceptance. A non-Anthropic family must review the frozen head.

**4. The adversarial loop does not converge on its own.** Codex round 1 → 8 blocking findings → round 2 → more → the self-red-team found more again. → **The A/B/C tiering that terminated Wave 2 is standing policy from round one**, not a rule discovered mid-loop: tier A (false green on realistic input) blocks; tier B is fix-or-disclose-with-a-fixture; tier C makes the sentence true and always terminates.

**5. Aggregate green concealing a single failure.** A 241/241 suite hid a real regression until it was isolated. → **Per-island verdicts, never a pack-level pass number, as the shipping signal.**

**6. Test fixtures poisoning the release path.** Literal URLs inside a shipped test file made manifest generation refuse. → **Any integrity artifact added here must be built and run against the real fixture corpus before it is claimed**, because this pack deliberately ships hostile fixtures (non-UTF-8 bytes, BOM/CRLF, symlink trees, a `#`-prefixed path).

**7. The verification method being the untested part.** My own tooling was wrong seven times in this build — `$?` after a pipe and after a command substitution, `timeout` absent on macOS, `grep -P` returning zero on a present pattern, an `awk` line count disagreeing with the validator, a working-tree link sweep that shipped dead links into v1.0, and a decode crash on a deliberately non-UTF-8 fixture name. → **Every check added in this phase gets its own red/green proof, exactly like the gates it inspects.** `known-dirty-fixture` already states the rule; the tooling has to obey it too.

## The phases

Ordered so nothing expensive is spent on a head that is about to move.

**Phase 1 — clear the verification debt — COMPLETE (`0427e9d`, 2026-08-23).**
45 findings are already tiered and written down from Waves 2 and 3: **10 tier-B, 35 tier-C, zero tier-A.** Thirteen Wave-3 islands were modified after their last critic and never re-judged. Nothing here is a false green; it is claim precision — an "every" or "never" broader than the code, an exit-code table omitting a code it can emit, a stale count. Under the first law an unbacked sentence is laundering, so this is real debt. Exit condition: every island holds a clean blind-critic verdict at one head.

**Phase 1 evidence.** All 45 findings closed across 14 islands; blind critics passed 11 of 14 and caught five unbacked sentences in the other three — every one about the category-vs-enumeration fixes made earlier in this build, which is the pack's own lesson landing on its author. `instruction-density-cap` claimed a marker class its code did not implement, and the counterexample sat inside the sentence's own example string (`»` is category `Pf`, outside the five chosen), so a guillemet-bulleted rules file counted zero and consented at any cap. `measurement-humility` claimed it peels every punctuation and symbol mark while taking only `Sm`/`Sk` of the symbols, so `none©` and `tbd$` read as substance. `parnas-partition` claimed no respelling of a named marker survives; five ordinary ones did. All three widened to every `P*` and every `S*` (or, for the fold, to whitespace and the non-breaking hyphen), with the one sentence the code still could not back narrowed rather than defended.

The readability pass ran on all 50 islands in the same commit: **mean AI-likeness 38 → 23**, scored by the deterministic `ai-humanizer` scorer, **zero islands scoring higher after**. Substance was verified island by island against `git show HEAD:` rather than the working tree — 50/50 clean, no ledger citation, relative link, or enforced/advisory label lost, and nothing below 85% of its original word count. Readability improved and nothing shrank to buy it.

Standing verification at that head: 600/600 validator checks, 727 committed-tree links resolving, zero cache residue, and the same five `verify-proofs.py` mismatches as before — a heredoc, a `printf`-built fixture dir, and a `cd`-dependent pair, each confirmed correct by running its block whole. Those are the tool's documented limits, not island defects.

**Phase 2 — the dogfood audit — COMPLETE (`67a3dba`, 2026-08-24).** Run this pack's own doctrine over its own 50 islands: does any `SKILL.md` contain instructions that could invert authority, over-claim harness behaviour, or make an agent act outside the user's request? The measurement above says the mechanical answer is clean; the *semantic* answer needs the same adversarial reading the Forge's supply-chain island applies to third-party skills. A skills pack that has never audited itself for injection surface has no standing to teach the discipline.

**Phase 3 — script lane-keeping — COMPLETE (`f57ea34`, 2026-08-23).** 41 scripts, each asserted and proven to: read only paths it was given, write only under its own `mktemp`, never network, never execute constructed input, and return a documented exit code. Mostly true today; the point is to make it a *checked* claim rather than an observed one. Includes fixing the one real finding below.

**Phases 2 and 3 evidence.** Ten seats read all 50 islands adversarially and produced 34 raw findings; a synthesis seat verified 10 against the files. The verdict was the useful part: the pack **passes** the parts of its own doctrine that ask *is this skill hostile* — no egress, no eval, no credential access, no unpinned installs, nothing telling an agent to ignore prior instructions — and **failed** the parts that ask *is this skill honest about its authority, and does it hand my agent to someone else's prose.*

Two HIGH findings, both closed. The phrases *data not instruction*, *untrusted input* and *prompt injection* appeared nowhere across fifty islands while ten of them sent an agent into somebody else's text and acted on it; the third law now sits in [CONTEXT.md](CONTEXT.md) and at the ingestion **step** of all ten sites. And a dozen islands advertised a diagnosis then handed the agent a fix-until-green loop that deleted tests, reverted working trees and cut CI gates; REPORT is now the default on a diagnostic ask at all twelve.

Four findings were the pack teaching the wrong thing by example or by broken pointer, each confirmed by execution before it was fixed: `mkrepo.sh` overwrote a real repository's file, swept an untracked file into a commit and appended two fixture commits onto real history — exiting 0; five islands cited `unclebob/scripts/validate-island.py`, dead since the pack was separated out of the Forge, as the sole evidence for their only enforced claim; `crap-score.py` let an unreadable input take exit 1, the dirty-verdict code, inside the fix-until-green loop it prescribes; and `priority-zone`'s clean exemplar dropped an `ALWAYS`-tagged sandbox-key rotation rule, teaching that the way to meet a line budget is to delete an operational rule.

Phase 3 shipped [`scripts/lane-check.py`](scripts/lane-check.py): four lanes over the 41 shipped skill scripts — no network, no arbitrary execution, no unscoped `rm -rf`, exit codes documented in the file. **41 scanned, zero breaches**, proven red on four deliberate breach fixtures. UB-H1 is closed the honest way: `verify-proofs.py` inherently executes repository content, so it states that trust boundary plainly and refuses network, privilege-escalation and device-destructive primitives rather than pretending otherwise.

**Low findings, open and logged rather than quietly dropped:** `qa-script-seat` defers its runtime preflight and sandbox-safety layer to `computer-use-smoke`, which lives in the Forge and is absent from a pack-only install — the dependency note needs to say so and inline a minimum safety floor. `dependency-fence`'s sidecar `short_description` asserts a checker "agents cannot violate" while the island installs no hook. Four documented commands write to fixed `/tmp` paths (`component-cohesion`, `define-errors-out`, `interface-budget`), which collide between concurrent runs and follow a pre-planted symlink on a shared host. `interface-budget`'s closed reason vocabulary has no slot for *the user asked me to read this*, creating standing pressure to mislabel an honest read as `defect-suspected`.

**Phase 4 — freeze, then cross-family review.** One immutable head. A non-Anthropic family reviews it with a void-on-move receipt bound to that exact SHA. This is the gate v1.x cannot self-certify past.

**Phase 5 — proportionate release integrity.** Signed tags, a published digest of the release tree, and a `verify` command a user can run before copying a skill into their agent. The company site as first-contact witness publishing the exact release identity and digest — GitHub canonical, the site never a second mutable tree. This is the one piece of the Forge's first-contact design that transfers, because it is cheap and it is the only defence against "did I get what was published."

## The one real finding from this measurement

**UB-H1 — `scripts/verify-proofs.py` executes commands extracted from `SKILL.md` with `shell=True`.** On a repo you authored, harmless. But it is precisely the artifact-controlled-execution shape: a fork or PR that adds a command to a proof block gets it run by anyone who runs the verifier. Severity low (dev tool, not shipped as a skill, and the repo is the trust boundary), but it is my tool preaching a discipline it does not practise. Fix in Phase 3: drop `shell=True` in favour of an argument-vector run with an allowlisted leading token, or refuse to execute a command whose first token is not `python3`/`bash`/`./scripts/`.

## What this pack deliberately will not do

Stated so a future session does not quietly adopt it: no threshold root, no 2-of-3 ceremony, no `releaseSequence` checkpoint store, no freshness launcher, no signed POSIX-mode manifest, no fleet-parity gate. Every one of those defends an installer this pack does not have. If the distribution model changes, this list is the first thing to revisit — and the Forge's `28edb94` chain is the reference implementation to copy from, not to re-derive.

**No authority without evidence — and the right amount of apparatus is the amount the threat model earns.**
