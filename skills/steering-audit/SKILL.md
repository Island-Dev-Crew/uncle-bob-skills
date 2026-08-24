---
name: steering-audit
description: Audit a standing prompt (CLAUDE.md, AGENTS.md, a system prompt) into a before/after rule inventory. Every rule is classified generative (must shape generation, stays in the priority zone) or checkable (has a mechanical test, migrates out into a deterministic gate), because steering decays and gates do not (C3, C4). Use when a rules file has grown past trust, when hardening an agent fleet's prompts, or when the user says "audit my CLAUDE.md", "my agent ignores its rules", or "move rules into hooks". Differentiator - it owns only the classification and the migration; hook and denylist mechanics belong to agent-guardrails, tool-vs-model routing to model-routing, prompt wording to writing-for-agents.
---

# Steering Audit: guidelines out, gates in

A grown standing prompt is obeyed "in the Pirates of the Caribbean sense. They're more like guidelines" (C3). The cause is positional, not moral. Attention over a long context traces a U-curve: strong at the head, strong at the tail, weak in the middle. So "the 50th and the 80th sentence in there, they're gone" (C3; evidence in [lost-in-the-middle](../../research/lost-in-the-middle.md)). A deterministic tool in a loop has no middle: "you must change the code until this tool says that it's okay" (C4). That holds at rule 1 and rule 80 alike. This island audits one standing prompt (CLAUDE.md, AGENTS.md, a system prompt) and moves every rule to the side of that line where it survives: "trim that initial prompt down to its absolute minimum … and then do deterministic tools after the fact" (C3).

## The two destinations

- **Generative** rules shape the words as they are produced: identity, voice, architecture intent, priorities, style direction, what-to-reach-for-when. No artifact check substitutes for them, because by the time an artifact exists the shaping moment is over. These stay in the prompt, inside the head-of-context priority zone.
- **Checkable** rules have a mechanical test over the finished artifact: format, lint, types, tests, complexity caps, file-size caps, naming patterns, secret scans, commit-message shape. Each migrates out into a deterministic gate the agent loops against (C4), and its prompt line is deleted in the same change that lands the gate.

Litmus (advisory): write the one-line command that would check the rule against the finished work. If you can write it and it can exit non-zero, the rule is checkable. If the only checker is "a model re-reads and judges", the rule is generative. Whether that judging step deserves a model at all is a routing call this island cedes (see Boundaries).

Classify to the strictest destination a rule supports. A rule that is half vibe, half measurable ("keep functions small and readable") splits in two: a checkable half (a max-lines gate) and a generative remainder, each with its own row.

## The audit

1. **Inventory before.** Save a before-copy first. Audit ids stay bound to it, because step 3 deletes lines and any later extraction renumbers:
   ```bash
   cp <prompt.md> <prompt.before.md>
   python3 scripts/inventory.py extract <prompt.before.md>   # R<n>, line, text per candidate rule
   ```
   It emits every markdown list item outside code fences, deterministically. Prose rules that live in paragraphs are invisible to it. Add those by hand as extra rows (advisory: the extractor is a floor, never the ceiling).
2. **Classify every rule** with the litmus. Every row gets `generative` or `checkable`. "Unsure" is not a destination: an unsure rule is generative until a checker for it exists.
3. **Migrate the checkables.** For each, name the concrete gate: a pre-commit step, a CI check, a linter rule, a validator script. Wiring hooks and denylists is [agent-guardrails](../../COMPANION.md#agent-guardrails)' concern. Name the gate here, build it there. Prove a new gate can go red against a known-bad input before its prompt line dies; the sibling [known-dirty-fixture](../known-dirty-fixture/SKILL.md) island owns that discipline. A checkable rule whose gate does not exist yet is marked `pending` and *stays in the prompt* until the gate lands. Delete steering with no gate in place and you lose the rule entirely.
4. **Rewrite what stays.** The surviving generative rules go to the head of the file, worded per [writing-for-agents](../../COMPANION.md#writing-for-agents). The doc-level levers (leading words, pruning, no-ops, negation) are its property, not restated here.
5. **Verify.** Check the audit against the *before-copy*, never the rewritten prompt. Surviving rules renumber, and a renumbered prompt can false-green against the wrong audit rows:
   ```bash
   python3 scripts/inventory.py check <prompt.before.md> <audit.md>   # exit 0 iff every before-inventory id sits on an audit line carrying 'generative' or 'gate'
   ```
   Non-zero exit lists the unaccounted rules. Classify them and rerun until green.

## The deliverable

One before/after inventory table, every rule a row:

| id | line | rule (abridged) | class | destination | status |
|---|---|---|---|---|---|
| R1 | 41 | functions under 50 lines | checkable | gate - lint max-lines-per-function, pre-commit | enforced |
| R2 | 58 | prefer editorial layouts over template grids | generative | prompt (priority zone) | advisory |
| R3 | 102 | no hardcoded secrets | checkable | gate - secret scanner in CI | pending (rule stays in prompt until the gate lands) |

The status column applies the evidence discipline per rule. `enforced` only where the named gate exists today and blocks. `pending` where a gate is named but has not landed. Generative rows are `advisory` by nature — the prompt asks, it cannot make.

## Boundaries

This island owns the classification and the migration of rules, and nothing else. It cedes:

- **Tool-vs-model routing decisions** to [model-routing](../../COMPANION.md#model-routing). When a "checker" would itself be a model call, whether that clears a cost floor is its call, not this island's.
- **Hook and denylist mechanics** to [agent-guardrails](../../COMPANION.md#agent-guardrails). This audit names which gate a rule migrates into. How a hook is wired, what a denylist blocks, and the four guardrail layers all live there.
- **Doc-level writing levers** stay with [writing-for-agents](../../COMPANION.md#writing-for-agents). How the surviving generative rules are worded, pruned, and pointed is its single source of truth.

The head-of-context token budget itself (how small the priority zone must be, position lints) belongs to the sibling [priority-zone](../priority-zone/SKILL.md) island. This island decides *which* rules deserve that zone, not how big the zone is.

## Enforced vs advisory

- `enforced`: `scripts/inventory.py extract` is deterministic (same prompt, same rows), and `check` exits non-zero while any extracted rule id lacks an audit line carrying a destination. Verify against the shipped fixtures: `python3 scripts/inventory.py check scripts/fixtures/prompt.md scripts/fixtures/audit-missing-row.md` must exit 1 (R3 unaccounted), and the same check against `scripts/fixtures/audit-complete.md` must exit 0. The validator (`../../scripts/validate-island.py`) mechanically gates this island's shape.
- `advisory`: the extractor's candidate set (prose rules must be hand-added), the generative-vs-checkable judgment itself, the litmus, and the split rule. v0 is honest about this. Classification is a judgment call with a mechanical completeness check around it, not a mechanical classification.

## Done when

- Every row of the before-inventory carries a class, a destination, and a status. The mechanical slice: `inventory.py check <prompt.before.md> <audit.md>` exits 0, proving destination presence per before-inventory id (enforced). Class and status *correctness* have no mechanical check (advisory).
- Every `checkable + enforced` row's prompt line is deleted, and every deletion landed in the same change as its gate (advisory: verify by diff).
- No row is status `enforced` without a gate that exists and can go red today (advisory).

Loop until all three hold: classify → migrate → `check` → fix → recheck.

**No authority without evidence. Steering decays; the gate never does — leave in the prompt only what must shape generation.**
