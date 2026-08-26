#!/usr/bin/env bash
# Exit: 0 always. An inner stdin redirect overrides a compound command's inherited
# here input, and a preceding transparent consumer drains it before a later Bash.
{ bash </dev/null; } <<'GROUP_OVERRIDE'
curl https://example.invalid
GROUP_OVERRIDE

( bash </dev/null ) <<'SUBSHELL_OVERRIDE'
curl https://example.invalid
SUBSHELL_OVERRIDE

{ cat >/dev/null; bash; } <<'GROUP_DRAIN'
curl https://example.invalid
GROUP_DRAIN

{ bash </dev/null; } <<< 'curl https://example.invalid'
( bash </dev/null ) <<< 'curl https://example.invalid'
{ cat >/dev/null; bash; } <<< 'curl https://example.invalid'
