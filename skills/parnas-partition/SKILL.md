---
name: parnas-partition
description: The decomposition criterion from Parnas 1972 - a module boundary is judged by the design decision it HIDES, never by the processing step it performs, so every proposed module must name its secret or the split is rejected. Reach for it when an agent proposes a new module, package, or file split, when a repartition plan comes back from interrogating the agents about structure, or when someone says "split this module", "where should the boundary go", "decompose by secrets", "what does this module hide", or "why does one change touch six files". Differentiator - this island owns only the question that decides WHERE a boundary goes; depth vocabulary and the deletion test, interface token economics, cohesion sizing, and duplicate-fact detection all live on neighbouring islands.
---

# Parnas Partition: a module is a secret, not a step

One criterion decides every boundary: **decompose by what a module hides, not by the processing steps it performs.** That is Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules," CACM 15(12), 1972, the origin of information hiding, recorded in [`seventies-canon.md`](../../research/seventies-canon.md). Its operational form is the whole of this island's concern:

> **A proposed module that cannot name the design decision it conceals is not a module. Reject the split and ask again.**

Ask "what does this do?" and every pile of code has an answer. Ask instead: *what could change inside here without anyone outside noticing?* If the honest answer is *nothing*, you drew a step, not a secret. You bought a boundary that charges maintenance rent and pays no interest.

## The agent-era sharpening

Parnas wrote for humans holding a design in their heads. The criterion binds harder now, for a reason Bob states directly about models: *"Anything that is well partitioned with well-disciplined interfaces… is something a human can grasp because we compartmentalize in our minds. Well, so do the models"*. He is just as direct about the failure mode when you don't: *"If you load up a module with every bit of stuff under the of under the sun [sic], the poor agent is going to wonder, 'What the heck am I doing in here?'"* (C15, quoted through [the ledger](../../docs/01-CONCEPT-LEDGER.md); all conversation quotes on this island come that way, never from memory).

The research brief draws the consequence explicitly. Modules whose internals are hidden *are exactly the modules an agent can regenerate without cascading breakage*, and the module boundary is the natural context-window boundary ([`seventies-canon.md`](../../research/seventies-canon.md)). So a secret is three things at once:

1. *A blast radius.* The secret marks what may be rewritten. Hand an agent a module whose secret is "the on-disk layout of the spool" and it may replace every byte of it. Hand it "step 3 of ingest" and it cannot change anything without first asking what step 4 assumed.
2. *A context boundary.* The secret is the reason a caller never needs to load the body. The body is, by construction, the part nobody outside is entitled to know.
3. *A regeneration unit.* A module with a stated secret can be thrown away and rebuilt from its interface plus that one sentence. A module without one can only be edited.

This is also the missing half of the human design step Bob refuses to automate. He interrogates the agents, gets *"scared to death because the answers were horribly frightening"*, and then *"I would design a module structure… and give them an implementation plan"* (C12). Interrogating and re-partitioning is [`structure-interrogation`](../structure-interrogation/SKILL.md)'s seat. **This island supplies the criterion that design step applies.**

## The two decompositions, side by side

| | Decomposed by *step* | Decomposed by *secret* |
|---|---|---|
| Module name reads like | `parse`, `validate`, `transform`, `stage-2` | `spool-store`, `wire-codec`, `retry-policy` |
| Interface is | whatever the next step needs next | the smallest set of operations a caller can want |
| A change to the data format | ripples through every step that touched it | stops at one module |
| An agent can regenerate it | no, it must first learn what its neighbours assumed | yes, from the interface and the secret |
| The honest hidden decision | "the order we happen to do things in" | one nameable design decision |

Three signatures give away a step decomposition whatever the folder names say: one feature edit touches every module in a row; the modules can only be understood in sequence; and no module can be described without naming another.

## The declaration rule

Every module carries exactly one row in a **secrets manifest**, a TSV of `module-path TAB the design decision it hides`:

```
src/spool	the on-disk layout of the staged upload spool
src/store	whether a record lives in SQLite or in the object store
src/wire	the JSON envelope version negotiated with the client
```

A declaration earns its place when it names a decision that could plausibly have gone the other way. `"whether a record lives in SQLite or in the object store"` names an alternative. `"the store"`, `"TODO"`, `"handles storage"` name nothing. They restate the folder name, and a module whose secret is its own name has no secret.

Two modules that hand you the *same* sentence are not two modules. That is one decision expressed twice, which is [`leak-scan`](../leak-scan/SKILL.md)'s finding, not this island's.

## The gate: declaration only

