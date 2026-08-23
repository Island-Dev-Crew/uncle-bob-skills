---
name: component-cohesion
description: Component cohesion for the agent era - the REP/CCP/CRP tension triangle plus the constraint that a component is also a context-window unit, so what changes together must fit in one agent's context together. Reach for it when drawing or redrawing component boundaries, when commits keep fanning across many components, or when someone says "component cohesion", "common closure principle", "what changes together ships together", or "this module is too big for the agent to hold". Differentiator - this island owns the cohesion triangle and the context-fit constraint layered on it; deep-modules owns the design vocabulary, interface-budget owns interface-versus-implementation token economics, stability-order owns the computed component-coupling numbers, and coupling-budget owns the budget on the coupling a change adds.
---

# Component Cohesion: what changes together must fit together

Three principles decide which classes belong in one component. They contradict each other on purpose, and the honest answer is never "satisfy all three" — it is "know which one your repo is paying for right now." The agent era adds a fourth pull that used to be invisible: **a component is also a context-window unit**, so the answer to "how big may this component grow?" is now measurable rather than felt.

Canon ground for the three principles is [`martin-canon.md`](../../research/martin-canon.md) (*Clean Architecture*, Ch. 13). Conversation quotes come only through the [concept ledger](../../01-CONCEPT-LEDGER.md). The tension *reading* below — which principle pulls which way, and what that costs at each stage — is this island's reasoning from those three definitions, not a sourced quotation, and is marked `advisory` throughout.

## The three principles and the direction each pulls

| Principle | Says | Pulls components |
|---|---|---|
| **REP** — Reuse-Release Equivalence | the granule of reuse is the granule of release | toward **releasable** — a component must be versionable and shippable as one thing |
| **CCP** — Common Closure | classes that change together belong together | toward **bigger** — absorb the co-changers so one change touches one component |
| **CRP** — Common Reuse | classes used together belong together, so no consumer is forced to depend on what it does not use | toward **smaller** — split off what only some consumers need |

CCP and CRP pull in opposite directions by construction, and REP prices whichever compromise you strike: once a boundary is published, moving a class across it costs a release. That is the triangle. There is no position that wins all three; there is only a position you chose deliberately and can defend with numbers.

## The fourth pull — the component as a context-window unit

Compartmentalisation is not a human affectation that models tolerate. It is how they work too: *"Anything that is well partitioned with well-disciplined interfaces… is something a human can grasp because we compartmentalize in our minds. Well, so do the models"* (C15). The failure mode is stated just as plainly: *"If you load up a module with every bit of stuff under the of under the sun [sic], the poor agent is going to wonder, 'What the heck am I doing in here?'"* (C15).

Two ledger facts turn that from a metaphor into a sizing rule:

- **A context window has momentum, and mixed contents contaminate it.** *"the only way to clear the trajectory is to clear the context window"* (C11). A component that bundles unrelated reasons-to-change hands every agent that opens it a pre-contaminated context.
- **Structure is what lets a model skip reading.** A small interface over a deep implementation lets an agent *"read the interface without having to understand the implementation"* (C16) — but only while the component's own working set still fits.

So CCP gets a ceiling it never had. For a human, "how big before this stops being one closure?" was bounded by comprehension, which nobody could measure, so CCP was argued rather than checked. For an agent the bound is tokens, and tokens are countable. **CCP says merge until change stops crossing boundaries; context-fit says stop merging before the component stops fitting one agent's working set.** When those two disagree, the repo has a real, computed design problem rather than a taste dispute — and the disagreement is exactly what the gate below prints.

## The stage read — which principle to favour (advisory)

| Stage | Favour | Why | What tells you you are wrong |
|---|---|---|---|
| Pre-release, the repo is its own only consumer | **CCP** | nothing is published, so REP costs nothing and CRP has no third party to over-serve — merge the co-changers | context-fit breach, or spread that never falls after merging |
| Internal platform, several in-repo consumers | **CRP** | an over-broad component forces every consumer to carry, rebuild, and *load* what it does not use | consumers importing one component for a single symbol |
| Published library, external consumers | **REP** | the boundary is now a version and a changelog; a class cannot move across it for free | breaking releases caused by internal reshuffles |
| Legacy repo under agent renovation | **context-fit, then CCP** | the spread number is the only honest map of where the boundaries actually are | agents thrashing inside one oversized component |

The stage choice is a judgment call and stays `advisory` — no mechanical check in this island picks it for you. What the gate does is make the *cost* of the choice visible: spread is the CCP bill, oversize is the context-fit bill.

## Measuring the two edges that are measurable

Two of the four pulls reduce to arithmetic over artifacts a repo already has — the commit history and the component map. [`scripts/cohesion-read.py`](scripts/cohesion-read.py) reads one TSV and gates on both:

