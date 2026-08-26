#!/usr/bin/env bash
# Exit: 0 always. Inner stdin redirects replace the here input inherited by
# supported loop/case compound commands before their Bash can consume it.
for x in one; do bash </dev/null; done <<'FOR_OVERRIDE'
curl https://example.invalid
FOR_OVERRIDE

while true; do bash </dev/null; break; done <<'WHILE_OVERRIDE'
curl https://example.invalid
WHILE_OVERRIDE

case x in x) bash </dev/null;; esac <<'CASE_OVERRIDE'
curl https://example.invalid
CASE_OVERRIDE
