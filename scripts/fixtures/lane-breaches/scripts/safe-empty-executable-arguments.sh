#!/usr/bin/env bash
# Exit: 0 always. An empty executable or -c program does not promote a later
# curl-shaped data argument into command position.
bash -c '' curl
command '' curl
env '' curl

'' bash <<'EMPTY_DIRECT_COMMAND'
curl https://example.invalid
EMPTY_DIRECT_COMMAND

command '' bash <<'EMPTY_WRAPPED_COMMAND'
curl https://example.invalid
EMPTY_WRAPPED_COMMAND

env '' bash <<'EMPTY_ENV_COMMAND'
curl https://example.invalid
EMPTY_ENV_COMMAND

nohup '' bash <<'EMPTY_NOHUP_COMMAND'
curl https://example.invalid
EMPTY_NOHUP_COMMAND

nice '' bash <<'EMPTY_NICE_COMMAND'
curl https://example.invalid
EMPTY_NICE_COMMAND
