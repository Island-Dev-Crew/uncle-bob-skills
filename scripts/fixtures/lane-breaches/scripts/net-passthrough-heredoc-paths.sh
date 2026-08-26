#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: these commands copy their literal
# here-document stdin unchanged into a shell that executes the pipeline.
cat /dev/stdin <<'CAT_STDIN' | bash
curl https://example.invalid
CAT_STDIN

tee /dev/null <<'TEE_STDIN' | bash
curl https://example.invalid
TEE_STDIN
