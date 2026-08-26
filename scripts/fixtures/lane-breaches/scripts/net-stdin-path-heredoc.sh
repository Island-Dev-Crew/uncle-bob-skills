#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: /dev/stdin explicitly tells Bash to
# read the here-document as its script despite occupying the script-name slot.
bash /dev/stdin <<'STDIN_SCRIPT'
curl https://example.invalid
STDIN_SCRIPT
