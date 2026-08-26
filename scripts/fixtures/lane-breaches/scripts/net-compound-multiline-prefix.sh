#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: multiline subshells and status-negated
# compounds still inherit their trailing here input.
(
    bash
) <<'MULTILINE_SUBSHELL'
curl https://example.invalid
MULTILINE_SUBSHELL

! {
    bash
} <<'NEGATED_GROUP'
curl https://example.invalid
NEGATED_GROUP

! for x in one; do
    bash
done <<'NEGATED_FOR'
curl https://example.invalid
NEGATED_FOR
