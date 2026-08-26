#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: command-taking wrappers do not make
# the wrapped network program data.
nice -n 5 curl https://example.invalid
timeout --signal TERM 2s wget https://example.invalid
stdbuf -o L nc example.invalid 80
