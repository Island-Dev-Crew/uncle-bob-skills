#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: the shell's source/dot builtins execute
# the here-document through a literal standard-input path inside `-c`.
cat <<'EOF' | bash -c 'source /dev/stdin'
curl https://example.invalid
EOF

bash -c '. /dev/stdin' <<'EOF'
curl https://example.invalid
EOF

source /dev/fd/0 <<'EOF'
curl https://example.invalid
EOF

. /proc/self/fd/0 <<'EOF'
curl https://example.invalid
EOF

builtin source /dev/stdin <<'EOF'
curl https://example.invalid
EOF

builtin . /dev/fd/0 <<'EOF'
curl https://example.invalid
EOF
