#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: trailing here input is inherited by a
# literal Bash in each supported loop/case compound command.
for x in one; do bash; done <<'FOR_HEREDOC'
curl https://example.invalid
FOR_HEREDOC

while true; do bash; break; done <<'WHILE_HEREDOC'
curl https://example.invalid
WHILE_HEREDOC

until false; do bash; break; done <<'UNTIL_HEREDOC'
curl https://example.invalid
UNTIL_HEREDOC

case x in x) bash;; esac <<'CASE_HEREDOC'
curl https://example.invalid
CASE_HEREDOC

select x in one; do bash; break; done <<'SELECT_HEREDOC'
1
curl https://example.invalid
SELECT_HEREDOC
