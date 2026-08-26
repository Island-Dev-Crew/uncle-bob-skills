#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: a here-document supplied to Bash is
# executable shell input, not inert data supplied to an ordinary command.
bash <<'EOF'
curl https://example.invalid
EOF
