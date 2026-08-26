#!/usr/bin/env bash
# Exit: 0 always. Green controls: later curl words are argv data, and a name on
# a compound coprocess is not itself an executable position.
coproc echo curl https://example.invalid
coproc printf '%s\n' curl
coproc curl { printf '%s\n' safe; }
coproc FETCH { printf '%s\n' curl; }
printf '%s\n' coproc curl https://example.invalid
:
