---
name: stability-order
description: Component stability computed as a check instead of argued as an opinion - instability I = Ce/(Ca+Ce), abstractness A = abstract-types/total-types, distance from the main sequence D = |A+I-1|, with Stable Dependencies and Stable Abstractions violations failing loudly and naming the offending component. Reach for it when components are argued about rather than measured, when deciding which component owes you abstractions, or on trigger phrases like 'stable dependencies principle', 'instability metric', 'distance from the main sequence', 'which component should be abstract'. Differentiator - this island owns the computed NUMBERS only; the declared layering direction belongs to the sibling dependency-fence, and hook plumbing, gate infrastructure and evidence format live on neighbouring islands.
---

# Stability Order: the numbers a component cannot argue with

Bob's structural move is a human one: *"I'd interrogate the agents. What's the structure here? How does this module interrelate with that module?… and then I would get scared to death because the answers were horribly frightening. And then I would design a module structure…"* (C12, [ledger](../../docs/01-CONCEPT-LEDGER.md)). The interrogation returns prose, and prose is where opinion hides. This island turns the countable half of that answer into arithmetic. Three numbers per component. Two principles read as verdicts over those numbers. A checker that names the component out loud when either principle breaks. What remains judgement stays judgement, and is labeled so below.

Research ground for every non-transcript claim here is [`martin-canon.md`](../../research/martin-canon.md): Clean Architecture (2017) Ch. 14, the component *coupling* chapter that carries ADP, SDP and SAP, plus the DIP formulation *"depend in the direction of abstraction"*.

## The three numbers

For each component `c` (a deployable/releasable grouping, not a file):

```
Ce(c) = count of distinct components c depends on          (efferent coupling, outgoing)
Ca(c) = count of distinct components that depend on c      (afferent coupling, incoming)

I(c) = Ce / (Ca + Ce)                 instability   0 = maximally stable, 1 = maximally unstable
A(c) = abstract_types / total_types   abstractness  0 = wholly concrete, 1 = wholly abstract
D(c) = | A(c) + I(c) - 1 |            distance from the main sequence, 0 = on it
```

Read them as pressure, not virtue. `I` says how free a component is to change. Nothing depends on it and it depends on everything → `I = 1`, change it freely. Everything depends on it and it depends on nothing → `I = 0`, it is pinned. `A` says how much of it can be extended without editing it. The main sequence is the line `A + I = 1`, where the two are in balance, and `D` is how far off that line a component sits.

Two edge cases decide whether the gate is honest:

- **`Ca + Ce = 0` leaves I undefined.** There is no division to perform. So the checker prints the component as `ISOLATED` and excludes it from both verdicts, rather than defaulting it to a passing number. Silent defaults are how components sneak past a metric gate.
- **A graph with no edges judges nothing**, so the checker exits 2 rather than 0. An empty gate cannot pass.

## The two principles, as verdicts

**SDP: Stable Dependencies.** Depend in the direction of stability. A component should not depend on anything less stable than itself. As a check over the graph: for every edge `X -> Y`, `I(X)` must be `>= I(Y)`, so instability never increases along a dependency arrow. A breach names the pair and prints both numbers.

**The `>=` is this island's chosen boundary, not a quotation.** [`martin-canon.md`](../../research/martin-canon.md) verifies the principle and its chapter, but it carries no comparator. The non-strict form is a decision made here: it matches [`crap-gate`](../crap-gate/SKILL.md)'s exactly-at-passes convention, and the clean fixture depends on it. Equal instability passes. That buys discrimination at the boundary and costs one exemption, stated here rather than hidden: **every edge inside an `I`-uniform subgraph is exempt from SDP.** A pure dependency cycle is exactly that shape. Each node on it has `Ca = Ce`, so `I` is uniform and no edge can breach. The gate reports the metrics and exits 0. That blind spot is captured as a run below, and cycle bans belong to [`deep-modules`](../../COMPANION.md#deep-modules).

**SAP: Stable Abstractions.** A stable component should be abstract; an unstable one may be concrete. This completes SDP. If the pinned component is abstract, everything depending on it can extend rather than edit it (DIP, [`martin-canon.md`](../../research/martin-canon.md)). `D` is the single number that carries it: a component breaches when `D > max-distance`. The two breach directions are opposite diseases, so the checker labels which one:

| side | shape | what it feels like |
|---|---|---|
| `concrete-and-stable` (`A + I < 1`) | everything depends on it, nothing in it is extensible | rigid: every change to it is a change to everyone |
| `abstract-and-unstable` (`A + I > 1`) | abstraction nobody depends on | dead weight: interfaces with no callers |

Clean Architecture Ch. 14 gives these two regions names. The brief in [`martin-canon.md`](../../research/martin-canon.md) verifies the principles and the chapter, not the region nicknames. So the checker prints the symptom instead of a nickname it cannot cite.

**Both comparisons are exact, and neither carries a tolerance.** `Ce`, `Ca`, `abstract` and `total` are counts, so `I`, `A` and `D` are rationals. The checker computes them as `fractions.Fraction` and parses `--max-distance` as one too, so the verdict turns on the number you wrote rather than on the double nearest it, and every decimal in the output is rendering. The precision matters in both directions, and the island got it wrong in one of them: a `1e-9` epsilon used to widen both comparisons, and it passed a component sitting at `D = 1/3` against `--max-distance 0.333333333`. Plain floats fail the opposite way — `0.3 + 0.6 - 1` is `0.10000000000000009`, so a component at exactly `D = 1/10` would be convicted of breaching `0.1`. Exact rationals are the only reading that is strict without also being wrong, and both readings are captured as runs below.

## The input contract

One JSON file, structural. The checker parses objects and arrays, never patterns, so there is no regex in it to fool:

```json
{
  "components": { "use-cases": { "abstract": 4, "total": 8 } },
  "edges": [["adapters", "use-cases"]]
}
```

`edges` run component-to-component and get deduped, so `Ce` counts distinct neighbours: a hundred imports into one component still count once. Four shapes are spec errors that exit 2 — an edge naming an undeclared component, a self-edge, `abstract > total`, or `total < 1`. The fence fails closed, and the fix is declaring the component, not dropping the edge.

Extracting the graph is your stack's job (`go list -deps`, `jdeps`, dependency-cruiser rolled up to package level, an import scan). **Counting `abstract` types is the judgement call this island does not make for you.** Pick the rule your language actually supports: interfaces plus abstract classes in Java or C#, protocols in Swift, exported interfaces plus type-only exports in TS. Write it down once, then apply it the same way to every component. A metric computed by an inconsistent rule is an opinion wearing a decimal point.

## Wiring the loop

The checker is the tool at the end of C14's pattern: *"another deterministic tool… That goes into a nice tight little specification file that the agents cannot violate. There's another little checker that runs at the end"*. And it runs inside C4's loop: *"you must change the code until this tool says that it's okay."*

```bash
python3 scripts/stability-check.py components.json --max-distance 0.5
```

Exit `0` green, `1` violations, `2` usage/IO/malformed spec. The three are deliberately distinct: a broken spec must never read as a verdict.

**When it goes red, the levers are the formula's own.** For an SDP breach on `X -> Y`, either `X` becomes less stable or `Y` becomes more stable; in practice, stop pointing `X` at volatile `Y` directly. For a `concrete-and-stable` SAP breach, the lever is `A`: extract abstractions from the pinned component. For `abstract-and-unstable`, the lever is `Ca`: either something should depend on that abstraction, or it should be deleted. Which edit implements the chosen lever (invert the dependency, insert an interface, split the module in half) is [`dependency-fence`](../dependency-fence/SKILL.md)'s three-repair menu (C14), not this island's. This island's job ends at naming the offending component and the number that convicted it.

Editing `components.json` to turn red green is a redesign: the human's C12 act, taken in its own commit.

## The threshold is not the metric (advisory)

`--max-distance` defaults to `0.5`, and that default is a starting point, not a finding. Thresholds are exactly the part of a human discipline that moves when the worker changes (C17). Tune this number the way this pack tunes any gate parameter: run it at each candidate level, capture the outcomes, keep the level the evidence picks. That empirical loop is [`threshold-port`](../threshold-port/SKILL.md)'s. An agent's opinion about the right ceiling is a hypothesis and nothing more: *"you can't trust any debate you have with an agent, but I still have them anyway"* (C18).

## Boundaries

This island supplies metric content only:

- **Layering direction** belongs to the sibling [`dependency-fence`](../dependency-fence/SKILL.md): which module *may* depend on which, declared by a human in a fence spec. That island owns the declared direction and its three sanctioned repairs. This one owns the computed stability and abstractness numbers over whatever graph exists. Direction is a rule you write; instability is a number you measure. Run both: a graph can point perfectly inward and still have a stable component that is wholly concrete.
- **Entry-point rules, cycle bans, and the deletion test** belong to [`deep-modules`](../../COMPANION.md#deep-modules), along with the design vocabulary. This checker does not detect cycles and does not claim to. Because equal instability passes, an `I`-uniform cycle raises no verdict at all and exits `0` (captured run below). Nothing here substitutes for a cycle ban.
- **Hook and pre-commit plumbing** belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails): where the checker actually executes, whether pre-commit, PostToolUse, or a CI step. This island installs no hook.
- **Gate infrastructure** (loopback routing, the ledger, band caps) belongs to [`archipelago`](../../COMPANION.md#archipelago).
- **The captured metric report enters [`evidence-packet`](../../COMPANION.md#evidence-packet) format.** The checker's stdout plus its exit code become one rung of that packet's verification ladder, never a second evidence format.

## Enforced vs advisory

- `enforced`: the arithmetic and both verdicts. [`scripts/stability-check.py`](scripts/stability-check.py) computes `I`, `A` and `D` from the declared graph as exact rationals, then exits 1 on any SDP breach or any `D > max-distance`. Neither comparison carries a tolerance in either direction, so a breach `1e-10` past the ceiling fails and a component sitting exactly on it passes; the breach line widens its own numbers until the two render differently, out to the exact fraction. It exits 2 fail-closed on an undeclared component, a self-edge, `abstract > total`, an out-of-range `--max-distance`, an unreadable spec, or an edgeless graph. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: everything feeding the checker. What counts as a component boundary, the type-counting rule behind `A`, the graph-extraction command, the `0.5` ceiling, and the choice of lever when a breach lands. Each is named here so a later wave can mechanize it; claiming any of them as enforced would launder advisory into enforced.

**Red/green proof.** The checker earns its `enforced` line by having been watched failing, the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Recompute from this island's directory:

```bash
python3 scripts/stability-check.py scripts/fixtures/dirty-components.json   # exit 1
python3 scripts/stability-check.py scripts/fixtures/clean-components.json   # exit 0
```

The dirty run exits `1` on a well-formed spec, printing all three verdict kinds this gate can raise: `SDP-BREACH adapters -> use-cases` (0.33 < 0.50), `SDP-BREACH use-cases -> entities` (0.50 < 0.67), and `SAP-BREACH adapters D=0.54 > 0.50 … concrete-and-stable`. It fails on the check, not on the parse. The clean run exits `0` carrying both boundary cases, so the pair proves discrimination rather than blanket acceptance. `adapters -> use-cases` is an edge between two components of equal instability (0.50), and `legacy-util` sits at exactly `D = 0.50`. Both pass; nudge either and the gate goes red. The pair also runs under the ritual's own runner:

```bash
bash ../known-dirty-fixture/scripts/prove-gate.sh scripts/fixtures/dirty-components.json \
  scripts/fixtures/clean-components.json -- python3 scripts/stability-check.py   # exit 0, ACCEPTED
```

Deleting either fixture returns the gate to `unverified`.

**The boundary, pinned from both sides.** A third fixture carries one component at exactly `D = |3/10 + 3/5 - 1| = 1/10`, in a graph with no SDP breach anywhere, so the SAP comparison is the only judgement the run makes:

```bash
python3 scripts/stability-check.py scripts/fixtures/boundary-distance.json --max-distance 0.1            # exit 0
python3 scripts/stability-check.py scripts/fixtures/boundary-distance.json --max-distance 0.0999999999   # exit 1
```

Exactly on the line passes, and `1e-10` past it is past it: `SAP-BREACH report D=1/10 > 999999999/10000000000`. The red run reported `0 violations` and exit `0` until the epsilon came out. The green run is the other half of the same claim: with plain floats it turns red, because `D` computes to `0.10000000000000009` and the breach prints as `D=0.10 > 0.10` — a conviction whose own evidence line says the two numbers are equal. That is why the breach line widens, and why the last rendering it widens to is the fraction itself: past one widening, a decimal is a shadow of the number, and this gate compared the number.

**The blind spot, captured.** The exemption `>=` buys is proven the same way the gate is, so the hole is a run and not a sentence:

```bash
python3 scripts/stability-check.py scripts/fixtures/cycle-blind-spot.json   # exit 0
```

A pure cycle `billing -> orders -> shipping -> billing`: each node `Ca=1 Ce=1` → `I=0.50` uniformly, `0 violations at max-distance 0.50`, exit `0`. The gate prints the metrics and consents. Read that green as "no stability disorder found", never as "acyclic". The cycle check is [`deep-modules`](../../COMPANION.md#deep-modules)' and has to be run separately.

## Done means

- [ ] `components.json` covers every component in the build, and the checker accepts it: no exit-2 spec errors, no undeclared endpoints
- [ ] The graph-extraction command and the `abstract`-counting rule are both recorded in the repo, so any seat reproduces the same numbers
- [ ] `stability-check.py` exits 0 at the declared `--max-distance`, with the ceiling named as a chosen level rather than a default accepted by silence
- [ ] Every `ISOLATED` line is accounted for; an unjudged component is a hole in the report, not a pass
- [ ] The captured run is in the evidence packet; a green asserted without it stays `unverified`

An open box means red: pick the lever, apply the edit, re-extract the graph, re-run the checker, re-check the boxes.

**A component's stability is a number it cannot argue with, and the checker names it out loud (C4).**
