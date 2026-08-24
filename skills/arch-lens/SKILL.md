---
name: arch-lens
description: Have the agents build the repo its own drill-down architecture viewer - a small repo-local static tool that shows the modular structure as a diagram with dependency arrows, drills from module into submodules on click, and lands on the code itself. Use when a codebase has outgrown what one head holds, when an architecture conversation needs a shared picture, or when the user says "show me the architecture", "build an architecture viewer", "I want to click into the modules", or "map the dependencies visually". Differentiator - viewing and navigating only, built by the agent for this repo and generated into the working tree, never committed into a repo you were asked to visualise; ranking refactor candidates and the deletion test live in arch-survey, the module vocabulary in deep-modules.
---

# Arch Lens: the repo builds its own viewer

Have the agents build the repo its own drill-down architecture viewer, the way RCM had his: *"I also had my agents build me an architecture viewer so I can pop up on the screen a nice little UML diagram… shows me the modular structure of the system and where the dependencies run and I can click on a module and I can see inside it to the submodules… and it'll actually pop the code up on the screen"* ([C13](../../01-CONCEPT-LEDGER.md)).

The move is *agents-build-their-own-instruments*. The viewer is not a package to install. It is a small tool the agent writes for *this* repo's language and layout, and - when the human asks to keep it - commits beside the code it renders. RCM ran the same interrogation by hand: *"What's the structure here? How does this module interrelate with that module?"* (C12). A standing diagram answers that question instead of a prompt asked again every time. What the picture reveals may scare you. Deciding how to re-partition stays a human judgment (C12), and that call is made next door, per the boundary below.

## Boundary: visualization/navigation only

