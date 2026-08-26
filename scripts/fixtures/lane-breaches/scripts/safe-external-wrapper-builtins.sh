#!/usr/bin/env bash
# Exit: 0 always. External wrappers cannot invoke shell-only builtin names;
# their later network-shaped words are data, not executable shell syntax.
env source /dev/stdin <<'ENV_SOURCE_DATA'
curl https://example.invalid
ENV_SOURCE_DATA
nohup eval 'curl https://example.invalid'
nice builtin command curl https://example.invalid
stdbuf trap 'curl https://example.invalid' EXIT
command time eval 'curl https://example.invalid'
/usr/bin/command time eval 'curl https://example.invalid'
:
