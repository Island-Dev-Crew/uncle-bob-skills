---
name: dependency-fence
description: Declare which module may depend on which and how the flow runs - a tight machine-checkable fence spec of layered direction, a checker run at the end that goes red on any outward edge, and exactly three sanctioned repairs when it does (invert the dependency, insert an interface, split the module in half). Reach for it when locking a codebase's dependency direction before agents build, or on trigger phrases like 'enforce clean architecture layers', 'which module may depend on which', 'the imports flow the wrong way'. Differentiator - it owns layering DIRECTION only, as a named extension of deep-modules' dependency-cruiser lane, and ships the Clean Architecture inward-only Dependency Rule as its flagship preset.
---

# Dependency Fence: direction declared, checked, repaired three ways

Uncle Bob's fence is a deterministic tool, not a prose rule: *"define which module should depend on which, which one should not depend on which, how the dependency should flow. That goes into a nice tight little specification file that the agents cannot violate. There's another little checker that runs at the end."* (C14, [ledger](../../docs/01-CONCEPT-LEDGER.md)). This island ships that trio: the spec file, the checker, and the only three repairs allowed when the checker goes red.

## Named extension: what this island owns

This island is a named extension of [`deep-modules`](../../COMPANION.md#deep-modules)' dependency-cruiser lane, and it owns layering direction only: which layer may point at which. Entry-point rules (a package's roots are the only way in), cycle bans, and the deletion test all live in deep-modules, and are never re-shipped here. Direction can read green while an import still reaches a subfolder internal, or while two modules form a cycle inside one layer; route those to deep-modules. When an edge crosses layers the wrong way, this fence is the lane.

## The spec file: tight, declared, human-owned

`fence.json` sits at the repo root. It names the layers, ordered outermost to innermost, then maps source paths onto them by longest prefix:

```json
{
  "layers": ["frameworks", "adapters", "use-cases", "entities"],
  "modules": {
    "src/web": "frameworks",
    "src/controllers": "adapters",
    "src/use-cases": "use-cases",
    "src/domain": "entities"
  }
}
```

Writing it is the human's structural act. Bob's sequence (C12): *interrogate* the agents about the structure they see, expect to be scared, then design the module structure yourself and hand it back as a plan. The fence spec is that plan made machine-checkable. Agents run against the spec; the human owns its content (advisory, a design judgment no script can make).

## The checker: run at the end, red until repaired

[scripts/fence-check.py](scripts/fence-check.py) takes the fence spec plus a repo-internal edge list, and verdicts every edge:

```bash
python3 <this-skill-dir>/scripts/fence-check.py fence.json edges.json
```

- **GREEN (exit 0)**: every edge points inward or stays inside its own layer.
- **RED (exit 1)**: any `OUTWARD` edge, or any `UNMAPPED` endpoint. The fence fails closed, so a module missing from the spec is itself a violation, and the fix is to declare it, not to ignore it.
- Exit 2 flags a malformed spec (unknown layer, empty sections) before any edge is judged.

Produce `edges.json` with whatever extracts real import edges in your stack. For TS/JS that is dependency-cruiser, installed and invoked exactly as deep-modules specifies (pinned, local, never npx). It emits the edges directly:

```bash
node_modules/.bin/depcruise src --output-type json \
  | jq '[.modules[] | . as $m | .dependencies[] | select(.resolved | startswith("src/")) | {from: $m.source, to: .resolved}]' \
  > edges.json
```

Run the checker at the end of every agent change, and keep the agent in the loop until it consents: *"you must change the code until this tool says that it's okay"* (C4). The edge for agents cannot be argued with, only repaired.

## The three sanctioned repairs

When the fence goes red there are exactly three moves: *"inverting a dependency or inserting an interface or splitting a module in half"* (C14, Bob verbatim). Pick by symptom:

1. **Invert the dependency.** The inner module is calling outward for something it should be told about. Reverse who knows about whom: the inner side declares what it needs, the outer side supplies it (DIP, "depend in the direction of abstraction", [martin-canon](../../research/martin-canon.md)).
2. **Insert an interface.** The need is legitimate but the source edge points the wrong way. Define the port in the inner layer and implement the adapter in the outer layer. The source dependency now points inward while the call still flows outward at runtime.
3. **Split the module in half.** The module straddles two layers, so the fence flags edges into both of its faces. Cut it along the layer line and map each half to its own layer.

Editing `fence.json` to make red go green is a redesign, not a repair: it is the human's C12 act, taken deliberately in its own commit, never an agent's escape hatch.

## Flagship preset: the inward-only Dependency Rule

The four-layer spec above is the shipped preset — Clean Architecture's Dependency Rule, *"source code dependencies can only point inwards"* ([martin-canon](../../research/martin-canon.md), Clean Architecture 2017 / 2012 blog). `frameworks → adapters → use-cases → entities`, every edge pointing inward. Rename the layers to your codebase's words; keep the order and the one-way flow. Fewer layers is a legal fence, and even two, `app → domain`, is a real fence. Layers that exist only on paper are not.

## Enforced vs advisory

- **Enforced**: the direction verdict itself. Given a spec and an edge list, the verdict is mechanical and it fails closed, proven red/green against the fixture pair below rather than asserted.

### Red/green proof

Both edge lists are judged against the same [`scripts/fixtures/fence.json`](scripts/fixtures/fence.json), the shipped four-layer preset, so only the edges differ. Run from this skill directory:

```bash
python3 scripts/fence-check.py scripts/fixtures/fence.json scripts/fixtures/dirty-edges.json  # exit 1
python3 scripts/fence-check.py scripts/fixtures/fence.json scripts/fixtures/clean-edges.json  # exit 0
```

The dirty run exits 1, printing all three violations the gate can raise: two `OUTWARD` edges (`entities -> use-cases`, `use-cases -> frameworks`) and one `UNMAPPED` endpoint (`src/lib/logger.ts`). The clean run exits 0 on four edges that point inward or stay in-layer. Because the fixture is the final argument, the pair also runs under [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md)'s ritual: `prove-gate.sh scripts/fixtures/dirty-edges.json scripts/fixtures/clean-edges.json -- python3 scripts/fence-check.py scripts/fixtures/fence.json` exits 0, ACCEPTED. Re-run the pair on every change to the checker.

- **Advisory**: everything feeding the checker. Edge extraction per language, wiring the run into CI or the agent harness (this island installs no hook), the spec's fidelity to the architecture you actually want, and the choice among the three repairs. Until a hook or CI job runs the checker on every change, the end-of-loop run is a practice you keep, not a gate the machine keeps for you. Say which one your repo has.

**Ctrl-C.** A Ctrl-C (SIGINT) arriving mid-run is not a verdict. The seal maps `KeyboardInterrupt` to exit `2` — this island's non-verdict code — never to `0` or `1`, so an interrupted run cannot read as a pass or a finding. Pack policy: [CONTEXT.md — Interrupts are not verdicts](../../CONTEXT.md). A signal the interpreter never sees (`SIGKILL`, `SIGTERM`) is reported by the shell as `137`/`143` and is outside this table too.

## Done means green

The fence is standing when all four hold:

1. `fence.json` exists and the checker accepts it: no exit-2 spec errors, no unknown layers.
2. The edge-extraction command is recorded in the repo (script or docs), so any seat reproduces `edges.json` identically.
3. `fence-check.py` exits 0 on the full current edge list. The captured run is the evidence, not the claim.
4. On red: pick one of the three repairs, apply it, re-extract, re-run. Loop until green. A red left standing, or a green asserted without a captured exit-0 run, is `unverified`.

**The fence is a spec the agents cannot argue with. Red has exactly three exits, and none of them edits the spec.**
