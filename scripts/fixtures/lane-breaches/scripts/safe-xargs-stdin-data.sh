#!/usr/bin/env bash
# Exit: 0 always. Ordinary xargs consumes stdin as argv input and does not pass
# that same here payload to a Bash child as its program.
xargs bash <<'XARGS_HEREDOC'
curl https://example.invalid
XARGS_HEREDOC

xargs bash <<< 'curl https://example.invalid'

xargs -a /dev/stdin bash <<'XARGS_DEV_STDIN'
curl https://example.invalid
XARGS_DEV_STDIN

xargs cat <<'XARGS_CAT_PIPE' | bash
curl https://example.invalid
XARGS_CAT_PIPE

xargs cat <<< 'curl https://example.invalid' | bash
