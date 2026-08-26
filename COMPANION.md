# Companion islands — the IDC Skills Forge

**Every local gate, fixture, and validator in this pack runs from a fresh clone without another repository.** The runtime floor is Python 3.10+ with the pinned gate dependencies in [`requirements.txt`](requirements.txt), Bash, Git, standard POSIX utilities, and UTF-8-capable output. No shipped script reaches for the Forge. The proof replayer named in [CONTEXT.md](CONTEXT.md) runs every eligible, safely replayable, sequenced proof inside this tree and reports every candidate it does not execute. That is the whole of the standalone claim, and it is the half a machine checks.

It is a claim about the **tools**, not about every step of every protocol. The pack was built under the IDC Forge methodology, and its islands were deliberately scoped so they never re-implement a concern the Forge already owns. Where an island says "that boundary belongs to X", X is one of the 22 Forge islands below. Most of those references are **boundary statements**: they tell you what this pack deliberately does *not* do, so you reach for the right tool instead of finding a half-built one here, and the island's own protocol still runs to its own gate without X.

Three are **hand-offs**, marked as such below, and they are the honest exception to "standalone". There an island's protocol routes a *required* step outside this repository, and the paragraph on this page is a summary of the concern, not enough to execute the step:

- [`qa-script-seat`](skills/qa-script-seat/SKILL.md) generates its driver in **computer-use-smoke**'s shape and hands that island the runtime preflight and the exit-code verdict.
- Each seat of [`seat-relay`](skills/seat-relay/SKILL.md) is briefed in **delegated-authority-prompt**'s mandate format.
- Relay seats isolate through **worktree-fleet** mechanics once more than one coder mutates the same repo.

Without those three islands the local gates still run and still fail closed; what you supply yourself is the step. Each island says so at the step, in its own words.

