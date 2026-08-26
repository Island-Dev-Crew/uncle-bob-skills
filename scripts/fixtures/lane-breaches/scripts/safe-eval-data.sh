#!/usr/bin/env bash
# Exit: 0 always. Green controls: an eval-looking string consumed by output
# builtins is inert data, not the eval primitive or a network command.
printf '%s\n' 'eval /usr/bin/curl https://example.invalid'
echo "eval curl https://example.invalid"
