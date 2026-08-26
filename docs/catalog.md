# The 50-skill catalog

[← Back to the README](../README.md) · [Installation](../README.md#install-the-pack) · [Verification](../README.md#verify-the-pack) · [Evidence map](README.md)

Choose by the outcome you need, not by build wave. The six groups below are a discovery layer over the same fifty numbered skill directories.

**Tool-backed** means the skill ships at least one first-party script. It does not imply automatic CI wiring or that every claim is mechanical. **Playbook** means the skill deliberately leaves the core decision to a human or operating discipline. Each skill's own `Enforced vs advisory` section is authoritative.

<details open>
<summary><strong>Start & Ship</strong> — 9 skills · 6 tool-backed</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 1 | [Seat Relay](../skills/seat-relay/SKILL.md) | Move one story through a serial five-seat specialist relay with fresh context and typed handoffs. | Playbook |
| 2 | [Specifier Seat](../skills/specifier-seat/SKILL.md) | Turn settled intent into a Gherkin acceptance spec and human-viewpoint QA procedure. | Tool-backed |
| 3 | [QA Script Seat](../skills/qa-script-seat/SKILL.md) | Turn a QA procedure into a deterministic, story-bound executable UI gate. | Tool-backed |
| 16 | [Spec Mulch](../skills/spec-mulch/SKILL.md) | Let the temporary plan die on merge while the result and its standing gates remain the specification. | Tool-backed |
| 17 | [Story Cadence](../skills/story-cadence/SKILL.md) | Use small batches and feedback instead of a large plan that decays during execution. | Playbook |
| 35 | [Acceptance Surface Review](../skills/acceptance-surface-review/SKILL.md) | Define what a human still reads when agents write the implementation. | Tool-backed |
| 42 | [Manageability Review](../skills/manageability-review/SKILL.md) | Bounce code a human reviewer cannot restate clearly after one reading. | Playbook |
| 43 | [Egoless Fleet](../skills/egoless-fleet/SKILL.md) | Replace bare approval with a review record of defects found or hypotheses falsified. | Tool-backed |
| 44 | [Do It Twice](../skills/do-it-twice/SKILL.md) | Prove one thin end-to-end pilot before parallel agent fan-out. | Tool-backed |

</details>

<details>
<summary><strong>Quality Gates</strong> — 12 skills · 11 tool-backed</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 4 | [CRAP Gate](../skills/crap-gate/SKILL.md) | Put a per-function ceiling on complexity weighted by test coverage. | Tool-backed |
| 5 | [Mutant Hunt](../skills/mutant-hunt/SKILL.md) | Scope mutation hardening to covered lines in the story diff under a runtime budget. | Tool-backed |
| 6 | [Mutant Excusal Ledger](../skills/mutant-excusal-ledger/SKILL.md) | Require a written equivalence argument for every excused surviving mutant. | Tool-backed |
| 11 | [Threshold Port](../skills/threshold-port/SKILL.md) | Keep the value of a human practice, drop its ritual, and retune the numeric gate by experiment. | Playbook |
| 15 | [Known-Dirty Fixture](../skills/known-dirty-fixture/SKILL.md) | Make a checker earn trust by failing on known-bad input and passing known-good input. | Tool-backed |
| 23 | [Boy Scout Ratchet](../skills/boyscout-ratchet/SKILL.md) | Ensure every touched file leaves measurably no worse than it arrived. | Tool-backed |
| 24 | [Tests As Spec](../skills/tests-as-spec/SKILL.md) | Write the suite as a teaching document for the next fresh-context agent. | Tool-backed |
| 25 | [Gherkin Gate](../skills/gherkin-gate/SKILL.md) | Bind red-before-green evidence to the acceptance feature's hash. | Tool-backed |
| 32 | [Values Not Disciplines](../skills/values-not-disciplines/SKILL.md) | Require each quality rule to name its measuring tool or admit it is advisory. | Tool-backed |
| 33 | [Gate Toolchain](../skills/gate-toolchain/SKILL.md) | Select incremental CRAP and mutation tooling by implementation language. | Tool-backed |
| 34 | [Coverage Gaming Audit](../skills/coverage-gaming-audit/SKILL.md) | Find tests that execute code without asserting on it, then route them to mutation. | Tool-backed |
| 45 | [Measurement Humility](../skills/measurement-humility/SKILL.md) | Give every enforced metric a named failure mode and review date. | Tool-backed |

</details>

<details>
<summary><strong>Architecture & Modularity</strong> — 12 skills · 11 tool-backed</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 7 | [Dependency Fence](../skills/dependency-fence/SKILL.md) | Declare dependency direction, check it mechanically, and repair violations by inversion, interface, or split. | Tool-backed |
| 12 | [Arch Lens](../skills/arch-lens/SKILL.md) | Build a drill-down architecture viewer with dependencies and links to code. | Tool-backed |
| 13 | [Structure Interrogation](../skills/structure-interrogation/SKILL.md) | Extract the agent's model of what it built so a human can correct the partition. | Playbook |
| 21 | [Stability Order](../skills/stability-order/SKILL.md) | Compute instability, abstractness, and distance from the main sequence. | Tool-backed |
| 22 | [Component Cohesion](../skills/component-cohesion/SKILL.md) | Balance REP, CCP, and CRP while keeping a component inside one agent context. | Tool-backed |
| 26 | [Interface Budget](../skills/interface-budget/SKILL.md) | Price a module in context tokens and justify every implementation load. | Tool-backed |
| 27 | [Comment as Spec](../skills/comment-as-spec/SKILL.md) | Treat interface comments as the machine-readable specification an agent acts from. | Tool-backed |
| 28 | [Leak Scan](../skills/leak-scan/SKILL.md) | Detect one design decision expressed in multiple modules. | Tool-backed |
| 29 | [Define Errors Out](../skills/define-errors-out/SKILL.md) | Remove error cases by redesigning the API instead of adding another handler. | Tool-backed |
| 30 | [Tornado Detector](../skills/tornado-detector/SKILL.md) | Catch change amplification through the files-touched-per-change trend. | Tool-backed |
| 37 | [Parnas Partition](../skills/parnas-partition/SKILL.md) | Reject a module boundary that cannot name the design decision it hides. | Tool-backed |
| 38 | [Coupling Budget](../skills/coupling-budget/SKILL.md) | Charge every new cross-module edge against a declared budget and reason. | Tool-backed |

</details>

<details>
<summary><strong>Context & Agent Reliability</strong> — 6 skills · 4 tool-backed</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 8 | [Steering Audit](../skills/steering-audit/SKILL.md) | Separate generative prompt guidance from checkable rules that belong in gates. | Tool-backed |
| 9 | [Priority Zone](../skills/priority-zone/SKILL.md) | Protect the head of context with a size budget and placement lint. | Tool-backed |
| 10 | [Trajectory Hygiene](../skills/trajectory-hygiene/SKILL.md) | Make the mid-session kill-or-continue call before contamination compounds. | Playbook |
| 18 | [Thrash Watch](../skills/thrash-watch/SKILL.md) | Recognize circling, breakage chains, and give-up signatures, then choose an intervention. | Playbook |
| 36 | [Instruction Density Cap](../skills/instruction-density-cap/SKILL.md) | Put a countable ceiling on simultaneous directives in one prompt. | Tool-backed |
| 46 | [Plan Decay Detector](../skills/plan-decay-detector/SKILL.md) | Report when the plan's stated assumptions stop matching the repository. | Tool-backed |

</details>

<details>
<summary><strong>Economics & Strategy</strong> — 6 skills · 4 tool-backed</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 19 | [Margin Ledger](../skills/margin-ledger/SKILL.md) | Track whether a gate stack preserves the agent's speed advantage over a human baseline. | Tool-backed |
| 31 | [Strategic Ledger](../skills/strategic-ledger/SKILL.md) | Hold the tactical/strategic investment split in an evidenced band. | Tool-backed |
| 39 | [Conceptual Integrity Owner](../skills/conceptual-integrity-owner/SKILL.md) | Keep one named human accountable for the system's design. | Playbook |
| 40 | [Mythical Agent Month](../skills/mythical-agent-month/SKILL.md) | Size a fleet before communication paths consume the value of parallel work. | Tool-backed |
| 41 | [No Silver Bullet Triage](../skills/no-silver-bullet-triage/SKILL.md) | Route accidental complexity to agents and essential meaning to a human decision. | Playbook |
| 47 | [Change Cost Probe](../skills/change-cost-probe/SKILL.md) | Measure minutes or tokens per story and gate a rising cost-of-change trend. | Tool-backed |

</details>

<details>
<summary><strong>Learning & Transfer</strong> — 5 playbooks</summary>

| # | Skill | What it helps you do | Kind |
|---:|---|---|---|
| 14 | [Essence Pointer](../skills/essence-pointer/SKILL.md) | Use a working exemplar as the spec, then prove parity in a local implementation. | Playbook |
| 20 | [Boredom Dividend](../skills/boredom-dividend/SKILL.md) | Revive valuable practices humans abandoned only because they were tedious. | Playbook |
| 48 | [Human Subagent](../skills/human-subagent/SKILL.md) | Train a junior with the same briefs and gates used for agents until they can direct agents. | Playbook |
| 49 | [Strategy Shelf](../skills/strategy-shelf/SKILL.md) | Read the old engineering canon through the lens of agent-directed work. | Playbook |
| 50 | [Abstraction Ladder](../skills/abstraction-ladder/SKILL.md) | Test which fundamentals survive when the next abstraction rung reprices labor. | Playbook |

</details>

## Numbering and maintenance

The numbers preserve the historical roster; the outcome groups are editorial navigation and do not change skill identity or filesystem paths. Public titles come from each island's `agents/openai.yaml`. The skill's `SKILL.md` remains the source of truth for triggers, boundaries, enforced claims, advisory claims, and proofs.

No row is labeled “popular” or “best.” Those claims require real adoption or outcome telemetry that the repository does not currently collect.
