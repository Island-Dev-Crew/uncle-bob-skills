---
name: leak-scan
description: Detect information leakage - one design decision expressed in two or more modules - and report it as a duplicate-knowledge finding rather than a style complaint. Reach for it when a diff touches a client and a server together, when a magic constant or wire format turns up in a second file, or when the user says "leak scan", "duplicate knowledge", "this fact lives in two places", or "why did that one change need edits in two files". Differentiator - this island detects and reports leakage sites and adjudicates each one; the depth vocabulary and the churn-mined ranking of a refactor programme belong to neighbouring islands.
---

# Leak Scan: one fact, one owner

Ousterhout's classic red flag is **information leakage**: one design decision reflected in multiple modules ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). It is not duplicate *text*. Two copy-pasted helpers serving different purposes are a tidiness matter. One *fact* stated in a client and stated again in a server is leakage even when the two statements share no characters at all.

Uncle Bob's ground for why an agent fleet cares: partitioning is not a human affectation. *"Anything that is well partitioned with well-disciplined interfaces… is something a human can grasp because we compartmentalize in our minds. Well, so do the models"* (C15). A small interface lets a model *"read the interface without having to understand the implementation"* (C16). Quotes come only through the [concept ledger](../../01-CONCEPT-LEDGER.md).

## The two prices a leak charges an agent

1. **The context price.** Leakage is *the same fact paid for twice in context* ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). Every session that must be correct about the fact loads both sites, and the token budget for the actual task shrinks by the difference.
2. **The change price.** Change amplification: the fact moves, and a correct change now spans two files ([`ousterhout-debate.md`](../../research/ousterhout-debate.md)). An agent that finds one site and stops ships a half-change that compiles, passes, and is wrong.

Both prices are why leakage is reported as a knowledge defect with a blast radius, never as "duplicate code."

## The four shapes

| Shape | What it looks like | Detection today |
|---|---|---|
| Repeated literal fact | a header name, TTL, status code, queue name, or table name written out in two or more modules | **enforced**: [`scripts/leak-scan.py`](scripts/leak-scan.py) |
| Mirrored schema | the request shape declared once in client types and again in a server validator | advisory: read both, diff field by field, name the source of truth |
| Parallel dispatch | the same case list in two switch/match blocks, so adding a case means editing both | advisory: grep the case labels, count the sites |
| Re-implemented format rule | a date format, id prefix, or checksum rule coded independently per module | advisory: search for the rule's shape, not its text |

Only the first shape has a mechanical check in this island today. The other three are stated so the finding they produce has the same format, and so a later wave can mechanize them against fixtures.

## The enforced slice: scan, then adjudicate

**Report or repair — the ask decides, and it decides before the first edit.** An audit-, review- or diagnosis-shaped invocation ("leak scan this", "does this fact live in two places", "why did that one change need edits in two files") buys the *verdict*, and the verdict is the deliverable: run the scan, adjudicate every site, emit the finding fields below, stop. Exit 1 is then the answer, not a failure to be cleared, and the fix-until-green loop is not entered. Do not elect an owner, do not move a constant into another module, do not add a waiver row on the user's behalf — the proposed owner and the repair are *fields of the finding*, offered for the human's next word. Only an ask for the repair ("fix this duplicate knowledge", "give this fact one owner") opens the loop. Repairing on a scan-shaped ask is its own defect: it spends the human's review on an unrequested diff and destroys the site the scan was run to show them.

`leak-scan.py` walks the changed set, extracts string and numeric literals, and reports every literal appearing in **two or more distinct files**. The gate is not "no repeated constants". It is **no un-adjudicated repeated constant**: each one is either given a single owner or written into a waiver ledger with a reason.

```bash
python3 scripts/leak-scan.py --waivers leak-waivers.tsv src/
```

| Exit | Meaning |
|---|---|
| 0 | every cross-file literal is waived with a reason, or none exist. Also `--help`, which prints usage and computes no verdict, so a 0 is only a clean tree when the run actually scanned |
| 1 | at least one unwaived literal appears in two or more files |
| 2 | usage, IO or internal fault, fail-closed: bad path, an unreadable file **or directory**, a symlink leaving every authorized root, undecodable or malformed ledger, a stdout closed or broken (a report, a usage message or `--help` that could not be written), fewer than two comparable files, an interrupt, or an unexpected exception |
| 3 | stale waiver: the ledger waives a fact that does not leak across the scanned set |

Only 0, 1 and 3 are verdicts, and **0/1/2/3 are the only codes the script produces**. **Every fault leaves through 2**, including the ones that reach the interpreter rather than a check: a non-UTF-8 byte in the ledger, a broken pipe, a subdirectory the walk cannot read, an fd 1 already closed when the run starts, a Ctrl-C, any unhandled exception. So does the std-stream flush CPython performs at *shutdown*, which replaces the status with 120 when it raises. Argparse's usage-exit and `--help` route around any in-run handler, so the process takes its exit behind a forced flush at the bottom of the file rather than leaving that flush to the interpreter. None of these may borrow a verdict's code, because a CI consumer that reads 1 records leakage this run never computed.

**The key is the fact, not the token.** A string keys on its inner text and a number on its parsed value, so `"X-Idc-Signature"`, `'X-Idc-Signature'` and `` `X-Idc-Signature` `` are one fact, and `300`, `300.0`, `0x12C` and `3_00` are one fact. String text is NFC-normalised first. A fact written NFC in one module and NFD in the other, routine on macOS, is therefore one fact and one ledger row, the same fold the path side already applies. A quoted scalar that *is* a number folds onto that value too, so a config file's `"300"` and a module's bare `300` are one fact. That spelling matters most, because config-versus-code is where this island's own concern most often lands. Waiver keys are normalised the same way at load time, so a single ledger line covers every spelling. Comments, `/* */` blocks, Ruby `=begin`/`=end` blocks and Python triple-quoted blocks are blanked before lexing: prose *about* a fact is not a site **in any language the comment table covers**, and an `--ext .foo` outside that table gets no stripping, as the blind-spot list below says. A `#` or `//` inside a string is never a comment. One language's comment opener is another's data. PHP 8 attributes open `#[`, so PHP's `#` rule is anchored to refuse `#[` rather than deleting the line where route paths and queue names actually live.

**The floor and the ceiling are both declared.** String facts count from three inner characters; numeric facts count from two characters of their canonical decimal spelling and exclude 0 and 1. Numbers inside strings are masked before the number pass, and a number touching an identifier or a dot (`sha256`, `1.2.3`) is never a candidate. Integer spellings parse with `int()`, never `float()`, so two distinct 400-digit constants stay two facts instead of folding onto `inf`. The ceiling is 20 000 digits; past that, a token is refused as a candidate rather than crashing the floor check.

**One file is one file, whatever you call it.** Two spellings are the same file when they share `(device, inode)`, the single key the scan dedupes on. That folds letter case on a case-insensitive filesystem, Unicode NFC versus NFD, `./`, `../` and `//` segments, absolute versus relative, symlinks and hard links. Path-string comparison folds none of them, and counting one file twice reports every literal inside it as a cross-file leak. Extensions are matched case-folded for the same reason: a fact stated in `SERVER.PY` is not invisible to a `--ext .py` walk.

**The ledger cannot be pre-stuffed.** A waiver line needs a literal and a non-empty reason or the run is malformed (exit 2). A waiver for a fact that does not leak across the scanned set is stale (exit 3). Blanket-waiving a future list therefore fails the moment the repair lands. A ledger comment is a line whose first non-blank character is `#` **and that holds no TAB**. A `#` line that *does* hold a tab is ambiguous: comment, or a waiver for a fact whose text starts with `#`. So it is refused out loud (exit 2) rather than guessed at, and facts like `"#0B5FFF"` or `"# nosec"` are waived in their quoted spelling. Three more ways a row could have gone quiet are shut the same way. The ledger is read as `utf-8-sig`, so the BOM a Windows editor writes is stripped instead of riding along on row 1's key. A second row for a fact already waived, usually the same fact respelled (`300` after `0x12C`), is refused rather than overwriting the first. And a literal holding a line-breaking control character is refused, because no source literal can contain one. No data row is dropped in silence.

**Stale is scope-sensitive, and the flag says so.** "No longer leaking" is a claim about the whole tree the ledger governs. A scan of a changed pair cannot make it, because a waiver looks dead there whenever its second site was simply out of scope. The report therefore states which shape it saw: *stated in only N scanned files* versus *absent from the scanned set*. And `--no-stale` drops the question entirely for changed-set runs. Ledger honesty is then a separate run over the ledger's own tree, which is the only scan that can answer it.

