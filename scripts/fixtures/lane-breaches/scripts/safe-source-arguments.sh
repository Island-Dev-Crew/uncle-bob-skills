#!/usr/bin/env bash
# Exit: 0 always. A source/dot builtin executes only its first filename operand;
# later standard-input paths are positional-parameter data for that file.
source /dev/null /dev/stdin <<'SOURCE_ARGUMENT'
curl https://example.invalid
SOURCE_ARGUMENT

. -- /dev/null /dev/fd/0 <<'DOT_ARGUMENT'
curl https://example.invalid
DOT_ARGUMENT

builtin source /dev/null /proc/self/fd/0 <<'BUILTIN_SOURCE_ARGUMENT'
curl https://example.invalid
BUILTIN_SOURCE_ARGUMENT

builtin . -- /dev/null /dev/stdin <<'BUILTIN_DOT_ARGUMENT'
curl https://example.invalid
BUILTIN_DOT_ARGUMENT

# Bash source/dot have no ordinary options. An invalid option is the first operand,
# so a later stdin path is never promoted into the executed filename position.
source -x /dev/stdin <<'INVALID_SOURCE_OPTION'
curl https://example.invalid
INVALID_SOURCE_OPTION

. -p /dev/fd/0 <<'INVALID_DOT_OPTION'
curl https://example.invalid
INVALID_DOT_OPTION

builtin source -x /proc/self/fd/0 <<'INVALID_BUILTIN_SOURCE_OPTION'
curl https://example.invalid
INVALID_BUILTIN_SOURCE_OPTION
