All research verified. Final report follows.

## Core mechanism

In the interview transcript, Bob Martin frames the agent-era gap as "tactical versus strategic programming": agents are "really good at tactical, really bad at strategic," and his prescription is "the old books, the ones that nobody reads because they're old… Tom DeMarco… Ed Yourdon… the pragmatic programmer" (transcript, /private/tmp/…/va-unclebob/transcript.txt, sentence-lines 485–534). The 1970s–80s canon is strategy distilled: it was written when compute was scarce and every design decision had to be made *before* code was cheap — exactly the position of a 2026 engineer whose agents make code nearly free but design errors compounding.

## Provenance & history

- **Parnas (1972)** — "On the Criteria To Be Used in Decomposing Systems into Modules," CACM 15(12), pp. 1053–1058; origin of "information hiding": decompose by what each module *hides*, not by processing steps [1].
- **Constantine → Stevens/Myers/Constantine (1974)** — coupling/cohesion developed by Constantine in the mid-60s, canonized in "Structured Design," *IBM Systems Journal* 13(2), pp. 115–139; the journal's most-reprinted paper [2][3].
- **Yourdon & Constantine (1979)** — *Structured Design* (Yourdon Press) book-length treatment [3]; Yourdon's *Decline and Fall of the American Programmer* (1992) warned US devs would be outcompeted on cost/quality [4].
- **DeMarco** — *Structured Analysis and System Specification* (Yourdon Press, 1979): DFDs, data dictionary, functional decomposition [5]; *Controlling Software Projects* (1982), opening line "You can't control what you can't measure" — which DeMarco publicly softened in 2009 [6]; *Peopleware* (with Lister, 1987): "The major problems of our work are not so much technological as sociological in nature" [7].
- **Brooks** — *Mythical Man-Month* (1975): Brooks's law ("Adding manpower to a late software project makes it later"), conceptual integrity, the surgical team [8]; "No Silver Bullet" (1986/IEEE Computer 1987): essential vs. accidental complexity; no single technique yields 10x in a decade [9].
- **Dijkstra** — "Go To Statement Considered Harmful," CACM 11(3), March 1968 (editor's retitling of "A Case against the GO TO Statement," EWD215) [10]; "The Humble Programmer" (EWD340, 1972 Turing lecture): "intellectual manageability" as the limiting resource [11].
- **Weinberg (1971)** — *The Psychology of Computer Programming*: egoless programming — peer review whose goal is everyone finding defects, author included [12].
- **Royce (1970)** — "Managing the Development of Large Software Systems": drew the waterfall then wrote the unimplemented single-pass version "is risky and invites failure" — the canon's great irony: the industry adopted the strawman [13].
- **Hunt & Thomas (1999)** — *The Pragmatic Programmer*: DRY, orthogonality, tracer bullets [14].

## What holds up in 2026 for agent-directed engineering

- **Parnas's information hiding** is the load-bearing idea for agent context management: modules whose internals are hidden are exactly the modules an agent can regenerate without cascading breakage, and the module boundary is the natural context-window boundary [1].
- **Coupling/cohesion** gives the strategist an objective vocabulary for judging agent output — low coupling is what makes parallel agents on separate files safe (one writer per module) [2][3].
- **Brooks's law generalizes to agents**: adding agents to a late project adds coordination surface, not progress; and *conceptual integrity* — one mind owning the design — is precisely the strategic role Bob says humans must keep. The surgical team (one surgeon, many force-multipliers) is the human-plus-agents org chart, fifty years early [8]. "No Silver Bullet" says agents shrink *accidental* complexity only; essential complexity — deciding what the system means — stays human [9].
- **Dijkstra's intellectual manageability** is the review-gate criterion when generation is free: accept only code a human can still reason about [10][11].
- **Weinberg's egoless programming** transfers cleanly: review agent output the way peers reviewed each other — assume defects exist, find them without attachment [12].
- **Royce's irony** is the standing warning against process cargo-culting — read what the paper actually says (he demanded iteration and "do it twice"), a discipline that maps to evidence-gated pipelines over single-pass agent runs [13].
- **DeMarco/Lister**: specification-before-construction (DFDs → today's spec-first agent workflows) [5]; measurement with humility — DeMarco's own retraction models updating a doctrine when evidence turns [6]; and *Peopleware*'s sociological framing now covers human-agent teams too [7].
- **DRY and tracer bullets** are direct agent directives: agents love duplicating; tracer bullets are the thin end-to-end slice you have an agent walk before fanning out [14].

## Skill seeds

- **parnas-decomposition-gate** — module boundaries judged by what they hide — gate: each new module names its hidden design decision or the split is rejected.
- **coupling-budget** — coupling/cohesion taxonomy applied to agent diffs — gate: cross-module imports added by an agent require explicit justification in the PR evidence.
- **conceptual-integrity-owner** — one human architect per system, Brooks-style — gate: no merged design change without the owner's recorded sign-off; agent count never substitutes for it.
- **no-silver-bullet-triage** — classify work as essential vs. accidental complexity — gate: agents assigned only accidental items; essential items require a human decision record.
- **intellectual-manageability-review** — Dijkstra gate on generated code — gate: reviewer must restate the change's control flow in N sentences or it bounces.
- **egoless-agent-review** — Weinberg peer-review protocol for agent output — gate: defect count sought, not zero-defect claims; "looks good" without a found-or-falsified list fails.
- **royce-do-it-twice** — tracer-bullet/pilot pass before fan-out — gate: evidence of one working end-to-end slice before parallel agent dispatch.
- **measurement-humility** — DeMarco-style metrics with retraction clause — gate: every enforced metric names the behavior it might corrupt, reviewed quarterly.

## Citations

[1] https://dl.acm.org/doi/10.1145/361598.361623
[2] https://dl.acm.org/doi/10.5555/1241515.1241533 (also https://mrpicky.dev/a-brief-history-of-coupling-and-cohesion/)
[3] https://history.computer.org/pioneers/constantine.html
[4] https://en.wikipedia.org/wiki/Decline_and_Fall_of_the_American_Programmer
[5] https://archive.org/details/structuredanalys0000dema
[6] https://blog.carlana.net/post/my-early-metrics-book-controlling-software/ (retraction: https://cacm.acm.org/opinion/a-measure-of-control)
[7] https://en.wikipedia.org/wiki/Peopleware:_Productive_Projects_and_Teams
[8] https://en.wikipedia.org/wiki/Brooks%27s_law
[9] https://dl.acm.org/doi/10.1109/MC.1987.1663532 (PDF: https://worrydream.com/refs/Brooks_1986_-_No_Silver_Bullet.pdf)
[10] https://homepages.cwi.nl/~storm/teaching/reader/Dijkstra68.pdf
[11] https://www.cs.utexas.edu/~EWD/transcriptions/EWD03xx/EWD340.html
[12] https://en.wikipedia.org/wiki/Egoless_programming (book: https://geraldmweinberg.com/Site/Programming_Psychology.html)
[13] https://www.praxisframework.org/files/royce1970.pdf
[14] https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/ (https://en.wikipedia.org/wiki/The_Pragmatic_Programmer)

Bob's "old books" framing: local transcript at /private/tmp/claude-502/-Users-IDC2-5-Desktop-IDC-skills/061b386e-e97d-4adb-adf8-6065dec28950/scratchpad/va-unclebob/transcript.txt (he names DeMarco, Yourdon, and The Pragmatic Programmer explicitly). UNVERIFIED: none — all claims above are sourced; note the "tactical vs. strategic" vocabulary itself originates outside this canon (commonly attributed to Ousterhout's *A Philosophy of Software Design*, not verified here).