## Core mechanism

Ousterhout's thesis: the root enemy is complexity, defined by two causes — **dependencies** (code that can't be understood in isolation) and **obscurity** (important information that isn't obvious) — producing three symptoms: change amplification, cognitive load, unknown unknowns ([codito.in summary](https://codito.in/philosophy-of-software-design-ousterhout/); book: APoSD ch.2). The chief weapon is the **deep module**: small, simple interface hiding a powerful implementation; **information hiding** is how you get depth, **information leakage** (one design decision reflected in multiple modules) is the classic red flag. Shallow modules — wide interface, little hidden — add interface cost without absorbing complexity. **Tactical programming** (ship the next feature, accept kludges) compounds complexity; **strategic programming** treats great design as the primary goal and budgets **~10–20% of development time** as investment that repays within months; the "**tactical tornado**" is the prolific engineer who ships fast and leaves complexity behind (Ousterhout's own Stanford CS190 lecture ["Working Isn't Good Enough"](https://web.stanford.edu/~ouster/cgi-bin/cs190-winter18/lecture.php?topic=working)). **Comments are a design tool**: interface comments define the abstraction, and if a module can't be described simply in comments, the design is wrong; missing comments cost far more than stale ones. **Define errors out of existence**: redesign APIs so error cases can't occur, rather than handling/propagating them.

## Provenance & history

- Book: *A Philosophy of Software Design*, 1st ed. 2018; 2nd ed. July 2021, which added explicit disagreements with Martin on method length and comments ([Ousterhout's book page, Stanford](https://web.stanford.edu/~ouster/cgi-bin/aposd.php)).
- **Written debate**: Ousterhout and Martin held discussions Sept 2024–Feb 2025, published as a transcript at [github.com/johnousterhout/aposd-vs-clean-code](https://github.com/johnousterhout/aposd-vs-clean-code). Points of contention: **function length** (Martin: extract every meaningfully nameable thing, historically "2–4 lines" — now framed as pedagogy, not law; Ousterhout: over-decomposition yields shallow, *entangled* methods); **comments** (Martin: "comments are always failures," potential misinformation; Ousterhout: essential, irreplaceable, interface docs mandatory); **TDD** (Martin: red-green-refactor at second-scale; Ousterhout: "bundling" — design in larger units, tests after). Agreement: over-decomposition is real; some comments (public APIs) are needed; comprehensive unit tests are non-negotiable. The PrimeGenerator case study converged on a joint 4-method version faster than either original.
- **Recorded discussion**: YouTube, ["John Ousterhout and Robert 'Uncle Bob' Martin Discuss Their Software Philosophies"](https://www.youtube.com/watch?v=3Vlk6hCWBw0), posted ~Mar 30 2025.
- **Clean Code 2nd edition** (Addison-Wesley, Oct 8 2025) confirms the appendix: "Appendix: The Clean Code Debate," p.561, including the PrimeGenerator rewrites ([InformIT](https://www.informit.com/store/clean-code-a-handbook-of-agile-software-craftsmanship-9780135398579), [O'Reilly TOC](https://www.oreilly.com/library/view/clean-code-a/9780135398586/)).

## What holds up in 2026 for agent-directed engineering

The local transcript (`../source/transcript.txt`) is a host + Uncle Bob conversation (Ousterhout invoked, not present; exact venue/date UNVERIFIED). Verbatim substance:

- **Deep modules for agents** — the host proposes deep modules are "really good with models because they can read the interface without having to understand the implementation"; Bob: "Yeah, absolutely… they pay attention to the structure. It can allow them to not read the code beneath them, which is both a danger and an advantage… as long as the code is consistent, you're okay. They also pay attention to the tests."
- **TDD concession** — Bob: "I cannot and will not enforce [TDD] on the agents… I allow the agents to behave more like John [Ousterhout] would, which is to write a function and then write the test for that function… They always fall back on doing that. So I figure that's probably" fine. He substitutes **post-hoc deterministic gates** (mutation testing, CRAP/coverage, cyclomatic limits) run by fresh-context agents ("born, do the task, and die").
- **Context economy rationale** — lost-in-the-middle degradation; keep steering minimal and layer deterministic checks *outside* the context window.

Assessment: module-shape rules translate directly into context-budget rules. A deep module = a cheap token-priced abstraction: the agent loads interface + interface comment + tests, never the implementation. Information leakage = the same fact paid for twice in context. Ousterhout's comment doctrine wins outright for agents (interface comments are the machine-readable spec); Martin's tiny-function doctrine loses (entangled fragments force whole-file loads); Martin's testing rigor survives as *gates*, not *process*. Strategic programming's 10–20% becomes investment in repo shape that compounds across every future agent session.

## Skill seeds

- **interface-only-context** — agent must attempt tasks from interfaces + interface comments + tests before loading implementations; gate: log of files loaded per task, implementation loads justified.
- **deep-module-gate** — flag shallow modules at review; evidence: exported-surface-to-hidden-LOC ratio per module, trend enforced advisory→blocking.
- **leak-scan** — detect one design decision expressed in ≥2 modules; evidence: duplicate-knowledge report (grep/embedding) attached to PR.
- **define-errors-out** — API review pass that removes error cases by redesign; gate: count of raised/propagated error paths before vs after the change.
- **test-after-per-function** — codify Bob's concession: per-function test-after allowed, hardened by mutation-testing gate; evidence: mutation score + coverage artifact.
- **tornado-detector** — catch change amplification; evidence: files-touched-per-feature metric across recent PRs, threshold alarm.
- **strategic-ledger** — enforce the 10–20% investment mindset; evidence: tagged share of design/refactor work per cycle with before/after complexity metrics.
- **comment-as-spec** — every exported symbol carries an interface comment that states the abstraction without leaking implementation; gate: lint on exports + spot-check that comment alone suffices to use the module.

## Citations

- https://web.stanford.edu/~ouster/cgi-bin/aposd.php (book page, editions, Clean Code disagreements)
- https://web.stanford.edu/~ouster/cgi-bin/cs190-winter18/lecture.php?topic=working (tactical/strategic, tornado, investment — primary)
- https://codito.in/philosophy-of-software-design-ousterhout/ (dependencies+obscurity → three symptoms)
- https://github.com/johnousterhout/aposd-vs-clean-code (written debate, Sept 2024–Feb 2025)
- https://www.youtube.com/watch?v=3Vlk6hCWBw0 (recorded discussion, Mar 2025)
- https://www.informit.com/store/clean-code-a-handbook-of-agile-software-craftsmanship-9780135398579 and https://www.oreilly.com/library/view/clean-code-a/9780135398586/ (Clean Code 2nd ed., Oct 8 2025; "Appendix: The Clean Code Debate," p.561)
- Local transcript: ../source/transcript.txt (deep-modules-for-agents exchange; TDD concession — venue/date UNVERIFIED)