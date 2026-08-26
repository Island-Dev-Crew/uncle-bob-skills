#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: exec -a accepts an empty argv[0]
# value without consuming the network utility that follows it.
exec -a '' curl https://example.invalid