```
commits   <TAB> total <TAB> N                # the history's own commit count
component <TAB> NAME  <TAB> SIZE_LINES       # the component map + its size
commit    <TAB> REF   <TAB> comp_a,comp_b    # one commit, the components it touched
```

- **context-fit** — no component may exceed `--context-lines` (default 1500). Derive the map rows from your component boundaries; derive sizes with `wc -l` or a token counter. A size is a whole number of at most twelve digits; a longer digit run is refused as input rather than converted.
- **CCP spread** — at most `--spread-max-pct` of commits (default 25) may touch more than `--fan` components (default 2). Derive the commit rows from `git log --name-only` folded through the same map — **one row per commit ref, carrying all its components**, never one row per path. The per-path shape is the gate's own laundering attack: it flattens every fan to 1 and inflates the denominator, turning a 75% breach into 0.0%. Two independent guards refuse it (exit 2) rather than scoring it: a ref repeated across rows, and a declared commit count that disagrees with the number of commit rows read — which catches the fold even when it mints a distinct ref per path. Derive `N` from `git rev-list --count` over the same range.
- **one entity, one key** — every component name and commit ref is compared and joined by a single documented key function: NFC-normalise, split on `/`, drop empty and `.` segments, casefold. So `API/Router.py`, `./api/router.py` and `api/router.py//` are one component, and a fan counted over three spellings of one name is 1, not 3. Two spellings *declared* separately are refused as a collision (exit 2) — never quietly merged, and never scored as separate components each sitting under the size budget. Absolute names, `..` segments, and non-ASCII names are refused outright rather than guessed at. CRLF line endings and trailing whitespace score the same as their clean twins, and one leading UTF-8 BOM — the artifact every Windows editor writes — is stripped as the encoding marker it is, so a map saved on Windows is scored rather than refused; a U+FEFF anywhere else stays in the line and is refused like any other control character.

Both budgets breach on strictly-greater, so a value sitting exactly at the budget passes, and the breach line prints the integer basis (`2501/10000 commits`) beside the rounded percent, so a percent that rounds to the budget can never look like it agrees with it. Exit codes carry distinct meanings and the gate returns no fourth: **0** clean, **1** a real verdict against real input, **2** usage/IO/malformed/empty input — and every error path exits 2, including closed stdin, closed stdout, a stdout *or* stderr pipe whose reader has gone, argparse's own usage exit, and any unexpected exception, so no IO error or crash can wear the code reserved for a verdict. Buffered output that never lands is not a rendered verdict, so a stdout write failure downgrades a 0 or 1 to 2; the gate owns its own final flush and seals an unwritable stream onto `/dev/null` so CPython's shutdown flush cannot raise and replace the status with **120**. That is the code the ordinary `… | head -1` CI idiom used to produce, silently swallowing a computed BREACH; it now yields the real verdict when the whole report fits the pipe buffer and **2** when `head` closes first, because a truncated report is not a rendered verdict. The seal is reached by converting argparse's `SystemExit` rather than re-raising it — re-raising skipped the seal, so `--help` on a dead stdout pipe and a usage error on a dead stderr pipe both exited 120 with their text still buffered. (`--help` prints usage and exits 0 when that usage text lands; that is the one 0 that is not a verdict.) A diagnostic never touches stdout either: with fd 2 closed CPython sets `sys.stderr` to `None` and `print(file=None)` falls back to stdout, filing an io-error line into the captured evidence stream, so the gate writes stderr explicitly and drops the message rather than misdirecting it. An empty, unparseable, or undecodable map cannot pass; a commit naming an undeclared component, a ref declared on more than one row, a whitespace-only row, and a comment marker anywhere but column 0 are input errors rather than quiet zeros or silently dropped rows.

What the gate **cannot** see is whether the artifact was derived honestly from the repo at all: `N` is a number you supply, so a fold that also falsifies its own declaration is a fabricated artifact rather than a naive one. Enforced is that the artifact's two counts agree; deriving them from `git` is `advisory` and belongs in the evidence rung beside the run.

Producing the map from a specific language's build files, and the budget numbers themselves, are `advisory`: tune them the way this pack tunes every threshold — by controlled runs, never by asking an agent, since *"you can't trust any debate you have with an agent"* (C18).

**Red/green proof.** The gate earns its `enforced` line by having been watched failing — the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Each check has its own dirty fixture, so neither verdict can hide behind the other. Recompute from this island's directory:

Capture each exit code on its own line (`cmd; rc=$?`) — never read `$?` after a pipe or a command substitution, both of which clobber it.

