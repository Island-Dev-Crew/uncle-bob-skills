---
name: mythical-agent-month
description: Brooks's law generalised to agent fleets - adding agents to a late project adds coordination surface, not progress, because communication paths grow as n(n-1)/2 while only partitionable work actually divides. Reach for it when deciding how many agents to run at once, when a fleet looks busy but the story is not landing sooner, or on "how many agents should I run", "add more agents", "fleet sizing", "would a bigger fleet be faster", "why is parallel slower". Differentiator - it sizes the FLEET and prices its coordination surface, so a serial relay of specialists and a crowd of peers can be compared as numbers rather than vibes.
---

# Mythical Agent Month: coordination surface is what a crowd costs

Bob's relay is five agents, not one, and he is explicit that staging costs something: the seats have to hand work to each other, each new seat pays *"startup times are high… 10, 15 seconds to even start up… then it's got to figure out its whole context all over again"* (C10), and the whole stack is still worth it only because the margin survives — *"factor of four, factor of five improvement… and very high quality"* (C5). This island is the sizing question underneath that: **how many agents before the handoffs eat the margin?**

The answer is fifty years old. The [seventies-canon brief](../../research/seventies-canon.md) records Brooks's law and the surgical team from *The Mythical Man-Month* (1975) and argues both generalise to agent fleets: adding agents to a late project adds coordination surface, not progress. The arithmetic is simply the number of distinct pairs in a set of n — **n(n-1)/2** — and it is quadratic while your throughput gain is, at best, linear. Bob's own fleet note points straight at the tension: *"you could have three coders running at the same time. And my little laptop can support a lot more than three"* (C10). The machine can host more agents than the work can absorb, and that gap is where fleets go wrong.

### A grounding note, because this island is about honest cost

The roster line for this island carries the phrase "communication overhead like crazy" as a C9 quote. It is in the source transcript, but it is **not in [the concept ledger](../../01-CONCEPT-LEDGER.md)**, and the ledger is the only thing an island may quote the conversation from ([CONTEXT.md](../../CONTEXT.md)); claims that go beyond the conversation cite a brief in `research/` instead. So this island rests no claim on it and does not cite it as ledger-backed authority. Everything quoted above is ledger-backed; the ledger gap is recorded here rather than papered over.

## Where this island sits

