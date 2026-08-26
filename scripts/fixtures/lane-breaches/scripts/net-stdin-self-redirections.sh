#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: a later self-duplication or standard-
# input self-path preserves the here payload that Bash executes as its program.
bash <<< 'curl https://example.invalid' <&0
bash 0<<< 'curl https://example.invalid' 0<&0
bash <<< 'curl https://example.invalid' 0>&0

bash <<'HEREDOC_SELF_DUP' <&0
curl https://example.invalid
HEREDOC_SELF_DUP

bash <<'HEREDOC_DEV_STDIN' </dev/stdin
curl https://example.invalid
HEREDOC_DEV_STDIN

bash <<'HEREDOC_DEV_FD' </dev/fd/0
curl https://example.invalid
HEREDOC_DEV_FD
