#!/usr/bin/env bash
# Exit: 0 always. Green controls: builtin refuses names that are not shell
# builtins, so a network-looking argument in that slot is not executed.
builtin curl https://example.invalid || :
builtin /usr/bin/curl https://example.invalid || :