[`scripts/secret-manifest.py`](scripts/secret-manifest.py) refuses a module list unless every module on it carries a non-duplicated, non-placeholder declaration holding at least `--min-chars` **substantive** characters (default 12). It checks four things and no fifth: **presence, at-most-one manifest row per module, minimum length, and non-placeholder form. Never its truth.**

A *substantive* character is a Unicode letter or digit, counted after NFC normalization, minus the four Hangul fillers U+115F, U+1160, U+3164 and U+FFA0, which are category `Lo` and satisfy `\w` while rendering as blank. Dots, the `_` character, combining marks and format characters (U+200B) are length, not substance. **A declaration whose substance count is zero is refused unconditionally, at every value of `--min-chars` including 0**, exactly like an empty one, because that is what it is.

Placeholders are caught in two shapes from one shared vocabulary, so the two rules cannot drift apart. *Bare* (the whole declaration): `todo`, `tbd`, `tba`, `tbc`, `fixme`, `xxx+`, `wip`, `n/a`, `placeholder`, `unknown`, `undecided`, `undetermined`, `unspecified`, `undocumented`, `pending`, `later`, `none`, `null`, `nil`, a run of `?` or of `-`. *Marker-plus-text* (the declaration *opens* with it): the hard stubs `todo|tbd|tba|tbc|fixme|xxx+|wip` on a word boundary alone; the spelled-out stubs `to be <determined|decided|confirmed|defined|specified|documented|written|known|named|chosen|settled|picked|filled [in]|figured out|sorted out|worked out|nailed down>` and `not [yet] <same list>`, each of which an optional leading `still` also guards; and the soft markers `placeholder|unknown|undecided|undetermined|unspecified|undocumented|pending|later|n/a` **only when an end of phrase or a "not yet" tail follows**. So `unknown at this time` is refused, while `Later-binding of the codec dispatch table` and `N/A handling in the CSV importer` are not. That guard is why the marker set can be this wide without inventing false reds.

Both rules run twice: once against the declaration as written, once against an NFKC-normalized copy with the separator punctuation `.` `-` `_` `·` stripped out. `T.B.D.`, `T-B-D` and fullwidth `ＴＯＤＯ` therefore meet the same rules as `tbd` and `TODO`. The copy is tested, never substituted, so the fold can only add refusals.

Whether the named decision is really hidden, really a decision, or really the right one is human judgment, and is marked `advisory` below. The gate is deliberately thin so that it is honest.

Exit codes: `0` every listed module declares a secret, or `--help` on a live stdout · `1` at least one is undeclared, empty-declared, declared with zero substantive characters, placeholder-declared, short of `--min-chars` substantive characters, or declared twice · `2` usage error, unreadable or non-UTF-8 input, a malformed row, an empty module list, an ambiguous module key, a module path of `.` (it normalizes to nothing), a failed output flush, a stream missing entirely because its fd was closed before launch (`cmd 1>&-`), or any internal failure.

**No error this gate can produce wears a verdict's code.** Every one of them lands on 2. One branch is narrower than that sentence would be if left absolute, and is named here rather than implied: the mandated shutdown seal maps a `SystemExit` carrying a *non-integer* code to `1`. `argparse` raises only integer statuses and this script never calls `sys.exit` with a string, so no input reaches that branch. The seal is used verbatim, as the pack requires it.

Keys are normalized once, through one documented function: strip surrounding blanks, NFC-normalize, drop `.` segments, resolve `..` textually, collapse `//`, strip one trailing `/`. Letter case is *not* folded and absolute is *not* conflated with relative, so a spelling variant fails to join and reads as *undeclared*, which refuses rather than consents. Two different raw paths *in the module list* that collapse to one key are an ambiguity the gate will not resolve, and exit `2`; two manifest rows that collapse to one key are a duplicate declaration, and exit `1` when that module is on the list.

### Red / green proof (run from this island's directory)