```bash
python3 scripts/cohesion-read.py scripts/fixtures/dirty-scatter.tsv    # exit 1 — BREACH CCP spread 3/4 commits (75.0%) over budget 25%
python3 scripts/cohesion-read.py scripts/fixtures/dirty-oversize.tsv   # exit 1 — BREACH context-fit, monolith 4200 lines
python3 scripts/cohesion-read.py scripts/fixtures/clean-triangle.tsv   # exit 0 — 0 over, spread exactly 25.0%
python3 scripts/cohesion-read.py scripts/fixtures/dirty-duplicate-ref.tsv  # exit 2 — input error, 'b1' declared twice
python3 scripts/cohesion-read.py scripts/fixtures/dirty-perpath-refs.tsv   # exit 2 — input error, declared 4 commits, read 10 rows
python3 scripts/cohesion-read.py scripts/fixtures/dirty-case-collide.tsv   # exit 2 — input error, 'Monolith' collides with 'monolith'
python3 scripts/cohesion-read.py scripts/fixtures/dirty-ghost-row.tsv      # exit 2 — input error, whitespace-only row is not dropped
python3 scripts/cohesion-read.py scripts/fixtures/dirty-undecodable.bin    # exit 2 — io error, undecodable map cannot pass
python3 scripts/cohesion-read.py scripts/fixtures/dirty-absurd-size.tsv    # exit 2 — input error, size is not at most 12 digits
python3 scripts/cohesion-read.py scripts/fixtures/dirty-bom-scatter.tsv    # exit 1 — the 75% breach still renders through a UTF-8 BOM
python3 scripts/cohesion-read.py 0<&-                                  # exit 2 — io error, closed stdin cannot pass
python3 scripts/cohesion-read.py scripts/fixtures/dirty-scatter.tsv >&-    # exit 2 — io error, closed stdout renders no verdict
printf '' | python3 scripts/cohesion-read.py                           # exit 2 — input error, empty map cannot pass
# stdout is a pipe whose reader is already gone — the `| head -1` shape, deterministic
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/cohesion-read.py","scripts/fixtures/dirty-scatter.tsv"],stdout=w).returncode)'   # exit 2 — io error, not 120
# stderr is a pipe whose reader is already gone, on an input-error path
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/cohesion-read.py","/nonexistent/map.tsv"],stderr=w).returncode)'                  # exit 2 — io error, not 120
# stderr closed: the diagnostic must be dropped, never redirected into the verdict stream
rm -f /tmp/cc-out.txt; python3 scripts/cohesion-read.py /nonexistent/map.tsv 2>&- 1>/tmp/cc-out.txt   # exit 2, and /tmp/cc-out.txt is 0 bytes
# argparse's own exits must reach the seal too, not re-raise past it
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/cohesion-read.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # exit 2 — usage error, dead stderr pipe, not 120
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/cohesion-read.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # exit 2 — --help text never landed, dead stdout pipe, not 120
```

`dirty-scatter` keeps every component under the size budget and `dirty-oversize` keeps spread at 0%, so each red is caused by the check it is named for. The clean fixture is deliberately built on both boundaries — `billing` at exactly 1500 lines, spread at exactly 25% — proving the gate discriminates at its budget instead of rejecting everything. The six integrity fixtures and seven IO probes watch the fail-closed path fail. `dirty-duplicate-ref` is `dirty-scatter`'s history verbatim in the per-path shape (a 75% breach that scored 0.0% before the guard existed); `dirty-perpath-refs` is the same fold with a distinct ref minted per path, which slipped past that guard and scored 0.0% until the declared count was required. `dirty-case-collide` is one 4200-line component split across three spellings of its name, each under budget, until one key joined them. `dirty-ghost-row` carries a tab-only row that used to vanish from the denominator unannounced. `dirty-undecodable` is a non-UTF-8 map that must not reach a verdict at all, and `dirty-absurd-size` carries a 4301-digit size field that used to escape `int()` as an uncaught `ValueError`. `dirty-bom-scatter` is `dirty-scatter` re-saved with a UTF-8 BOM, which used to make line 1 unparseable and turn a 75% breach into an input refusal — a real verdict lost to an encoding marker. The seven probes close the stream shapes from outside the file: `0<&-` made `sys.stdin` `None` and the `AttributeError` escaped as **exit 1** — a traceback with no verdict on stdout wearing the code reserved for a real verdict; `>&-` made `print` a silent no-op, so a BREACH exited 1 having shown nobody anything; a stdout pipe whose reader was already gone let CPython's shutdown flush override the status with **exit 120** (nondeterministically on small maps, always past 64 KB — the `| head -1` idiom), and a dead stderr pipe did the same on an input-error path; `2>&-` sent the io-error line to *stdout*, the stream "Done means" below captures as the evidence rung; and the last two are argparse's own exits, which were re-raised straight past the seal, so `--nope` on a dead stderr pipe and `--help` on a dead stdout pipe each exited **120** with their text unflushed — the same 120 the verdict paths had already closed, left open on the one path that never reached `main()`'s return. Deleting any of them returns the gate to `unverified`.

