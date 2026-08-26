#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: each literal trap handler launches
# the network client when its shell reaches EXIT.
trap 'curl https://example.invalid' EXIT
bash -c "trap 'curl https://example.invalid' EXIT"
builtin trap 'curl https://example.invalid' EXIT