```bash
G=scripts/secret-manifest.py
python3 $G --manifest scripts/fixtures/green/manifest.tsv --modules scripts/fixtures/green/modules.txt            # exit 0
python3 $G --manifest scripts/fixtures/red/manifest.tsv --modules scripts/fixtures/red/modules.txt                # exit 1
python3 $G --manifest scripts/fixtures/ambiguous/manifest.tsv --modules scripts/fixtures/ambiguous/modules.txt    # exit 2
python3 $G --manifest scripts/fixtures/empty-list/manifest.tsv --modules scripts/fixtures/empty-list/modules.txt  # exit 2
python3 $G --manifest scripts/fixtures/malformed/manifest.tsv --modules scripts/fixtures/malformed/modules.txt    # exit 2
python3 $G --manifest scripts/fixtures/green/manifest.tsv --modules scripts/fixtures/nope.txt                     # exit 2
python3 $G --manifest scripts/fixtures/todo-prefix/manifest.tsv --modules scripts/fixtures/todo-prefix/modules.txt # exit 1
python3 $G --manifest scripts/fixtures/no-substance/manifest.tsv --modules scripts/fixtures/no-substance/modules.txt              # exit 1
python3 $G --manifest scripts/fixtures/no-substance/manifest.tsv --modules scripts/fixtures/no-substance/modules.txt --min-chars 0  # exit 1
python3 $G --manifest scripts/fixtures/spelled-placeholder/manifest.tsv --modules scripts/fixtures/spelled-placeholder/modules.txt  # exit 1
python3 $G --manifest scripts/fixtures/idiom-swap/manifest.tsv --modules scripts/fixtures/idiom-swap/modules.txt  # exit 1
python3 $G --manifest scripts/fixtures/filler-letters/manifest.tsv --modules scripts/fixtures/filler-letters/modules.txt            # exit 1
python3 $G --manifest scripts/fixtures/filler-letters/manifest.tsv --modules scripts/fixtures/filler-letters/modules.txt --min-chars 0  # exit 1
python3 $G --manifest scripts/fixtures/honest-soft/manifest.tsv --modules scripts/fixtures/honest-soft/modules.txt  # exit 0
python3 $G --manifest scripts/fixtures/dot-root/manifest.tsv --modules scripts/fixtures/dot-root/modules.txt        # exit 2
python3 $G --manifest scripts/fixtures/green/manifest.tsv --modules scripts/fixtures/green/modules.txt 1>&-        # exit 2
```

The `green` fixture is deliberately hostile. Its manifest carries a UTF-8 BOM, CRLF line endings, a comment line, a path beginning with `#`, and a module name spelled NFD while the module list spells it NFC (macOS hands you both routinely), plus `./src/store/` against a declared `src/store`. Exit 0 there is the normalization proving itself, not leniency.

The `red` fixture fails for four separate reasons, printed by name: `src/auth` is undeclared *because the manifest spells it `src/Auth`* (case is not folded), `src/wire` is declared `TODO`, `src/store` is declared `SQLite` (6 substantive characters), and `src/report` is missing outright.

Five more fixtures watch the rules a bare-marker check alone would miss. `todo-prefix` declares three modules `TODO: decide the on-disk layout`, `TBD - waiting on review from Dana`, and `FIXME later, this is the spool format`, which is the stubbed-manifest form a real engineer writes, and all three are refused by name. `spelled-placeholder` is that same stub in ordinary English rather than in markers: `to be determined`, `placeholder, fill this in later`, `not yet decided, ask the architect`, `unknown at this time`. All four are refused.

`idiom-swap` is the third turn of that screw, and the one this island got wrong first. Six declarations respell markers the vocabulary already names: a leading `still` in front of `to be determined`, `To be confirmed with the storage team`, `T.B.D.` and `T-B-D` with the dots and hyphens doing the hiding, a bare `TBC`, and a fullwidth `ＴＯＤＯ`. Every one of the six was exit 0 until the fold and the two vocabulary additions above landed; all six are refused now. What still passes is the class named under the second disclosed limit below, plus any respelling the fold does not reach. The fold removes `.`, `-`, `_`, `·`, the non-breaking hyphen and whitespace, and the stub words match a trailing plural, so `to-be-determined`, `TODOs`, `T B D`, `T‑B‑D` and a `yet`-led stub are all refused. A respelling that hides behind some other separator, or behind a synonym the vocabulary does not name, is not.

`no-substance` declares one module twelve dots, one twelve U+200B (category `Cf`, which `strip()` leaves in place), and one nothing at all. `filler-letters` is the harder version: twelve U+3164 HANGUL FILLER, twelve copies of `_`, and six U+115F/U+1160 pairs, all of them `\w` characters, all of them blank on screen. Every row of both fixtures exits 1 at `--min-chars 0` as well as at the default, because zero substance is refused unconditionally.

`honest-soft` is the false-red control that keeps the wide marker set honest: `Later-binding of the codec dispatch table`, `NAT traversal strategy used for peer connections`, `Pending-writes buffering policy for the upload spool`, and `placeholder rendering used while a photo is still loading` all pass. `dot-root` proves a bare `.` row is a usage error by design, not a module: it normalizes to nothing and exits 2.

A verdict nobody can read is not a verdict. With fd 1 closed before launch, `print()` returns silently and the flush loop has nothing to fail on, so the gate checks for a missing stream directly and exits 2 rather than reporting a green into the void.

An exception is not a verdict either. Both dead-pipe probes exit 2, never 120:

```bash
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/secret-manifest.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # exit 2
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);sys.exit(subprocess.run([sys.executable,"scripts/secret-manifest.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'    # exit 2
```

