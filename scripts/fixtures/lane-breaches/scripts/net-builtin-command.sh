#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: Bash's builtin wrapper still
# executes the command builtin, which in turn launches the literal binary.
builtin command /usr/bin/curl https://example.invalid
