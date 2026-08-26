#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: when xargs reads argv from another
# file, its Bash child inherits the command's untouched here input as a program.
xargs -a /dev/null bash <<'XARGS_ALT_HEREDOC'
curl https://example.invalid
XARGS_ALT_HEREDOC

xargs --arg-file=/dev/null bash <<< 'curl https://example.invalid'

xargs -a /dev/null cat <<'XARGS_ALT_CAT_PIPE' | bash
curl https://example.invalid
XARGS_ALT_CAT_PIPE

xargs --arg-file=/dev/null cat <<< 'curl https://example.invalid' | bash
