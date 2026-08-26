#!/usr/bin/env bash
# Exit: 0 always. An inner stdin override prevents the trailing here input from
# reaching Bash even in multiline/status-negated compound forms.
(
    bash </dev/null
) <<'MULTILINE_SUBSHELL_OVERRIDE'
curl https://example.invalid
MULTILINE_SUBSHELL_OVERRIDE

! {
    bash </dev/null
} <<'NEGATED_GROUP_OVERRIDE'
curl https://example.invalid
NEGATED_GROUP_OVERRIDE

! for x in one; do
    bash </dev/null
done <<'NEGATED_FOR_OVERRIDE'
curl https://example.invalid
NEGATED_FOR_OVERRIDE
