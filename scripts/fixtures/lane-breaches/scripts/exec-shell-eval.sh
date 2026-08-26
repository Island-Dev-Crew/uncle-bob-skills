#!/usr/bin/env bash
# Exit: 0 always. A deliberate L2 eval primitive whose literal program also
# crosses L1 by launching a named network binary.
eval /usr/bin/curl https://example.invalid
eval -- '/usr/bin/curl https://example.invalid'
builtin eval -- '/usr/bin/curl https://example.invalid'
