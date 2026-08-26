#!/usr/bin/env bash
# Exit: 0 always. Green controls: only the last standard-input redirection is
# active, so neither curl-bearing here-document becomes the shell's program.
bash <<'OVERRIDDEN' <<'ACTIVE'
curl https://example.invalid
OVERRIDDEN
:
ACTIVE

bash <<'OVERRIDDEN_BY_FILE' < /dev/null
curl https://example.invalid
OVERRIDDEN_BY_FILE

bash <<'OVERRIDDEN_BY_CLOSED_FD' 0<&-
curl https://example.invalid
OVERRIDDEN_BY_CLOSED_FD
