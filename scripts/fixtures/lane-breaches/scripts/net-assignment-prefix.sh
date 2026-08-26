#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: a shell environment assignment before
# a command does not turn the command into data.
LC_ALL=C curl https://example.invalid
