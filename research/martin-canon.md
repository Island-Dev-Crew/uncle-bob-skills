## Core mechanism

Martin's canon is one idea applied at three scales: **constrain structure so change stays cheap, and prove it with tests.**

- **Clean Code (2008):** functions "should be small… do one thing" (Ch. 3); intention-revealing "Meaningful Names" (Ch. 2); the **Boy Scout Rule** — leave the code cleaner than you found it (Ch. 1) [InformIT 1st ed].
- **SOLID:** SRP ("gather things that change for the same reasons"), OCP ("open for extension, closed for modification"), LSP, ISP, DIP ("depend in the direction of abstraction") — his own definitions in "Solid Relevance" (2020).
- **Clean Architecture (2017):** the **Dependency Rule** — "source code dependencies can only point inwards"; component cohesion **REP/CCP/CRP** (Ch. 13) and coupling **ADP/SDP/SAP** (Ch. 14) [InformIT; 2012 blog post].
- **Three Laws of TDD:** (1) write a failing test before any production code; (2) no more test than suffices to fail; (3) no more production code than suffices to pass — the "nano-cycle" inside red-green-refactor ["The Cycles of TDD", 2014].

## Provenance & history

- SOLID + package principles first consolidated in **Agile Software Development: Principles, Patterns, and Practices** (2002; SRP/OCP/LSP/DIP/ISP as Chs. 8–12, package design Ch. 20) [InformIT].
- **Clean Code, 2nd Edition** is real: published **Sept 30, 2025** (Pearson, ISBN 9780135398579), a "comprehensive rewrite" — 7 languages (Java, JS, Go, Python, Clojure, C#, C), four parts (Code / Design / Architecture / Craftsmanship), new chapters on **AI tools** and testing disciplines, ethics [Pearson].
- **blog.cleancoder.com is dormant** — the archive ends Jan 2023 (verified by fetch); his 2025–26 positions live on X ("morning bathrobe rant" series, e.g. "AI out-codes you; deal with it"), interviews, an O'Reilly live course **"AI Agents for Clean Code"**, and GitHub (**unclebob/swarm-forge**, a tmux multi-agent orchestrator).

## What holds up in 2026 for agent-directed engineering

From the interview transcript (`…/scratchpad/va-unclebob/transcript.txt`) plus the sources above, his line is precise: **values transfer, disciplines don't.**

**Explicitly NOT imposed on agents:** strict TDD nano-cycle. Direct quote: "test-driven development… that's a human discipline… I cannot and will not enforce that on the agents. I don't think it makes any sense to make an agent write a single line of a test and then write a single line of the production code… it's probably a mistake to impose a human discipline on an agent. It is not a mistake to impose human values on the agent." He also doesn't read agent code: "my goal… I don't have to look at the code at all… I will look at the crap scores… and do spot checks" (transcript; corroborated by explainx.ai).

**Retained as measured gates:** tests everywhere; **CRAP score** (coverage × cyclomatic complexity per function — threshold ≤4 for humans, relaxed to 6, maybe 8 for agents because "they have a huge, perfectly accurate short-term memory"); **mutation testing** ("the hardener… absolutely merciless… 100% coverage"); module structure ("module structure, boundaries, dependency direction" — swarm-forge review gates); Gherkin acceptance tests + deterministic QA scripts as the human-reviewed surface. Prose rules fail: agents treat CLAUDE.md-style instructions "in the Pirates of the Caribbean sense — more like guidelines"; and "You can't tell an agent to be clean. You have to measure the cleanliness that they produce and have them correct failures" [X, status 2082497764223492161]. His pipeline: **specifier → coder (unit tests + Gherkin) → cleaner (CRAP analysis) → hardener (mutation) → QA agent**. Meta-position on tooling: "don't download those. I wrote them for me… point your agents at them… and build one for you" (transcript). CRAP acronym expansion ("Change Risk Anti-Patterns", Savoia/Evans): UNVERIFIED from primary sources.

## Skill seeds

- **crap-gate** — per-function CRAP ceiling (coverage × cyclomatic complexity) — CI fails any function above threshold (agent lane ~6, human lane 4); score report is the evidence artifact.
- **mutation-hardener** — post-green mutation pass on changed modules — gate: zero (or budgeted) surviving mutants, mutant log captured.
- **agent-gauntlet** — specifier→coder→cleaner→hardener→QA role pipeline — gate: each stage emits its tool output (Gherkin run, CRAP report, mutation log, deterministic QA script result) before handoff.
- **dependency-rule-scan** — imports point inward only, components acyclic (ADP) and stability-ordered (SDP/SAP) — gate: static import-graph check fails on outward/cyclic edges.
- **acceptance-surface-review** — human reviews only Gherkin specs + QA procedures, never implementation — gate: reviewed .feature files + passing executable QA script, criticality-scaled.
- **values-not-disciplines** — encode measured thresholds, never rituals (no red-green-refactor enforcement on agents; no prose-only "be clean" rules) — gate: every quality rule must name its measuring tool or be marked advisory.
- **harness-selfbuild** — agents study a reference harness and generate a project-local one — gate: generated tools pass against a known-dirty fixture before adoption.

## Citations

- Clean Code 1st ed (2008): https://www.informit.com/store/clean-code-a-handbook-of-agile-software-craftsmanship-9780132350884
- Clean Code 2nd ed (Sept 30, 2025): https://www.pearson.com/en-us/subject-catalog/p/clean-code-a-handbook-of-agile-software-craftsmanship-2nd-edition/P200000013239/9780135398548
- Clean Architecture (2017), Chs. 13/14/22: https://www.informit.com/store/clean-architecture-a-craftsman-s-guide-to-software-9780134494166
- Dependency Rule (2012): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- SOLID definitions, "Solid Relevance" (2020): https://blog.cleancoder.com/uncle-bob/2020/10/18/Solid-Relevance.html
- Three Laws / Cycles of TDD (2014): https://blog.cleancoder.com/uncle-bob/2014/12/17/TheCyclesOfTDD.html
- PPP (2002): https://www.informit.com/store/agile-software-development-principles-patterns-and-practices-9780135974445
- Blog index (dormant since Jan 2023): https://blog.cleancoder.com/
- swarm-forge: https://github.com/unclebob/swarm-forge
- O'Reilly live course: https://www.oreilly.com/live-events/ai-agents-for-clean-code-with-uncle-bob-martin/0642572376765/
- X posts: https://x.com/unclebobmartin/status/2082497764223492161 ; https://x.com/unclebobmartin/status/2046206145597972849
- Interview transcript (local): /private/tmp/claude-502/-Users-IDC2-5-Desktop-IDC-skills/061b386e-e97d-4adb-adf8-6065dec28950/scratchpad/va-unclebob/transcript.txt
- Secondary corroboration: https://explainx.ai/blog/uncle-bob-ai-coding-gauntlet-tests-not-reviews-july-2026 ; https://akitaonrails.com/en/2026/04/20/clean-code-for-ai-agents/