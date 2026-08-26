---
name: proof-grammar-island
description: A fixture whose proof block carries every shape of the proof grammar at once - a bare island-relative script, a distant exit-report line, an off-allowlist command, a usage template, and a candidate with no exit code. Never distributed; exists so the extractor's classification is a captured run rather than a claim. Trigger phrases - "proof grammar fixture", "pending red test".
---

# Proof grammar island

One block, five classifications. The first four shapes were each silently dropped or
silently misread before the grammar was written down (C4).

- `enforced`: verify-proofs.py runs the two proofs, and `--strict` goes red on the PENDING.
- `advisory`: nothing else here is real.

```bash
scripts/probe.sh dirty   # exit 1
$ scripts/probe.sh clean
| PASS nothing dirty
$ echo $?   # → 0
python3 -c "import sys; sys.exit(0)"
scripts/probe.sh <mode>
true   # exit 0
```

The five, in order: a bare island-relative script with an inline code; the same script
whose code sits on a report line two lines below its output; a candidate carrying no code
at all (PENDING); a usage template with a `<placeholder>` (TEMPLATE); an off-allowlist
leading token that still states a code (SKIPPED).

Two proofs run here, so the PENDING is not the only thing `--strict` has to weigh.
[`pending-only/`](pending-only/SKILL.md) is the island where it is, and where the two answers
compete.

[`unrecognized-command/`](unrecognized-command/SKILL.md) captures the report-binding boundary:
an off-allowlist command between a candidate and an exit report is `SKIPPED`; the earlier
candidate stays `PENDING` and cannot borrow that later status.

Two narrower grammar edges sit beside it. [`bash-builtin/`](bash-builtin/SKILL.md) proves an
off-allowlist Bash builtin is the same command boundary, and
[`empty-assignment/`](empty-assignment/SKILL.md) proves an empty ordinary binding clears stale
block context rather than disappearing.

[`host-independent-command/`](host-independent-command/SKILL.md) removes the last lookup guess:
a syntactically command-shaped line owns its position whether or not that name exists on the
review host. Ambiguous shell-looking output stops report search too; `| ` marks explicit output,
and inline exit annotations are the other unambiguous form.

[`malformed-command/`](malformed-command/SKILL.md) extends that boundary to rows a shell lexer
rejects, while [`export-boundary/`](export-boundary/SKILL.md) proves a replayable export still owns
the status it produces. [`report-compound/`](report-compound/SKILL.md) requires a pure report to
end where the report grammar ends. [`comment-lexing/`](comment-lexing/SKILL.md) watches hashes
protected by ANSI-C quoting or escaped whitespace, and
[`continuation/`](continuation/SKILL.md) watches Bash's zero-byte backslash-newline removal. The
parser self-check below keeps encoded forbidden names entirely out of a subprocess while proving
hex, octal, and Unicode spellings are refused in direct commands and all four substitution forms.

The host-independence and lexer claims are executable rather than inferred from this prose:

```bash
python3 check-host-independent.py   # exit 0
python3 check-parser-regressions.py  # exit 0
```
