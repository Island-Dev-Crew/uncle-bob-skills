#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: the argument following a shell's
# -c flag is a command program, not an inert string.
bash -c 'curl https://example.invalid'
