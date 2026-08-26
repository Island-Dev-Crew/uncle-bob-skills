#!/usr/bin/env bash
# Exit: 0 always. Trap query/list modes inspect trap state or signal names;
# their remaining operands are data, and an empty handler ignores a signal.
trap -p 'curl https://example.invalid'
trap -l 'curl https://example.invalid'
trap -pl 'curl https://example.invalid'
builtin trap -p 'curl https://example.invalid'
trap '' EXIT
trap 'curl https://example.invalid'
trap -x 'curl https://example.invalid' EXIT
