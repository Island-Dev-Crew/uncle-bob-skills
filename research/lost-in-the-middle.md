## Core mechanism

LLMs do not use their context window uniformly. Liu et al. showed that when the relevant fact moves through a long context, accuracy traces a **U-shaped curve**: highest when the information is at the very beginning (**primacy**) or end (**recency**), and significantly degraded in the middle — sometimes worse than having no context at all ([TACL 2024](https://aclanthology.org/2024.tacl-1.9/)). Hsieh et al. tied this to an intrinsic **U-shaped positional attention bias**: beginning/end tokens receive more attention *regardless of relevance*, and calibrating that bias away ("found-in-the-middle") recovers up to 15 points ([Findings of ACL 2024](https://arxiv.org/abs/2406.16008)). Guo & Vosoughi confirmed primacy/recency as general **serial-position effects** across tasks and models, and found prompt-based mitigations inconsistent ([arXiv 2406.15981](https://arxiv.org/abs/2406.15981)). Consequence for prompting: an instruction buried mid-context competes for attention it structurally does not get, so long steering files are obeyed probabilistically — softly, like guidelines.

## Provenance & history

- **2023–24 — the founding paper.** "Lost in the Middle: How Language Models Use Long Contexts," Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang; TACL 2024 (submitted Aug 2023). Multi-document QA + key-value retrieval probes ([ACL Anthology](https://aclanthology.org/2024.tacl-1.9/); [code](https://github.com/nelson-liu/lost-in-the-middle)).
- **2024 — mechanism & psychology.** Attention-bias calibration ([Hsieh et al.](https://arxiv.org/abs/2406.16008)); serial-position effects ([Guo & Vosoughi](https://arxiv.org/abs/2406.15981)).
- **2025 — degradation beyond position.** **NoLiMa** (Modarressi et al., ICML 2025) removed lexical overlap between question and needle: at 32K tokens, 11 models drop below 50% of their short-context baselines ([arXiv 2502.05167](https://arxiv.org/abs/2502.05167)). Chroma's **"Context Rot"** report (Hong, Troynikov, Huber, July 2025) tested 18 models incl. GPT-4.1/Claude 4/Gemini 2.5: performance grows non-uniform with input length even on trivial retrieval/replication tasks ([research.trychroma.com](https://research.trychroma.com/context-rot)).
- **2025 — instruction-density decay.** **IFScale** (Jaroslawicz et al.): with up to 500 simultaneous instructions, even frontier models fall to ~68%; **universal primacy effects** (earlier instructions favored), errors shifting from modification to omission; reasoning models hold to ~100–250 instructions ([arXiv 2507.11538](https://arxiv.org/abs/2507.11538)). The specific "~3 rules then decay" threshold is **UNVERIFIED** — the evidence shows graded decay with density and position, not a cliff at 3.
- **2025–26 — practitioner doctrine.** Dex Horthy (HumanLayer), author of **12-Factor Agents** (April 2025), coined the **smart zone / dumb zone** framing — recall degrades past ~40% context utilization; ship work in the smart zone, reset ruthlessly ([Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/context-engineering-with-dex-horthy); [LinearB podcast](https://linearb.io/dev-interrupted/podcast/dex-horthy-humanlayer-rpi-methodology-ralph-loop)). Anthropic's context-engineering guidance: find the smallest set of high-signal tokens ([Sept 2025](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).

## What holds up in 2026 for agent-directed engineering

The transcript (`../source/transcript.txt`) shows Robert C. Martin independently converging on the research: agents "treat those rules in the Pirates of the Caribbean sense. They're more like guidelines"; his fix is to "trim that initial prompt down to its absolute minimum so that you can get as much of it as possible into its priority… and then do deterministic tools after the fact." The interviewer replies with "smart zone and the dumb zone… That's Dex Hardy's term" — verified as **Dex Horthy** (transcript mishears the name). The recording's primary [YouTube metadata](https://www.youtube.com/live/zcLPGC-tvgk) identifies both the channel and uploader as **Matt Pocock**, even though the transcript never names him. The interview is recorded in [`../source/README.md`](../source/README.md), retrieved 2026-08-19. This line previously said no URL was found and later left the interviewer's identity unverified; both claims were contradicted by the source metadata.

Evidence-based split:
- **Prompt (priority zone):** identity, task, the 3–10 constraints that must shape *generation* (style direction, architecture intent). Small, front-loaded — exploits primacy (Liu; IFScale).
- **Deterministic gate (post-hoc loop):** everything checkable — lint, types, tests, complexity, security, size caps. Gates don't occupy context, don't decay with length, and fail loudly; probabilistic compliance becomes enforced compliance. This is Martin's automated-checks loop and Horthy's Factor-style "own your context" made concrete.
- **Layering rule (from the transcript):** checks compose infinitely; steering instructions compete and dilute.

## Skill seeds

1. **priority-zone-trim** — keep the initial steering file within a token budget — encodes primacy/IFScale evidence as a hard line-count/token gate on CLAUDE.md/AGENTS.md.
2. **rule-to-gate-mover** — classify each steering rule as "generative" (stays in prompt) or "checkable" (moves to a deterministic hook/CI gate) — encodes the guidelines-vs-gates split.
3. **dumb-zone-monitor** — warn/reset when session context passes ~40% utilization — encodes Horthy's smart/dumb-zone threshold and NoLiMa/Context-Rot degradation curves.
4. **middle-instruction-audit** — flag must-follow instructions positioned mid-context; relocate to head or tail — encodes the U-shaped attention curve.
5. **gate-loop-harness** — run deterministic checkers (crap-score, lint, tests) in a fix-until-green loop after each agent pass — encodes "checks never decay."
6. **instruction-density-cap** — fail review when a single prompt carries more simultaneous directives than the model class reliably tracks — encodes IFScale's density-decay data.
7. **context-reset-ritual** — structured compaction/re-anchor of the priority zone on long sessions — encodes serial-position recency plus context-rot findings.

## Citations

- https://aclanthology.org/2024.tacl-1.9/ · https://github.com/nelson-liu/lost-in-the-middle
- https://arxiv.org/abs/2406.16008 · https://arxiv.org/abs/2406.15981
- https://arxiv.org/abs/2502.05167 · https://research.trychroma.com/context-rot
- https://arxiv.org/abs/2507.11538
- https://newsletter.pragmaticengineer.com/p/context-engineering-with-dex-horthy · https://linearb.io/dev-interrupted/podcast/dex-horthy-humanlayer-rpi-methodology-ralph-loop
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Local transcript: ../source/transcript.txt
