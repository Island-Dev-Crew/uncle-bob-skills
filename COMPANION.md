# Companion islands — the IDC Skills Forge

This pack is **standalone**: nothing here requires another repo to run, and every gate, fixture, and validator in it works from a fresh clone with nothing but `python3` and `bash`.

But the pack was built under the IDC Forge methodology, and its islands were deliberately scoped so they never re-implement a concern the Forge already owns. Where an island says "that boundary belongs to X", X is one of the 21 Forge islands below. Those references are **boundary statements, not dependencies** — they tell you what this pack deliberately does *not* do, so you can reach for the right tool instead of finding a half-built one here.

The Forge lives in its own repository (**IDC Skills Forge**, `IDC-skills`). If you have it, the islands below are at `skills/<name>/SKILL.md` in that repo. If you don't, this page is the whole answer: it tells you what the concern is and who owns it, and this pack keeps its hands off it either way.

---

### agent-guardrails
Four mechanical layers beneath an agent fleet — shell denylist, git block, pre-commit gate, read-only data role. **Owns hook and denylist plumbing.** This pack's gates supply the *metric* (what to measure, what threshold fails); how a check gets wired into a pre-commit hook or a PreToolUse guard is that island's concern.

### arch-survey
Surveys a whole codebase for refactor opportunities: mines change-history hot spots, gates each through the deep-module deletion test, and ranks them into a before/after report. **Owns discovery and ranking.** [`arch-lens`](skills/arch-lens/SKILL.md) here renders and navigates structure; it never ranks what to fix.

### archipelago
The full-cycle, evidence-gated build protocol: typed contracts at every seam, gates that must be able to fail, loopback routing, a tamper-evident ledger, band caps. **Owns gate infrastructure.** This pack's gates plug into that machinery; they never re-invent ledgers, loopback, or band caps.

### computer-use-smoke
Drives a real UI through a scripted smoke path and asserts observable outcomes. **Owns behavioral UI assertion.** [`qa-script-seat`](skills/qa-script-seat/SKILL.md) generates the executable from a QA procedure and binds it to a story; the runtime assertion primitive is that island's.

### deep-modules
Vocabulary and enforcement for deep modules — much behaviour behind a small interface at a clean seam — with dependency-cruiser rules making entry points the only way in. **Owns the design vocabulary, entry-point rules, and the deletion test.** [`dependency-fence`](skills/dependency-fence/SKILL.md) is a named extension owning layering *direction* only; [`interface-budget`](02-ROSTER-50.md) (Wave 2) adds only the context-economy rationale.

### delegated-authority-prompt
Composes a maximum-authority delegation prompt in five slots — objective and definition of done, context pack, decision rights, stop conditions, evidence contract. **Owns the mandate format.** Each seat in [`seat-relay`](skills/seat-relay/SKILL.md) is briefed with that pattern rather than a new prompt shape.

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
Git worktrees for same-machine parallel agents, with the boundary that worktree artifacts are inadmissible as gate evidence until re-derived from a fresh clone. **Owns parallel isolation and that evidence rule.** Relay seats reuse those mechanics when several stories mutate one repo. *(User-invoked in the Forge — read it directly.)*

### writing-for-agents
The universal levers for any document an agent reads: context pointers, the two loads, information hierarchy, completion criteria, pruning, failure modes. **Owns document-level context economy.** [`priority-zone`](skills/priority-zone/SKILL.md) owns the *positional* evidence and its enforcement — the token budget at the head of a context — not the wording levers.

---

**No authority without evidence.** These are the boundaries this pack refuses to cross. An island that quietly re-implemented one of them would be a duplicate, and the roster in [02-ROSTER-50.md](02-ROSTER-50.md) records the boundary each one was built to respect.