The Forge lives in the public [IDC Skills repository](https://github.com/Island-Dev-Crew/idc-skills) and is not vendored here. The three hand-off targets are [computer-use-smoke](https://github.com/Island-Dev-Crew/idc-skills/blob/main/skills/computer-use-smoke/SKILL.md), [delegated-authority-prompt](https://github.com/Island-Dev-Crew/idc-skills/blob/main/skills/delegated-authority-prompt/SKILL.md), and [worktree-fleet](https://github.com/Island-Dev-Crew/idc-skills/blob/main/skills/worktree-fleet/SKILL.md). If that repository is unavailable, the hand-off step is yours to satisfy with equivalent tooling. One further Forge island, [teach](https://github.com/Island-Dev-Crew/idc-skills/blob/main/skills/teach/SKILL.md), is named by [`human-subagent`](skills/human-subagent/SKILL.md) and [`strategy-shelf`](skills/strategy-shelf/SKILL.md) but is not one of the 22 boundaries below; the ruling that drew that line is entry 33 of [03-FORGE50-AUDIT.md](docs/03-FORGE50-AUDIT.md).

---

### agent-guardrails
Four mechanical layers beneath an agent fleet — shell denylist, git block, pre-commit gate, read-only data role. **Owns hook and denylist plumbing.** This pack's gates supply the *metric* (what to measure, what threshold fails); how a check gets wired into a pre-commit hook or a PreToolUse guard is that island's concern.

### arch-survey
Surveys a whole codebase for refactor opportunities: mines change-history hot spots, gates each through the deep-module deletion test, and ranks them into a before/after report. **Owns discovery and ranking.** [`arch-lens`](skills/arch-lens/SKILL.md) here renders and navigates structure; it never ranks what to fix.

### archipelago
The full-cycle, evidence-gated build protocol: typed contracts at every seam, gates that must be able to fail, loopback routing, a tamper-evident ledger, band caps. **Owns gate infrastructure.** This pack's gates plug into that machinery; they never re-invent ledgers, loopback, or band caps.

### computer-use-smoke
**HAND-OFF.** Drives a real UI through a scripted smoke path and asserts observable outcomes. **Owns behavioral UI assertion.** [`qa-script-seat`](skills/qa-script-seat/SKILL.md) generates the executable from a QA procedure and binds it to a story; the runtime assertion primitive is that island's. *That seat's step 2 needs this island's mechanics and does not restate them — outside this pack, and yours to supply if you do not have the Forge.*

### cross-family-review
The verdict ceremony: an independent reviewer from a **different model family** reviews a diff at an exact head along a Standards axis and a Spec axis, and returns a named-seat verdict bound to that SHA — the seat that wrote the code never reviews it, and the verdict **voids** the moment the head moves, including a message-only amend. **Owns who may review, what a verdict binds, and when it voids.** [`acceptance-surface-review`](skills/acceptance-surface-review/SKILL.md) rules only on *what surface* lands in front of that reviewer and how blast radius widens it; it invokes the ceremony and never redefines the verdict format, the void-on-move rule, or the author-never-reviews law.

### deep-modules
Vocabulary and enforcement for deep modules — much behaviour behind a small interface at a clean seam — with dependency-cruiser rules making entry points the only way in. **Owns the design vocabulary, entry-point rules, and the deletion test.** [`dependency-fence`](skills/dependency-fence/SKILL.md) is a named extension owning layering *direction* only; [`interface-budget`](skills/interface-budget/SKILL.md) (Wave 2) adds only the context-economy rationale.

### delegated-authority-prompt
**HAND-OFF.** Composes a maximum-authority delegation prompt in five slots — objective and definition of done, context pack, decision rights, stop conditions, evidence contract. **Owns the mandate format.** Each seat in [`seat-relay`](skills/seat-relay/SKILL.md) is briefed with that pattern rather than a new prompt shape. *The relay's step 1 needs the five slots and does not restate them; the five names above are the summary, not the island.*

### diagnose
A disciplined loop for hard bugs: build a red-capable feedback loop first, reproduce, minimise, hypothesise, instrument, fix with a regression test. **Owns debugging code.** [`thrash-watch`](skills/thrash-watch/SKILL.md) here watches *agent behaviour* — looping, flailing, giving up — and borrows "build the observation loop first" by reference.

### evidence-packet
Assembles a byte-verifiable packet — the diff, the verification-ladder commands, their captured outputs — so a reviewer recomputes instead of trusting. **Owns the evidence format.** CRAP reports, mutation logs, and fixture proofs from this pack are rungs captured in that format; this pack never defines a second one.

### finding-register
A durable register where each finding is enumerated at an exact SHA, provenance-marked, and given a collision-free id. **Owns durable finding capture.** [`thrash-watch`](skills/thrash-watch/SKILL.md) detects live; anything durable graduates into that register.

### gauntlet-loop
Fans out builder sub-agents each shadowed by a blind critic, looped against a falsifiable bar. **Owns parallel generation against one bar.** [`seat-relay`](skills/seat-relay/SKILL.md) is the serial counterpart: one baton down five different mandates. Many attempts at one bar is that island; staged specialist passes is this one. *(It is user-invoked in the Forge — a person runs it; no agent can fire it by description.)*

### grill
A relentless interview that reaches shared understanding before building, emitting settled decisions as ADRs. **Owns eliciting decisions from a human.** [`specifier-seat`](skills/specifier-seat/SKILL.md) starts *after* understanding is settled: it transforms an intent doc, it never interviews.

### handoff
Compacts a session into a state-based handoff a fresh agent resumes from, plus the wake protocol the receiver runs. **Owns the end of a context.** [`trajectory-hygiene`](skills/trajectory-hygiene/SKILL.md) owns the middle of one — when to continue, when to kill and respawn.

### job-to-be-done
Pre-build triage asking whether a thing should be built or automated at all, and where the human stays in the loop. **Owns the one-shot decision before work starts.** [`margin-ledger`](skills/margin-ledger/SKILL.md) owns the continuous accounting once agents are already running.

### model-routing
Routes a task to the cheapest model or tool that still clears its cognitive-demand floor, recording why the pick clears the bar. **Owns model and tool selection.** Relay seats invoke it for per-seat picks rather than setting their own floors; [`steering-audit`](skills/steering-audit/SKILL.md) cedes the tool-versus-model axis to it.

### prototype
Builds a throwaway prototype to answer one design question, then discards the code. **Owns throwaway code.** [`spec-mulch`](skills/spec-mulch/SKILL.md) here mulches throwaway *plan documents* — a different artifact with a different lifetime.

### skill-supply-chain-review
Audits a third-party skill before adoption — provenance, hidden invocation, dangerous instructions, injection surface — and emits a trust verdict bound to a pinned version. **Owns third-party adoption.** [`essence-pointer`](skills/essence-pointer/SKILL.md) is the opposite move: don't adopt the artifact, study it and build your own.

### skill-tune
Improves a skill or context file empirically — run, judge, edit, re-run, keep an edit only when a measured score rises. **Owns the measure-edit-keep loop for prose.** [`threshold-port`](skills/threshold-port/SKILL.md) applies that discipline to *numeric gate parameters*, referencing the loop rather than re-deriving it.

### spec-pipeline
One pipeline from a discussed feature to shipped code: spec, then tracer-bullet tickets with blocking edges, then implement at pre-agreed seams. **Owns spec-to-tickets-to-implement.** [`seat-relay`](skills/seat-relay/SKILL.md) is an execution discipline *inside* its implement stage, and [`spec-mulch`](skills/spec-mulch/SKILL.md) is an explicit, stated divergence from its publish-the-spec rule.

### wayfinder
Charts work too big for one session as a map of decision tickets, resolved one at a time. **Owns multi-session planning machinery.** [`story-cadence`](skills/story-cadence/SKILL.md) is comparative doctrine only — how big a batch should be and why — with no map or ticket machinery of its own.

### worktree-fleet
**HAND-OFF, conditional.** Git worktrees for same-machine parallel agents, with the boundary that worktree artifacts are inadmissible as gate evidence until re-derived from a fresh clone. **Owns parallel isolation and that evidence rule.** Relay seats reuse those mechanics when several stories mutate one repo. *(User-invoked in the Forge — read it directly.)* *The hand-off only bites once a second coder mutates the same repo; a single-story relay never reaches it. The evidence rule in bold is inlined at [`seat-relay`](skills/seat-relay/SKILL.md) and holds whether or not you have the island.*

### writing-for-agents
The universal levers for any document an agent reads: context pointers, the two loads, information hierarchy, completion criteria, pruning, failure modes. **Owns document-level context economy.** [`priority-zone`](skills/priority-zone/SKILL.md) owns the *positional* evidence and its enforcement — the token budget at the head of a context — not the wording levers.

---

**No authority without evidence.** These are the boundaries this pack refuses to cross — nineteen of them concerns it simply keeps its hands off, and three marked **HAND-OFF** where a protocol here reaches for a step that ships elsewhere. An island that quietly re-implemented one of them would be a duplicate, and the roster in [02-ROSTER-50.md](docs/02-ROSTER-50.md) records the boundary each one was built to respect.