### Disclosed blind spot

Manifest rows for modules *not* on the list are ignored, so a declaration left behind by a deleted module passes. Captured rather than hidden, in the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) spirit, because an evidenced boundary beats a silent one:

```bash
python3 scripts/secret-manifest.py --manifest scripts/fixtures/stale-blind-spot/manifest.tsv --modules scripts/fixtures/stale-blind-spot/modules.txt   # exit 0
```

`src/deleted-cache` is declared and gone, and the run is green. Pair the gate with a module list generated from the tree you actually have, so the list, not the manifest, defines the universe. The list must hold *module directories only*. A bare `.` row is a usage error and exits 2, which is why the `git` recipe filters it out (`dirname` emits `.` for every file at the repo root):

```bash
ls -d src/*/
git ls-files | xargs -n1 dirname | sort -u | grep -v '^\.$'
```

**A second disclosed limit: placeholder detection is lexical, and the vocabulary above is finite.** A stub phrased outside it passes, captured, not hidden:

```bash
python3 scripts/secret-manifest.py --manifest scripts/fixtures/soft-marker-limit/manifest.tsv --modules scripts/fixtures/soft-marker-limit/modules.txt  # exit 0
```

`pending a decision from the architect` and `ask Dana what this hides` are both green. No lexical rule closes this, and none is claimed to. Whether a declaration says anything is the human judgment marked `advisory` below.

## Enforced vs advisory

- `enforced`: declaration **presence, at-most-one manifest row per module, minimum substantive-character length (with zero substance refused unconditionally), and non-placeholder form (bare marker, marker-plus-text, the spelled-out stub idioms named above, and the separator-stripped, NFKC-folded respellings of all three)** for every module on the supplied list. That is `secret-manifest.py`, exit-code gated, red/green/error proven above. Its two disclosed limits, stale manifest rows and stubs phrased outside the marker vocabulary, each ship as a captured exit-0 fixture.
- `enforced`: this island's own shape, checked by the pack validator [`../../scripts/validate-island.py`](../../scripts/validate-island.py), twelve mechanical checks.
- `advisory`: **everything that matters most.** Whether a declared secret is true; whether it is a design decision rather than a restatement of the module's name; whether the decomposition is by secret or by step; whether the module list handed to the gate is complete. No checker on this island judges any of these, and none is claimed to. A green run means *the sentences exist*, not *the partition is right*.
- `advisory`: the three consequences of a secret (blast radius, context boundary, regeneration unit), the three step-decomposition signatures, the two-decompositions table, and the "could it have gone the other way?" test for a declaration. These elaborate the brief's one sourced sentence. They are reasoning from the criterion, not sourced quotation.

## Boundaries: who owns what

- *Depth and seam vocabulary, and the deletion test* belong to [`deep-modules`](../../COMPANION.md#deep-modules) and are never restated here. That island answers *how deep is this module, and is the seam clean?*; this island answers only *where does the boundary go?* A module can be deep and still be a step, and this criterion is what catches it.
- *The token economics of reading an interface*, what a module costs to use and the ledger of justified implementation loads, is [`interface-budget`](../interface-budget/SKILL.md)'s seat. This island says a secret makes the body unnecessary to read; pricing that in tokens is there.
- *Cohesion principles*, REP, CCP, CRP, and sizing a component to a context window, are [`component-cohesion`](../component-cohesion/SKILL.md)'s seat. Cohesion asks *what belongs together*; this island asks *what stays hidden*. They disagree usefully and neither absorbs the other.
- *The same fact expressed twice* across modules is [`leak-scan`](../leak-scan/SKILL.md)'s finding. This island rejects an undeclared split; that island rejects two splits sharing one declaration.
- *Ranking which existing boundaries to fix*, churn mining and before/after refactor reports, is [`arch-survey`](../../COMPANION.md#arch-survey)'s seat. This island judges a proposed boundary, one at a time.
- *Justifying the cross-module imports a split produces* is [`coupling-budget`](../coupling-budget/SKILL.md)'s seat. This island judges whether the boundary should exist; that one prices the edges it adds.

## Done when

- [ ] Every module in the change carries one manifest row naming a decision that could have gone the other way.
- [ ] `secret-manifest.py` exits 0 against a module list generated from the tree, not hand-written.
- [ ] Any module whose only honest answer was "step N of the pipeline" was merged away or re-cut, and the rejection is recorded.
- [ ] No two modules were declared with the same secret (send that to `leak-scan`).
- [ ] The declarations a human accepted as *true* are marked as a human judgment, because the gate did not check that.

**No authority without evidence. Name the decision the module hides, or you have not drawn a module: you have drawn a step and called it architecture.**