## The three repairs

A breach has exactly three moves, and the numbers say which:

1. **Merge** — two components whose commits always appear together are one closure wearing two names (spread high, both small). Merge, then re-run.
2. **Split** — a component that is over the context budget *and* appears in most spread commits is carrying several reasons to change. Split along the change axis, not the noun axis: group by which commits touch what.
3. **Move** — a class that keeps dragging its component into other components' commits belongs in one of those. Move the class, not the boundary.

Then re-run the gate. The loop ends only when the tool consents (C4) — that is the whole shape of a gate in this pack, and repairs are proposed against measurements, never against a vibe.

## Boundaries

- **[`deep-modules`](../../COMPANION.md#deep-modules) owns the design vocabulary** — depth, seam, entry points, and the deletion test — and this island never restates it. Everything here is layered *on top* of that vocabulary and adds exactly one thing to it: the agent-context-sizing rationale for how large a cohesive unit may grow. Reach for that island to decide whether a module is deep; reach for this one to decide which classes are inside it.
- **Token economics of reading an interface instead of an implementation** — what an agent must load before it may open the implementation, and the log that justifies each load — is the sibling [`interface-budget`](../interface-budget/SKILL.md). This island sizes the component; that island prices reading it.
- **Workspace and folder compartmentalisation** — how directories, worktrees, and per-agent workspaces are laid out on disk, and who gets which one — is a Forge concern this pack refuses; [COMPANION.md](../../COMPANION.md) records those refusals, and the on-disk isolation lane there is [`worktree-fleet`](../../COMPANION.md#worktree-fleet). This island partitions *code* into components and says nothing about where they live on a filesystem.
- **Dependency direction between components** — which component may depend on which, and the invert/interface/split repairs for a violation — belongs to [`dependency-fence`](../dependency-fence/SKILL.md). Cohesion decides membership; that island decides direction.
- **Component coupling metrics** — instability, abstractness, distance from the main sequence, ADP/SDP/SAP — are the `stability-order` island (roster line 21, [`02-ROSTER-50.md`](../../02-ROSTER-50.md)). *Clean Architecture* splits cohesion (Ch. 13) from coupling (Ch. 14) and so does this pack.
- **Plumbing stays plumbing** — where the gate executes belongs to [`agent-guardrails`](../../COMPANION.md#agent-guardrails), loopback and ledgers to [`archipelago`](../../COMPANION.md#archipelago), and the captured report becomes one rung of an [`evidence-packet`](../../COMPANION.md#evidence-packet) rather than a second evidence format.

## Enforced vs advisory

- `enforced` — the two verdicts and their arithmetic: [`scripts/cohesion-read.py`](scripts/cohesion-read.py) computes per-component size against the context budget and the share of commits exceeding the fan, exits 1 on either breach, and exits 2 fail-closed on every other outcome. That includes empty, malformed, undecodable and internally inconsistent input — a ref declared on more than one row, a declared commit count disagreeing with the rows read, two spellings of one name colliding under the documented key, a whitespace-only row, a size or count field too long to convert to an integer — and every IO and unexpected-exception path: closed stdin, closed stdout, a stdout or stderr pipe whose reader has gone, argparse's usage exit, and a write failure at any point, since the gate owns its final flush — converting argparse's `SystemExit` instead of re-raising it past that flush — rather than leaving it to a shutdown that would exit 120. Proven red on three verdict fixtures (one of them BOM-prefixed), six exit-2 integrity fixtures and seven IO probes, and green on the boundary-case clean one, above. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory` — every judgment around the arithmetic: which stage the repo is in and which principle to favour there, the three budget numbers, how the component map and commit rows are derived for a given language, whether the declared commit count and the component sizes were derived honestly from the repo, and which of the three repairs to apply. The gate reads an artifact; it does not audit the artifact against your `git` history. Each is written so a later wave can mechanize it; claiming any of them as enforced today would launder advisory into enforced.

## Done means

- [ ] The component map exists as an artifact — every source file assigned to exactly one named component
- [ ] Stage named, and the favoured principle named with it (CCP / CRP / REP), with the budgets that follow written down
- [ ] `cohesion-read.py` exits 0 over the map at the declared budgets, or every breach carries a chosen repair (merge / split / move)
- [ ] The captured run — stdout plus exit code — attached as an evidence rung, with the advisory budget choices stated as advisory

An open box means the verdict stays `unverified`: repair, re-run the gate, re-check the boxes.

**A component is one reason to change and one context that holds it — grow it until change stops crossing the boundary, and stop before the agent stops fitting inside.**
