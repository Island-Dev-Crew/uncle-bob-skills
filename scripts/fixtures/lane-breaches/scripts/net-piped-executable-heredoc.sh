#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: cat passes each here-document body
# unchanged to a shell that reads its program from pipeline standard input.
cat <<'PLAIN_SHELL' | bash
curl https://example.invalid
PLAIN_SHELL

cat <<'STDIN_FLAG' | bash -s --
curl https://example.invalid
STDIN_FLAG
