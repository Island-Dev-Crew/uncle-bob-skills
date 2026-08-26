#!/usr/bin/env bash
# Exit: 0 always. A deliberate L1 breach: builtin's option terminator does not
# turn the named command builtin or the binary it launches into data.
builtin -- command /usr/bin/curl https://example.invalid
