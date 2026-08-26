#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: literal here-string payloads become
# shell programs directly or through a recognised byte-preserving pipeline.
bash <<< 'curl https://example.invalid'
bash -s <<< $'cur\x6c https://example.invalid'
cat <<< 'curl https://example.invalid' | bash
tee /dev/null <<< 'curl https://example.invalid' | bash