- **The five-seat relay itself is [`seat-relay`](../seat-relay/SKILL.md)** — specifier, coder, cleaner, hardener, QA, the batons between them, the born-do-die lifecycle (C9, C10). That island runs the relay. **This island owns FLEET SIZE and its coordination cost** — how many agents, in what topology, before the handoffs stop paying.
- **The continuous agent-versus-human productivity ledger is [`margin-ledger`](../margin-ledger/SKILL.md)** — per-story gated wall clock against an honest human baseline, defending the 2–4x band and the 1x floor (C5). That island prices the **gate stack** as stories ship. This one prices the **fleet** before you spawn it. They meet at one number: an oversized fleet shows up in the margin ledger as a thinning margin, and this island is where you find out which agent caused it.
- **Per-step model picks are a Forge concern — [`model-routing`](../../COMPANION.md#model-routing).** Cheapening a seat's model changes what an agent costs per minute; it never changes how many communication paths a fleet has. Size first here, then route each seat there.
- **Same-machine isolation mechanics belong to [`worktree-fleet`](../../COMPANION.md#worktree-fleet).** Once this island says "three coders", giving each its own worktree is that island's job, along with its rule that worktree artifacts are inadmissible as gate evidence until re-derived from a fresh clone.

## Two shapes of work, and only one of them divides

| Shape | Example | What n does to it |
|---|---|---|
| **Partitionable** | five independent endpoints, five test files, five unrelated bug fixes | divides by n — this is the whole reason to run a fleet |
| **Needs shared context** | one domain model three seats must agree on, an interface being designed while it is being used | does not divide at all, and every agent holding it is one more that can disagree |

The second row is why "just add another agent" fails: work needing shared context is not made shorter by spreading it, and spreading it manufactures the pairs that then have to reconcile. Bob's compartmentalisation argument is the same claim at module scale — *"If you load up a module with every bit of stuff under the of under the sun [sic], the poor agent is going to wonder, 'What the heck am I doing in here?'"* (C15). A fleet with no partition is one loaded module wearing five hats.

## Why a serial relay beats a crowd

Compare the two topologies at the same headcount, using nothing but edge counts:

- **A crowd of n peers** on shared-context work is a mesh: **n(n-1)/2** paths. Five peers is ten reconciliations, and every one of them is an opportunity to disagree.
- **A relay of n seats** is a chain: **n-1** handoffs. Five seats is four batons — and each baton is a *typed artifact* (Gherkin, code, CRAP report, mutation log, QA verdict), not a conversation, so the coordination cost per edge is bounded by what the artifact contains rather than by how long two agents argue (C9).

Five seats: 4 edges. Five peers: 10 edges. Same headcount, two and a half times the surface — and the relay's edges are the cheap kind. That is the whole case for staging specialists in series, and it is why the relay can afford five agents on work that would drown five peers.

The relay's costs are still real and still additive: each seat pays the fixed startup and context-rebuild toll (C10), and the stack must keep the margin above the human floor or *"you've lost the game"* (C5). Serial staging buys a better edge count; it does not buy immunity.

## The sizing model

```
elapsed(n) = S * ((1 - p) + p/n)   +   h * n(n-1)/2
             \___ partition term ___/   \_ pair term _/
```

| Symbol | Meaning | Where the number comes from |
|---|---|---|
| `S` | serial minutes — the work if one agent did all of it | historical actuals, or the same honest-baseline discipline `margin-ledger` demands |
| `p` | partitionable share, 0 to 1 | your read of the story — the estimate most likely to be wrong, and the one to write down before you are attached to an answer |
| `h` | handoff minutes per communication path | measure it once: how long two agents' work actually took to reconcile |
| `n` | fleet size | the thing being decided |

The partition term divides only the partitionable share — shared-context work does not divide at all. The pair term is Brooks's. `elapsed` is convex in n (the first term falls at a decreasing rate, the second rises at an increasing one), so the first fleet size whose successor costs **at least as much** is the global optimum, and no search past it is needed. That "at least as much" is the script's own rule (`crossover()` triggers on `>=`): an exact tie counts as not paying, the same way the exit table does.

## One command

[`scripts/fleet-cost.py`](scripts/fleet-cost.py) reads a four-key plan file and answers one question — does the **last** agent in the proposed fleet still reduce elapsed time?

```bash
python3 scripts/fleet-cost.py <plan-file>
python3 scripts/fleet-cost.py --help      # -h is accepted as the same flag
```

| Exit | Meaning |
|---|---|
| `0` | the proposed fleet pays — the last agent reduces elapsed time. Also `--help` (or its accepted synonym `-h`) on a working stdout. |
| `1` | Brooks — the last agent does not reduce elapsed time. A tie counts as not paying: it bought nothing and added a path. |
| `2` | not a verdict — usage error, a path that is not a regular file (directory, FIFO, `/dev/zero` and other character devices), a plan over 64 KiB, unreadable file, non-UTF-8, malformed line, unknown key, duplicate key, missing key, out-of-range value, dead output stream, internal failure. |

Three codes; the script emits no others — and every input reaches one of them. The path is `stat`ed and refused unless it is a regular file, and the read is capped at 64 KiB, so there is no input class that runs forever instead of returning a code (`/dev/zero` on an uncapped read is a hung CI job, not a refusal). All arithmetic runs in exact rationals (`fractions.Fraction`), so no verdict is ever decided by a float; every printed minute figure is rounded for display, and when rounding would hide a non-zero difference the exact ratio is printed beside it.

### Red and green, both run

```bash
python3 scripts/fleet-cost.py scripts/fixtures/oversized-fleet.txt     # exit 1
python3 scripts/fleet-cost.py scripts/fixtures/right-sized-fleet.txt   # exit 0
```

The two fixtures carry **identical values for `serial_minutes`, `partitionable` and `handoff_minutes`, and differ only in `fleet`** (5 versus 2; their comment lines differ in wording and are not parsed), so the red run fails for the reason claimed — the fifth agent's marginal cost — and not for malformed input. The red run prints `crossover fleet 2 is the last size that still pays` and `elapsed fleet 4: 414.00m -> fleet 5: 499.60m (delta +85.60m)`.

The pack's own acceptance ritual agrees ([`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)):

```bash
bash ../known-dirty-fixture/scripts/prove-gate.sh scripts/fixtures/oversized-fleet.txt \
  scripts/fixtures/right-sized-fleet.txt -- python3 scripts/fleet-cost.py   # exit 0, ACCEPTED
```

A gate that only ever saw the input its author imagined is not hardened, so the same violation was re-run through the encodings a real editor or CI produces — a UTF-8 BOM plus CRLF line endings on the *dirty* plan, which still lands on the same verdict:

```bash
python3 scripts/fleet-cost.py scripts/fixtures/dirty-bom-crlf.txt   # exit 1
```

### A closed hole, kept as a fixture

`str.splitlines()` breaks on eight separators beyond LF/CRLF/CR — `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e`, U+0085 (NEL), U+2028 and U+2029. While the parser used it, a line whose first character was `#` was **not** ignored: everything after an embedded separator on that line was read as live configuration. The worst shape for this island is `handoff_minutes 0` smuggled inside a comment, because it zeroes the Brooks pair term — the one number the island exists to charge — so every fleet size then reports `PAYS`. U+2028 is what macOS TextEdit and Notes emit for a soft break and what survives a paste out of a PDF; `\x0c` is a routine Emacs page break.

The parser now splits on `\r\n|\r|\n` only, and tokenises on spaces and tabs only, so a comment line is ignored whole and every other whitespace character stays inside its token and is refused as an unknown key or a malformed value. The fixture is a three-key plan whose comment carries a U+2028 ahead of `handoff_minutes 0`:

```bash
python3 scripts/fleet-cost.py scripts/fixtures/comment-smuggle-u2028.txt   # exit 2, missing required key(s): handoff_minutes
```

That is the same code the byte-identical control returns with an ordinary space in place of the U+2028 — which is the point: the separator now changes nothing.

Hostile inputs were swept separately and every one returned `2`, never a verdict code: `nan`, `inf`, `4.8e2`, `-25`, `3/5`, `4_80`, a 4400-digit value, a duplicate key, a missing key, `Serial_Minutes` (case variant, refused rather than silently re-routed), a trailing `# comment` after a value, a `#` line carrying any of the eight exotic separators above ahead of a live key, an NBSP used as the key/value separator, `/dev/zero`, a FIFO with no writer, a 64 KiB+1 plan, `fleet 0`, `fleet 99999`, `fleet 5.0`, `partitionable 2`, an empty file, a UTF-16 file, a missing file, a directory, no arguments, two arguments. Recompute them rather than trusting this sentence.

A dead output stream is swept the same way, in both of its shapes — a closed-reader pipe, and an fd closed before the process starts (where CPython sets the stream to `None` and `print()` becomes a silent no-op, so an unguarded script would report a verdict into an empty log):

```bash
python3 scripts/fleet-cost.py scripts/fixtures/right-sized-fleet.txt >&-   # exit 2, not 0
python3 scripts/fleet-cost.py scripts/fixtures/oversized-fleet.txt   >&-   # exit 2, not 1
python3 scripts/fleet-cost.py --help                                 >&-   # exit 2, not 0
python3 scripts/fleet-cost.py scripts/fixtures/right-sized-fleet.txt 2>&-  # exit 2
```

## Known limit, disclosed rather than hidden

The model charges an **all-pairs mesh**. A hub-and-spoke fleet — one lead agent, k workers who never talk to each other — really has k paths, not k(k+1)/2, and this script over-charges it. The failure direction is over-strict (it refuses a plan the real topology would still pay for), never a false green, and it has a captured run:

```bash
python3 scripts/fleet-cost.py scripts/fixtures/hub-topology-blindspot.txt   # exit 1
```

At `S=480, p=0.9, h=8, fleet=6` the mesh model charges 15 paths and returns `1`; under hub-and-spoke the same fleet has 5 paths and would still be improving. Until a topology field exists, read a `1` on a genuinely hub-shaped fleet as "check the topology", not "cut an agent".

## Enforced vs advisory

- **`enforced`** — the arithmetic and the refusals: `fleet-cost.py` exits `1` on a fleet size whose last agent does not reduce exact-rational elapsed time, and `2` on every input it cannot parse into exactly the four named keys. Its own red/green acceptance is enforced by `prove-gate.sh` (run above, exit 0). This island's shape is enforced by [`validate-island.py`](../../scripts/validate-island.py).
- **`advisory`** — every input number. `S`, `p`, and `h` are estimates, and the script cannot check any of them; a wrong `p` produces a confident wrong verdict. Write the three numbers down with their source before running it, exactly as `margin-ledger` demands of a human baseline, or the output is a guess wearing an exit code.
- **`advisory`** — the topology judgement (mesh versus chain versus hub), the choice to stage serially rather than fan out, and everything about *which* agent to cut. No checker sees your fleet's shape.

## Done when

- [ ] The story's partitionable share is written down as a number with its reasoning, before the fleet size is chosen.
- [ ] `python3 scripts/fleet-cost.py <plan>` exits `0` for the fleet you intend to spawn, and the plan file is kept beside the run.
- [ ] Shared-context work is named explicitly and assigned to **one** agent or one relay chain, never split across peers.
- [ ] The crossover size is recorded, so the next person adding an agent knows what they are spending.
- [ ] If the fleet is hub-shaped, the limit above is acknowledged in the run notes rather than silently ignored.

**No authority without evidence. Paths grow as n(n-1)/2 and progress does not — count the edges before you spawn the crowd.**