**Fix until green** (C4), *entered only on a repair-shaped ask*, with exactly three repairs the scanner responds to:

1. **Elect one owner.** The fact lives in one module; the others import the symbol.
2. **Generate the second expression.** Client types and server validator are both emitted from one schema, so the second site stops being an independent statement.
3. **Waive with an authority.** The reason names who really owns the fact (an RFC, a published spec, a third-party SDK's raw-string API). A reason that names no external owner is an admission that repair 1 was skipped.

## Reporting it as a duplicate-knowledge finding

A finding is about the fact, not the file. Emit these fields and nothing that reads as taste:

- **Fact**: the decision, verbatim (`"X-Idc-Signature"`, `300` second clock skew, the seven-field event schema).
- **Sites**: every `path:line` where it is stated, from the scanner or from the read.
- **Proposed owner**: the one module that should hold it, named.
- **Repair**: which of the three above, and the import or codegen edge it creates.
- **Blast radius**: how many files a change to this fact must currently touch. That number is what makes the finding actionable to a human who does not care about style.
- **Shape and confidence**: literal (scanner-verified) or schema/dispatch/format-rule (`advisory`, read-derived). Never present a read-derived finding as scanner-verified.

Judgment calls stay judgment calls, out loud. Coincidental collisions (two unrelated modules both timing out at 30s) are closed as **not a leak** with that reason recorded. An agent's opinion about which site should own the fact is a hypothesis, never the verdict: *"you can't trust any debate you have with an agent"* (C18).

## Boundaries

- **Depth vocabulary belongs to [`deep-modules`](../../COMPANION.md#deep-modules)**. Deep versus shallow, interface width, the entry-point rules, and the deletion test are that island's. This island borrows the word *leakage* and stops; it never grades a module's depth.
- **Ranking a refactor programme belongs to [`arch-survey`](../../COMPANION.md#arch-survey)**. Churn-mined hot spots, the before/after report, and the order in which to attack them are that island's. This island detects and reports leakage sites; ordering them into a campaign is out of scope.
- **Durable capture belongs to [`finding-register`](../../COMPANION.md#finding-register)**. Anything that outlives the review is enumerated there at an exact SHA with a collision-free id. This island never defines a second register format; its report is the input to that one.

## Enforced vs advisory

- `enforced`: the repeated-literal verdict. [`scripts/leak-scan.py`](scripts/leak-scan.py) computes cross-file occurrence of each **normalised fact** (quote style and numeric spelling folded together, string text NFC-normalised, a quoted `"300"` folded onto the bare `300`, comments and docstrings blanked, integers parsed exactly) over a file set deduped by `(device, inode)` and matched on case-folded extensions. It exits 1 on any unwaived leak, 3 on any stale waiver (suppressed by `--no-stale`), and 2 fail-closed on every non-verdict outcome: bad arguments, an unreadable or undecodable ledger, an ambiguous `#`+TAB ledger line, a duplicate or control-character ledger row, an unreadable source file **or subdirectory**, a symlink whose canonical target leaves every authorized root, a stdout closed before the run or broken during it (including one that only fails at interpreter shutdown, where the status would otherwise become 120), fewer than two comparable files, an interrupt, or any unexpected exception. The island's own shape is enforced by the pack validator (`scripts/validate-island.py` at the pack root).
- `advisory`: everything the lexer cannot see. That covers mirrored schemas, parallel dispatch, re-implemented format rules, the choice of which module should own a fact, the coincidence call, the substance of a waiver reason, and the extension set the scan is scoped to. **So is the report-versus-repair routing at the head of this island**: no exit code can read the user's ask, so a run that stops at the verdict is a decision the agent states out loud, never one the gate makes for it. A directory walk skips VCS metadata and dependency/build caches (`.git`, `.hg`, `.svn`, `.venv`, `.tox`, the `*_cache` dot-directories, `__pycache__`) and walks everything else, `.github/` included. **A symlinked subdirectory too**, because the shared package a service reaches through a link is exactly where the counterpart module lives, and `os.walk`'s default skips that subtree whole and unannounced. Each directory is entered once per `(device, inode)`, so a link loop terminates on a verdict. **Inside the authorized roots only**: the canonical target of every directory walked and every file read must lie under a PATH argument or under a `--allow-root` (repeatable), and a link that leaves them all is refused by name and fail-closes 2 — never read, and never pruned in silence, since a silent prune is the same false green `followlinks` already produced once. A scan is authorized over what its caller named; documenting that links are followed is not authority to follow one out of the tree. Containment is a path test, not a sandbox: a hard link or a bind mount is a real entry inside the tree and no path test sees through it, and a `--allow-root` spelled in a different Unicode normal form than the filesystem's fails closed rather than matching. A literal split across concatenation or built at runtime is invisible to the scanner and stays a read-derived finding. So are the residual blind spots below, **an open list, not a closed set**, named rather than papered over; every unnamed one is another case the enforced check cannot see. An unquoted YAML scalar is not lexed as a string at all, so `.yaml`/`.yml` coverage is numbers and quoted strings only, and unquoted is the dominant YAML spelling, which makes a plain `queue: payments-inbound` invisible against the same string in code. Two spellings differing by escape sequence (`"a\"b"` vs `'a"b'`) do not fold. Only *canonical* Unicode equivalence folds, so a compatibility spelling (fullwidth or ligature forms, NFKC territory) is still a second fact. A template literal spanning lines is not lexed as a string. A Python triple-quoted block used as a *value* is treated as documentation and contributes no site. An extension outside the built-in comment table (`--ext .foo`) gets no comment stripping, so prose in it can still count as a site, and inside the table a comment form the table does not model (Rust's *nested* `/* /* */ */`) is stripped only to its first `*/`. A numeric token longer than 20 000 digits is refused as a candidate, so two modules restating the same absurdly long constant are invisible. **A source file that is not UTF-8 is decoded with replacement rather than refused**, so a `café` saved latin-1 arrives as `caf<0xFFFD>` and no longer matches its UTF-8 twin; `scripts/fixtures/latin1-source/` ships that hole as a *captured run* rather than a sentence, and closing it means making an undecodable **source** file the fail-closed 2 the ledger already is, which this wave does not do. And a stale verdict is only as wide as the scan: over anything narrower than the tree the ledger governs, treat exit 3 as a prompt to re-run wide, not as proof the waiver is dead.

**Red/green proof.** The scanner earns its `enforced` line by having been watched failing, the [`known-dirty-fixture`](../known-dirty-fixture/SKILL.md) ritual. Recompute from this island's directory:

```bash
python3 scripts/leak-scan.py scripts/fixtures/dirty
# exit 1 — LEAK "X-Idc-Signature" (client:5, server:5); LEAK 300 (client:14, server:8)

python3 scripts/leak-scan.py scripts/fixtures/dirty-respelled
# exit 1 — same two facts, one side `X-Idc-Signature`/0x12c in .ts, the other 'X-Idc-Signature'/300.0 in .py

python3 scripts/leak-scan.py scripts/fixtures/commented
# exit 0 — 0 cross-file literals

python3 scripts/leak-scan.py --waivers scripts/fixtures/clean/leak-waivers.tsv scripts/fixtures/clean
# exit 0 — 2 cross-file literals, 0 unwaived, 2 waivers applied, 0 stale

python3 scripts/leak-scan.py --waivers scripts/fixtures/clean/stale-waivers.tsv scripts/fixtures/clean
# exit 3 — STALE "X-Idc-Signature" waived, but stated in only 1 scanned file
```

Every fault path in that table is a captured run too, and none of them may borrow a verdict's code. Most were watched taking one before the fix: the non-UTF-8 ledger, the closed stdout and the duplicate ledger row all exited 1, the unreadable subdirectory exited 0, the subdirectory reached through a symlink exited 0, the link pointing out of the scanned root exited 1 having read and printed a file nobody named, and both argparse exits against a dead pipe exited 120. The rest, the CR and U+2028 rows, were already refusals, and are captured so a later change cannot quietly turn them into silent mis-keys:

```bash
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/non-utf8-waivers.tsv scripts/fixtures/clean
# exit 2 — a non-UTF-8 byte in the ledger is an IO fault (it used to raise UnicodeDecodeError and exit 1)
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/no-tab-waivers.tsv scripts/fixtures/clean            # exit 2
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/empty-reason-waivers.tsv scripts/fixtures/clean      # exit 2
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/duplicate-waivers.tsv scripts/fixtures/clean         # exit 2
# exit 2 — row 3 respells row 2's fact (300 after 0x12C); the first reason used to vanish silently
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/cr-waivers.tsv scripts/fixtures/clean                # exit 2
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/line-separator-waivers.tsv scripts/fixtures/clean    # exit 2
# a bare CR splits the row; a U+2028 inside the literal is refused by name — neither mis-keys in silence
python3 scripts/leak-scan.py --waivers scripts/fixtures/malformed/ambiguous-hash-waivers.tsv scripts/fixtures/hash-fact
# exit 2 — a '#' line holding a TAB is refused, not silently dropped as a comment
python3 scripts/leak-scan.py scripts/fixtures/commented >&-     # exit 2 — fd 1 closed: it used to raise a double
                                                                # AttributeError past the handler and exit 1
bash scripts/unreadable-dir-probe.sh                            # exit 0 — readable subtree 1, chmod-000 subtree 2
bash scripts/symlinked-dir-probe.sh                             # exit 0 — linked subtree 1 (it used to be 0), loop 1
bash scripts/root-escape-probe.sh                               # exit 0 — a link out of the root is refused 2 (it used
                                                                # to be 1, reading outside); --allow-root scans it, 1
bash scripts/interrupt-probe.sh                                 # exit 0 — a Ctrl-C mid-report exits 2, not 1 or 130

# The interpreter's 120 — a std-stream flush failing at SHUTDOWN — is the one fault that
# never reaches an in-run handler, because argparse exits before them. Both used to be 120:
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run(
  [sys.executable,"scripts/leak-scan.py","--nope"],stderr=w,stdout=subprocess.DEVNULL).returncode)'   # 2
python3 -c 'import os,subprocess,sys;r,w=os.pipe();os.close(r);print(subprocess.run(
  [sys.executable,"scripts/leak-scan.py","--help"],stdout=w,stderr=subprocess.DEVNULL).returncode)'   # 2

python3 scripts/leak-scan.py scripts/fixtures/hash-fact                                                          # exit 1
python3 scripts/leak-scan.py --waivers scripts/fixtures/hash-fact/hash-waivers.tsv scripts/fixtures/hash-fact     # exit 0
# "#0B5FFF" and "# nosec" are facts, and their quoted ledger rows survive the comment rule

python3 scripts/leak-scan.py scripts/fixtures/php-attribute    # exit 1 — #[Route("/api/payments/webhook")] is data, not a comment
python3 scripts/leak-scan.py scripts/fixtures/ruby-commented   # exit 0 — the =begin/=end twin of `commented`
python3 scripts/leak-scan.py scripts/fixtures/unicode-nfd      # exit 1 — one queue name, NFC in the producer and NFD in the consumer
python3 scripts/leak-scan.py --waivers scripts/fixtures/dirty/bom-waivers.tsv scripts/fixtures/dirty
# exit 0 — a BOM'd ledger still applies its two waivers (unstripped, the BOM mis-keyed row 1 and exit was 1)

python3 scripts/leak-scan.py scripts/fixtures/latin1-source     # exit 0 — LIMIT, not a pass: one file of this pair is
# latin-1, so its "café" arrives as "caf<0xFFFD>" and stops matching the UTF-8 twin. Shipped as a run so the hole is
# visible; re-encode that file UTF-8 and the same pair is exit 1, which is what `unicode-nfd` above proves in general.

python3 scripts/leak-scan.py scripts/fixtures/upper-ext        # exit 1 — QUEUE_SERVER.PY is a .py module
python3 scripts/leak-scan.py scripts/fixtures/bignum/distinct  # exit 0 — two 400-digit giants are two facts, not one inf
python3 scripts/leak-scan.py scripts/fixtures/bignum/shared    # exit 1 — a shared giant is still a leak
bash scripts/aliased-file-probe.sh                             # exit 0 — hard link, symlink, ./, //, case and NFC/NFD are one file

python3 scripts/leak-scan.py --no-stale --waivers scripts/fixtures/clean/leak-waivers.tsv \
  scripts/fixtures/clean/payment_client.py scripts/fixtures/clean/webhook_contract.py
# exit 0 — the changed pair asks only 'does this diff leak'; ledger honesty is the wide run above
```

Thirty-one runs: twenty-four over twelve fixture trees, five over the trees the probes build, two driving the script from a parent process with a dead pipe. Each proves one thing the others cannot. `dirty` is the plain restatement. **`dirty-respelled` states the same two facts with no character in common**, backtick and hex on one side, single quotes and a float on the other, so it goes red only if the key is the fact rather than the source token; a scanner keying on raw tokens passes it green. `commented` is two modules that each import their fact from the single owner and merely *name* both in an identical docstring and an identical comment. It stays green, so repair 1 above actually clears the gate and prose is not a site. `ruby-commented` is the same shape in `=begin`/`=end`, which used to go red and force an operator to choose between deleting documentation and writing a false waiver. `php-attribute` and `unicode-nfd` are two false GREENS a round-3 pass found: an attribute line eaten by the `#` rule, and one queue name spelled in two Unicode normal forms. Each is now red. The third, and the plainest, needed no exotic input at all: a service whose shared package is reached through a **symlinked subdirectory**, which `os.walk` skips whole and unannounced, so the gate returned 0 on a tree it had read only half of. `symlinked-dir-probe.sh` is that run. The `clean` tree is the dirty tree repaired. Both facts moved into `webhook_contract.py` and are imported, which is why they vanish instead of being waived, and its two surviving waivers (`"Content-Type"`, `"application/json"`) carry external owners, so it proves the gate discriminates rather than rejecting every shared string. The `stale-waivers.tsv` run proves the ledger cannot be pre-stuffed. The fault block below it is the other half of that discipline: a gate whose crashes exit 1 has been *watched* reporting leakage it never found, so each of those exit-2 runs is a hole closed rather than a sentence. `latin1-source` is the one run in the block that is **not** a pass. It is a limit, shipped so the non-UTF-8-source hole named above is a captured exit rather than a sentence. Eight runs are captured by probe, redirect or a driving parent, because a permission bit, a symlink, a closed fd, a dead pipe and a signal are not things a repo can store. `unreadable-dir-probe.sh` chmod-000s a subdirectory and asserts 2 (skipping out loud under root). `symlinked-dir-probe.sh` puts the counterpart module behind a symlinked subdirectory of the scanned root and asserts 1, then walks a link loop to prove the cycle guard terminates. `root-escape-probe.sh` is its opposite face: it points the link *out* of that root and asserts 2, because the counterpart the scan used to read and print `path:line` from was never a path the caller named, then re-runs it under `--allow-root` and asserts 1 so the refusal is containment rather than blindness (both skip out loud where symlinks cannot be made). `interrupt-probe.sh` blocks the report in an unread pipe and sends SIGINT (skipping out loud where SIGINT is ignored). The `>&-` run closes fd 1 before the process starts, and the two `subprocess` lines hand the child a pipe whose reader is already gone so the shutdown flush fails. Deleting any fixture returns the gate to `unverified`.

## Done means

These boxes belong to a **repair-shaped** ask. On a report-shaped one, done is the last two boxes only — every site adjudicated and every surviving finding handed on — with the scanner's exit reported as found rather than cleared.

- [ ] `leak-scan.py --no-stale` exits 0 over the changed set **together with the counterpart modules it talks to**, with the extension list covering every file the diff touched. A scan of fewer than two files exits 2 by design: widen the scope to the client/server or producer/consumer pair, never tick the box on a one-file run. `--no-stale` is what makes this box independent of the next one, because a changed pair cannot see whether a waiver is dead repo-wide, and asking it to would make these two boxes contradict each other. A `.yaml`/`.yml` file in that set is only half-lexed, so read its unquoted scalars by hand rather than reading a green exit as coverage of them
- [ ] Every waiver in the ledger names an external owner for its fact, and a **second run without `--no-stale`, scoped to the whole tree the ledger governs**, reports zero stale entries. That run is the only one entitled to the judgement
- [ ] The three read-derived shapes checked by hand across the diff's client/server or producer/consumer pair, each finding carrying fact, sites, proposed owner, repair, and blast radius
- [ ] Findings that outlive this review handed to the Forge finding register; the rest closed with a reason

An open box means the verdict stays `unverified`: repair (own it, generate it, or waive it with an authority), re-run the scanner, re-check the boxes.

**One fact, one owner. Every second copy is either deleted or signed for.**
