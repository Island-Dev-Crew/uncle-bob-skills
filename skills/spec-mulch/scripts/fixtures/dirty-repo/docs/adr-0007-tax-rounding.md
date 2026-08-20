# ADR-0007 — checkout tax rounds half-up at two decimals

Status: accepted (story-17)

Why: bankers' rounding drifted a cent against the payment processor on split
shipments, and the mismatch surfaced as failed captures.

The story spec that carried this decision was scaffolding. It was marked

`MULCH-ON-MERGE: story-17`

and is deleted on merge. This ADR is the one prose survivor — the behavior
itself lives in the Gherkin scenarios and the rounding unit tests.
