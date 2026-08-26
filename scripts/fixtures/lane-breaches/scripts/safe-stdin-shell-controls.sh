#!/usr/bin/env bash
# Exit: 0 always. The here-document is data when a shell sources a named file
# or when an ordinary rcfile path accompanies a `-c` program.
bash -c 'source ./fixture.sh' <<'EOF'
curl https://example.invalid
EOF

bash --noprofile --rcfile ./fixture.sh -ic ':' <<'EOF'
curl https://example.invalid
EOF


# Bash ignores rcfiles in non-interactive `-c` mode, so these stdin bodies are data.
bash --noprofile --rcfile /dev/stdin -c ':' <<'EOF'
curl https://example.invalid
EOF

bash --noprofile --init-file /dev/fd/0 -c ':' <<'EOF'
curl https://example.invalid
EOF
