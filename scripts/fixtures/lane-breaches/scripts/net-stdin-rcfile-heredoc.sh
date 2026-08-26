#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: Bash reads the literal stdin path as
# its interactive startup file before running the harmless `-c` program.
bash --noprofile --rcfile /dev/stdin -ic ':' <<'EOF'
curl https://example.invalid
EOF

bash --noprofile --rcfile /dev/fd/0 -ic ':' <<'EOF'
curl https://example.invalid
EOF

bash --noprofile --init-file /proc/self/fd/0 -ic ':' <<'EOF'
curl https://example.invalid
EOF

# The last supported startup-file option wins, so this body is executable.
bash --rcfile /dev/null --init-file /dev/stdin -ic ':' <<'LAST_STDIN_STARTUP'
curl https://example.invalid
LAST_STDIN_STARTUP