This island is VISUALIZATION/NAVIGATION only. Ranking refactor candidates, churn mining, and the deletion test are [`arch-survey`](../../COMPANION.md#arch-survey)'s seat. The design vocabulary — module, interface, depth, the deletion test itself — is [`deep-modules`](../../COMPANION.md#deep-modules)'s. Any "this looks shallow" observation the diagram provokes is handed to them, never judged here. Advisory - a routing rule kept by discipline; nothing blocks it mechanically.

## First, read the ask: a look, or an instrument?

Two shapes arrive at this island and they end differently. Route on what was actually asked, before anything is generated.

- **A look** - *"show me the architecture"*, *"map the dependencies visually"*, *"what does this repo look like?"* The picture and what it shows are the deliverable. Extract, check, render, walk, then put the diagram in front of the human and report what it revealed. Generated files stay in the working tree, unstaged: no `git add`, no commit, no push. **Never commit into a repo you were asked to visualise.** Four files land on disk here - `extract.*`, `graph.json`, `graph.js`, `index.html` - and a request to look authorises writing them, not entering them in someone else's history. Step 5's standing-instrument upkeep and the commit line in *Done when* are not entered on this shape; whether the lens is kept is the human's decision to make.
- **An instrument** - *"build the repo an architecture viewer"*, *"commit the lens so it regenerates"*. The repair was asked for. The whole build loop below applies, step 5 included, and the artifacts land where the next agent finds them.

Unsure which one arrived? Generate, report the four paths, and ask. RCM's viewer was something he popped up on a screen (C13); keeping it is the same class of human judgment as deciding how to re-partition (C12). Advisory - nothing here inspects the target repo's index, and the gate in the next section checks whether the graph is true, never whether it was committed.

## The deliverable (v0)

A `tools/arch-lens/` directory inside the target repo. No server, no build step, no network:

- `extract.*` is an import-graph extractor the agent writes for the repo's own language(s). It emits `graph.json` in the contract below.
- `graph.json` is the extract itself: modules as a drill-down tree, dependencies as edges.
- `index.html` is one static page, inline CSS and JS. It renders the top-level modules with dependency arrows, drills into submodules on click, and shows the file path and source when a leaf is clicked. Boxes and arrows are enough at v0; UML fidelity and layout engines are later waves. Browsers block `fetch` of local files under `file://`, so have the extractor also emit the data as `graph.js` (`const GRAPH = {…}`) and load that through a script tag.

The three artifacts travel together. What you are building is a standing instrument that regenerates as the code moves, not a one-shot screenshot. Advisory; see *Done when*.

## The graph contract

```json
{
  "modules": [
    {"id": "core", "parent": null, "path": "src/core"},
    {"id": "core.auth", "parent": "core", "path": "src/core/auth.py"}
  ],
  "edges": [{"from": "core.auth", "to": "core"}]
}
```

`id` is unique. `parent` builds the drill-down tree (`null` = top level). `path` is repo-relative, and it is the field that makes the final click land on real code. `edges` are dependency arrows at any granularity.

Enforced - [scripts/check-graph.py](scripts/check-graph.py) gates this contract with an exit code. Six things have to hold: JSON parses, ids are unique, parent chains resolve without cycles, edges resolve without self-loops, every module carries a non-empty string `path`, and, given the repo root, every `path` resolves to a real file or directory strictly inside that root (never the root itself, never escaping it). The gate ships the fixture pair that proves it can fail, so the proof is re-runnable rather than merely asserted. Run it from this island's directory (`unclebob/skills/arch-lens`):

```bash
python3 scripts/check-graph.py scripts/fixtures/dirty-graph.json scripts/fixtures/tree  # exit 1 — G3 undeclared parent, G4 self-edge, G5 pathless, G6 bad path
python3 scripts/check-graph.py scripts/fixtures/clean-graph.json scripts/fixtures/tree  # exit 0 — all six OK
```

The dirty fixture is deliberately valid JSON of the correct shape. It clears G1/G2 and goes red only on the structural checks this gate exists to catch; a fixture that failed for an unrelated reason would prove nothing. Deleting either fixture returns this gate to `unverified`.

```bash
python3 <this-skill-dir>/scripts/check-graph.py tools/arch-lens/graph.json <repo-root>   # exit 0 required
```

## Build loop: extract → check → render → walk

1. **Extract.** Write the smallest extractor that maps the repo's real import/require/include statements into `modules` + `edges`. Directories become parents; files become leaves. Advisory - at v0, whether the graph matches the code's true imports is the agent's claim, because no differ exists yet. Mark the extract `unverified` until steps 2 and 4 pass.
2. **Check.** Run `check-graph.py` with the repo root. Fix the extractor and re-run until it exits 0. Enforced - the exit code is the gate.
3. **Render.** Build `index.html` off `graph.js`, and keep it self-contained. Advisory at v0 - the suggested spot-check is `test -f tools/arch-lens/index.html && ! grep -qE '(https?:)?//[a-z]' tools/arch-lens/index.html`, which exits 0 only when the page exists and carries no absolute or protocol-relative URL. The `test -f` guard earns its keep: a bare `grep -q` reports green on a file that was never written. Stated as a command, not yet wired as a gate.
4. **Walk.** Open the page from `file://` and walk one full drill-down: top diagram → a module → a submodule → the source on screen. A failed hop is an extract or render bug. Fix it and re-walk until the whole path lands. Advisory - witnessed by human or agent eyes; state which hop was walked.
5. **Re-verify on change** (instrument shape). After the next code move, regenerate and re-run step 2. A standing instrument that has drifted red is worse than none. Enforced when run - step 2's exit code is the same gate. Advisory that anyone remembers to run it at all, until a hook or CI job schedules the regeneration.

## Done when

- `check-graph.py tools/arch-lens/graph.json <repo-root>` exits 0 (enforced).
- One full drill-down walk from the top diagram to a real source file is performed and stated (advisory).
- On the instrument shape, extractor, data, and page are committed in the target repo, so the next agent regenerates instead of rebuilding (advisory - no check inspects the target repo's index). On a look they are generated, their paths reported, and the commit is the human's call - that report closes the invocation.

**No authority without evidence. The lens shows what is; the checker says when the lens is true; what to fix about it is the neighbors' call.**
